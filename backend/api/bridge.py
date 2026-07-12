import os
import sys
from flask import Flask, request
from flask_cors import CORS
import mysql.connector 


sys.path.append(os.path.join(os.path.dirname(__file__), "..", "config"))
from db_config import DB_CONFIG

# Whitelist of real uof_main_data columns. Filter keys come straight from the
# request body and get spliced into the SQL as identifiers (not parameterizable
# like values are), so anything not in this set must be rejected before it
# touches the query string.
ALLOWED_COLUMNS = {
    "Form_ID", "County", "Agency_Name", "Officer_Name", "User_ID", "Incident_ID",
    "Report_Number", "Incident_Case", "Incident_Date", "Other_Officer_Involved",
    "Officer_In_Uniform", "Incident_Municipality", "Indoor_Or_Outdoor", "Incident_Weather",
    "Video_Footage", "Video_Type", "Incident_Lighting", "Location_Type", "Incident_Type",
    "Contact_Origin", "Planned_Contact", "Officer_Age", "Officer_Race/Ethnicity",
    "Officer_Rank", "Officer_Gender", "Officer_Injury_Type", "Officer_Injuries_Injured",
    "Officer_Medical_Treatment", "Officer_Hospital_Treatment", "Total_Sub_Injured",
    "Subject_Injured", "Subject_Injured_Prior", "Perceived_Condition", "Subject_Actions",
    "Subject_Resistance", "Subject_Medical Treatment", "Subject_Injury Type",
    "Subject_Arrested", "Reason_Not_Arrested", "Subject_Type", "Subject_Age",
    "Subject_Race/Ethnicity", "Subject_Gender", "Force_Type", "Incident_Year",
}

# Columns compared as numbers (range filters, or "tags-num" IN filters) rather
# than text — mirrors NUMERIC in uof_program_v2.html. Subject_Age is deliberately
# excluded: it's a multi-value column (see MULTI_VALUE_POSITION) so its range
# filter is handled via the tokenized uof_dashboard_values_data table instead.
NUMERIC_COLUMNS = {"Total_Sub_Injured", "Officer_Age", "Incident_Year", "Form_ID", "User_ID"}
# all of these columns use min/max specs in the request body, except only form_id, user_id use IN.

# Columns whose uof_main_data value is a raw comma-joined string (e.g.
# "Kick, Resisted arrest/police officer control"), tokenized per-value into
# uof_dashboard_values_data at ETL time. Filtering these means matching
# individual tokens there and constraining Form_ID, not matching the raw
# string on uof_main_data directly. Maps column name -> Position_Id, taken
# from clean_and_populate.py's pos_map (minus its single_cols, which are
# standardized single values, not tokenized).
MULTI_VALUE_POSITION = {
    "Indoor_Or_Outdoor": 13,
    "Incident_Weather": 14,
    "Video_Type": 16,
    "Incident_Lighting": 17,
    "Location_Type": 18,
    "Incident_Type": 19,
    "Contact_Origin": 20,
    "Planned_Contact": 21,
    "Officer_Injury_Type": 26,
    "Officer_Medical_Treatment": 28,
    "Subject_Injured": 31,
    "Subject_Injured_Prior": 32,
    "Perceived_Condition": 33,
    "Subject_Actions": 34,
    "Subject_Resistance": 35,
    "Subject_Medical Treatment": 36,
    "Subject_Injury Type": 37,
    "Subject_Arrested": 38,
    "Subject_Type": 40,
    "Subject_Age": 41,
    "Subject_Race/Ethnicity": 42,
    "Subject_Gender": 43,
    "Force_Type": 44,
}


def quote_col(col):
    return f"`{col}`"


app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY="dev"
)

CORS(app)

# test route
@app.route("/health", methods=("GET",))
def health():
  return {"status": "ok"}

