# =====================================================================
# bridge.py — API layer connecting the frontend to MySQL
#
# Supports TWO datasets from one endpoint:
#   - "uof"     -> uof_main_data
#   - "arrive"  -> arrive_main_data (+ arrive_values_data for multi-value filters)
#
# The frontend's JSON payload includes a "dataset" key to say which one
# it wants; this script picks the right table + column whitelist.
#
# Usage:
#   python bridge.py
# Listens on http://localhost:5001/query   (see README: port 5000 is
# reserved by macOS AirPlay, so this project deliberately uses 5001)
# =====================================================================

import sys
from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

sys.path.append(str(Path(__file__).parent / "config"))
from db_config import DB_CONFIG

app = Flask(__name__)
CORS(app)

MAX_ROWS = 5000

# ─────────────────────────────────────────────────────────────────────
# Dataset registry — add a new dataset here by giving it a table name,
# a whitelist of directly-filterable columns, numeric columns (so they
# aren't quoted as strings), and optionally a "values table" used for
# multi-value column filters (EXISTS-subquery pattern).
# ─────────────────────────────────────────────────────────────────────
DATASETS = {
    "uof": {
        "table": "uof_main_data",
        "id_col": "Form_ID",
        "date_col": "Incident_Date",
        "numeric_cols": {
            "Subject_Age", "Total_Sub_Injured", "Officer_Age",
            "Incident_Year", "Form_ID", "User_ID",
        },
        "allowed_cols": {
            "County", "Agency_Name", "Officer_Name", "Incident_ID",
            "Report_Number", "Incident_Case", "Incident_Date",
            "Other_Officer_Involved", "Officer_In_Uniform",
            "Incident_Municipality", "Indoor_Or_Outdoor", "Incident_Weather",
            "Video_Footage", "Video_Type", "Incident_Lighting",
            "Location_Type", "Incident_Type", "Contact_Origin",
            "Planned_Contact", "Officer_Age", "Officer_Race/Ethnicity",
            "Officer_Rank", "Officer_Gender", "Officer_Injury_Type",
            "Officer_Injuries_Injured", "Officer_Medical_Treatment",
            "Officer_Hospital_Treatment", "Total_Sub_Injured",
            "Subject_Injured", "Subject_Injured_Prior", "Perceived_Condition",
            "Subject_Actions", "Subject_Resistance",
            "Subject_Medical Treatment", "Subject_Injury Type",
            "Subject_Arrested", "Reason_Not_Arrested", "Subject_Type",
            "Subject_Age", "Subject_Race/Ethnicity", "Subject_Gender",
            "Force_Type", "Incident_Year",
        },
        "values_table": None,       # UoF multi-value handling not wired here yet
    },
    "arrive": {
        "table": "arrive_main_data",
        "id_col": "Random_ID",
        "date_col": None,           # no per-day date field, only Incident_Year
        "numeric_cols": {"Random_ID", "Incident_Year", "Outreach_Attempts"},
        "allowed_cols": {
            "Random_ID", "Incident_Year", "Arrive_Model", "Outreach_Attempts",
        },
        "values_table": {
            "name": "arrive_values_data",
            "fk_col": "Random_ID",
            # Columns filtered via arrive_values_data instead of directly,
            # since they're stored as multi-select tokens, not scalar values
            "multi_cols": {
                "Behaviors_Indicated_Prior_to_Arrival",
                "Other_Individuals_on_Scene",
                "Law_Enforcement_Observed_Behavior",
                "Law_Enforcement_Outcomes",
                "Mental_Health_Outcome",
                "Day_30_Outcomes",
            },
        },
    },
}


def build_sql(dataset_key: str, payload: dict):
    ds = DATASETS.get(dataset_key)
    if ds is None:
        raise ValueError(f"Unknown dataset '{dataset_key}'")

    filters = payload.get("filters", {})
    like    = payload.get("text_match", "exact") == "partial"

    clauses, params = [], []
    multi_cfg = ds.get("values_table")
    multi_cols = multi_cfg["multi_cols"] if multi_cfg else set()

    for col, rule in filters.items():
        # Reject anything not on the whitelist — prevents SQL injection
        # via arbitrary column names, and keeps queries scoped to the schema.
        if col != ds["date_col"] and col not in ds["allowed_cols"] and col not in multi_cols:
            continue

        quoted_col = f"`{col}`"

        # Date range (only applies if dataset has a date_col)
        if col == ds["date_col"]:
            if rule.get("from") and rule.get("to"):
                clauses.append(f"{quoted_col} BETWEEN %s AND %s")
                params += [rule["from"], rule["to"]]
            elif rule.get("from"):
                clauses.append(f"{quoted_col} >= %s")
                params.append(rule["from"])
            elif rule.get("to"):
                clauses.append(f"{quoted_col} <= %s")
                params.append(rule["to"])
            continue

        # Multi-value column -> EXISTS subquery against the values table
        if col in multi_cols and "in" in rule:
            vals = rule["in"]
            if not vals:
                continue
            vt = multi_cfg["name"]
            fk = multi_cfg["fk_col"]
            placeholders = ", ".join(["%s"] * len(vals))
            clauses.append(
                f"{ds['id_col']} IN (SELECT {fk} FROM {vt} "
                f"WHERE column_name = %s AND column_value IN ({placeholders}))"
            )
            params.append(col)
            params += vals
            continue

        # Standard IN list (scalar columns)
        if "in" in rule:
            vals = rule["in"]
            if not vals:
                continue
            if col in ds["numeric_cols"]:
                placeholders = ", ".join(["%s"] * len(vals))
                clauses.append(f"{quoted_col} IN ({placeholders})")
                params += [int(v) for v in vals]
            elif like:
                parts = [f"{quoted_col} LIKE %s" for _ in vals]
                clauses.append(f"({' OR '.join(parts)})")
                params += [f"%{v}%" for v in vals]
            else:
                placeholders = ", ".join(["%s"] * len(vals))
                clauses.append(f"{quoted_col} IN ({placeholders})")
                params += vals
            continue

        # Numeric range
        if "min" in rule or "max" in rule:
            lo, hi = rule.get("min"), rule.get("max")
            if lo is not None and hi is not None:
                clauses.append(f"{quoted_col} BETWEEN %s AND %s")
                params += [lo, hi]
            elif lo is not None:
                clauses.append(f"{quoted_col} >= %s")
                params.append(lo)
            elif hi is not None:
                clauses.append(f"{quoted_col} <= %s")
                params.append(hi)

    table = ds["table"]
    sql = f"SELECT * FROM `{table}`"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += f" LIMIT {MAX_ROWS}"
    return sql, params


@app.route("/query", methods=["POST"])
def query():
    payload = request.get_json(force=True)
    dataset_key = payload.get("dataset", "uof")

    try:
        sql, params = build_sql(dataset_key, payload)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        clean = [
            {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in row.items()}
            for row in rows
        ]
        return jsonify({"rows": clean, "count": len(clean)})

    except Exception as e:
        print(f"  ERROR: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "datasets": list(DATASETS.keys())})


if __name__ == "__main__":
    print(f"\n{'='*50}")
    print(f"  UoF / ARRIVE Query Bridge")
    print(f"  Datasets available: {', '.join(DATASETS.keys())}")
    print(f"  Listening on http://localhost:5001/query")
    print(f"{'='*50}\n")
    app.run(host="localhost", port=5001, debug=False)