@app.route("/query", methods=("POST",))
def query():
  try:
    body = request.get_json()
    # Sample Body:
    # {
    #   "table": "uof_main_data",
    #   "text_match": "exact", // or "partial" for LIKE
    #   "filters": {
    #     "Incident_Date": { "from": "2025-01-01", "to": "2025-06-30" },
    #     "County":        { "in": ["Essex", "Union"] },
    #     "Subject_Age":   { "min": "18", "max": "40" }
    #     ...
    #   }
    # }

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    # Build SQL query based on request body
    filters = body.get("filters", {})
    text_match = body.get("text_match", "exact")

    clauses = []
    params = []

    # Handle date range filter for Incident_Date
    date_filter = filters.get("Incident_Date", {})
    if date_filter:
        date_from = date_filter.get("from")
        date_to = date_filter.get("to")
        if date_from and date_to:
            clauses.append("Incident_Date BETWEEN %s AND %s")
            params.extend([date_from, date_to])
        elif date_from:
            clauses.append("Incident_Date >= %s")
            params.append(date_from)
        elif date_to:
            clauses.append("Incident_Date <= %s")
            params.append(date_to)

    for col, spec in filters.items():
        # Skip Incident_Date since it's handled separately, and skip any columns not in the allowed list or non-dict specs
        if col == "Incident_Date" or col not in ALLOWED_COLUMNS or not isinstance(spec, dict):
            continue

        position_id = MULTI_VALUE_POSITION.get(col)

        if "in" in spec:
            #get all "in" values
            values = [v for v in (spec.get("in") or []) if v not in (None, "")]
            if not values:
                continue

            # multi-value column: match individual tokens in uof_dashboard_values_data
            # and constrain Form_ID, since uof_main_data holds the raw joined string
            if position_id is not None:
                if text_match == "partial":
                    token_clauses = " OR ".join(["Column_Value LIKE %s"] * len(values))
                    token_params = [f"%{v}%" for v in values]
                else:
                    token_clauses = " OR ".join(["Column_Value = %s"] * len(values))
                    token_params = list(values)
                clauses.append(
                    "Form_ID IN (SELECT Form_Id FROM uof_dashboard_values_data "
                    f"WHERE Position_Id = %s AND ({token_clauses}))"
                )
                params.append(position_id)
                params.extend(token_params)
            # append params for non-numeric columns with partial match; use LIKE clauses
            elif col not in NUMERIC_COLUMNS and text_match == "partial":
                like_clauses = " OR ".join([f"{quote_col(col)} LIKE %s"] * len(values))
                clauses.append(f"({like_clauses})")
                params.extend(f"%{v}%" for v in values)
            # append params for numeric columns or exact match; use IN clause
            else:
                placeholders = ", ".join(["%s"] * len(values))
                clauses.append(f"{quote_col(col)} IN ({placeholders})")
                params.extend(values)

        # handle min/max range filters for numeric columns
        elif "min" in spec or "max" in spec:
            min_v, max_v = spec.get("min"), spec.get("max")

            # multi-value numeric column (currently just Subject_Age): tokens can
            # also be non-numeric ("Unknown", "Under 18"), so only compare tokens
            # that are actually digits — a numeric range can't meaningfully match
            # the rest.
            if position_id is not None:
                numeric_guard = "Column_Value REGEXP '^[0-9]+$'"
                if min_v not in (None, "") and max_v not in (None, ""):
                    clauses.append(
                        "Form_ID IN (SELECT Form_Id FROM uof_dashboard_values_data "
                        f"WHERE Position_Id = %s AND {numeric_guard} "
                        "AND CAST(Column_Value AS UNSIGNED) BETWEEN %s AND %s)"
                    )
                    params.extend([position_id, min_v, max_v])
                elif min_v not in (None, ""):
                    clauses.append(
                        "Form_ID IN (SELECT Form_Id FROM uof_dashboard_values_data "
                        f"WHERE Position_Id = %s AND {numeric_guard} "
                        "AND CAST(Column_Value AS UNSIGNED) >= %s)"
                    )
                    params.extend([position_id, min_v])
                elif max_v not in (None, ""):
                    clauses.append(
                        "Form_ID IN (SELECT Form_Id FROM uof_dashboard_values_data "
                        f"WHERE Position_Id = %s AND {numeric_guard} "
                        "AND CAST(Column_Value AS UNSIGNED) <= %s)"
                    )
                    params.extend([position_id, max_v])
            elif min_v not in (None, "") and max_v not in (None, ""):
                clauses.append(f"{quote_col(col)} BETWEEN %s AND %s")
                params.extend([min_v, max_v])
            elif min_v not in (None, ""):
                clauses.append(f"{quote_col(col)} >= %s")
                params.append(min_v)
            elif max_v not in (None, ""):
                clauses.append(f"{quote_col(col)} <= %s")
                params.append(max_v)

    # LIMIT is the only guard against
    # an unbounded SELECT * when a request carries no filters at all.
    sql = "SELECT * FROM uof_main_data"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " LIMIT 50;" 

    cursor.execute(sql, tuple(params))
    executed_query = cursor.statement if hasattr(cursor, "statement") else "no statement available"
    print(f"Executed SQL: {executed_query}")

    results = cursor.fetchall()
    
    # convert incident_date from python datetime to isoformat (YYYY-MM-DD)

    # print(results)
    # print(results[0].get("Incident_Date").isoformat())
    rows = []
    for row in results:
        r = dict(row)
        date_val = r.get("Incident_Date")
        if hasattr(date_val, "isoformat"):
          r["Incident_Date"] = date_val.isoformat()
        rows.append(r)

    response = {
        "rows": rows
    }
  except Exception as e:
    response = {
        "error": str(e)
    }
  finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()

  return response






if __name__ == "__main__":
  app.run(debug=True, port=5001)
