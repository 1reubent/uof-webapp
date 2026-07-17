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
    "Reason_Not_Arrested": 39,
    "Subject_Type": 40,
    "Subject_Age": 41,
    "Subject_Race/Ethnicity": 42,
    "Subject_Gender": 43,
    "Force_Type": 44,
}


# Single-value columns standardized via standard_values_table (see
# clean_and_populate.py's single_cols). column_name there is stored with
# spaces, not underscores (e.g. 'Officer Rank'), matching the ETL script's
# own col.replace("_", " ").lower() convention.
SINGLE_VALUE_COLUMNS = {
    "Video_Footage": "Video Footage",
    "Officer_Race/Ethnicity": "Officer Race/Ethnicity",
    "Officer_Rank": "Officer Rank",
    "Officer_Gender": "Officer Gender",
    "Officer_Hospital_Treatment": "Officer Hospital Treatment",
}

# Free-text uof_main_data columns with no standard/column-values catalog but
# low enough cardinality to be genuinely categorical (a few hundred distinct
# values at most), unlike Officer_Name/Report_Number/Incident_Case which are
# closer to unique identifiers (20k+ distinct values each) and wouldn't
# benefit from being bundled into a suggestion list.
DISTINCT_VALUE_COLUMNS = ["County", "Agency_Name", "Incident_Municipality"]


def quote_col(col):
    return f"`{col}`"


app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev")
)

CORS(app)

# test route
@app.route("/health", methods=("GET",))
def health():
  return {"status": "ok"}

# Cached response for /filter-values (below): this data only changes when
# the ETL pipeline lands new data, not on every page load, so recomputing it
# per-request just re-pays a ~4s DISTINCT-query cost for no reason. Render's
# free-tier deployment (see render.yaml) runs a single gunicorn worker, so a
# plain process-global is a genuinely shared cache across all requests, not
# just the current one -- and since the free tier already spins the process
# down after ~15min idle (recomputing on the next cold start regardless),
# "cache forever until restart" gets the same practical freshness as a TTL
# here, with less code.
# NOTE: this Render+Aiven deployment is temporary/testing-only. Once the app
# moves to an always-on server (no idle spin-down to naturally invalidate
# this), switch this to a TTL so it self-refreshes without needing a manual
# restart/redeploy to pick up new ETL data.
_filter_values_cache = None

# Bulk endpoint for the frontend's autocomplete: returns every known value for
# each cataloged/categorical free-text column in one shot, fetched once per
# page load rather than queried per keystroke. Columns not present in the
# response (Officer_Name, Report_Number, Incident_Case, IDs, numeric ranges)
# get no suggestions client-side -- same as today.
@app.route("/filter-values", methods=("GET",))
def filter_values():
  global _filter_values_cache
  if _filter_values_cache is not None:
    return _filter_values_cache
  try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    values = {col: [] for col in SINGLE_VALUE_COLUMNS}
    values.update({col: [] for col in MULTI_VALUE_POSITION if col != "Subject_Age"})
    values.update({col: [] for col in DISTINCT_VALUE_COLUMNS})

    # One query for all 5 single-value columns instead of 5 separate
    # round-trips -- each query here is a network hop to Aiven, and with 31
    # cataloged/categorical columns total, doing them one-by-one made this
    # endpoint take ~5.7s to answer (measured), which is a real page-load
    # delay even though it's fetched only once, not per keystroke.
    single_col_names = list(SINGLE_VALUE_COLUMNS.values())
    reverse_single = {v: k for k, v in SINGLE_VALUE_COLUMNS.items()}
    placeholders = ", ".join(["%s"] * len(single_col_names))
    cursor.execute(
        f"SELECT DISTINCT column_name, standard_value FROM standard_values_table "
        f"WHERE column_name IN ({placeholders}) ORDER BY column_name, standard_value",
        tuple(single_col_names),
    )
    for row in cursor.fetchall():
      r = dict(row)
      col = reverse_single[r["column_name"]]
      values[col].append(r["standard_value"])

    # One query for all 23 multi-value columns instead of 23 round-trips.
    multi_positions = {col: pid for col, pid in MULTI_VALUE_POSITION.items() if col != "Subject_Age"}
    reverse_multi = {v: k for k, v in multi_positions.items()}
    placeholders = ", ".join(["%s"] * len(multi_positions))
    cursor.execute(
        f"SELECT DISTINCT Position_Id, Column_Value FROM uof_column_values_data "
        f"WHERE Position_Id IN ({placeholders}) ORDER BY Position_Id, Column_Value",
        tuple(multi_positions.values()),
    )
    for row in cursor.fetchall():
      r = dict(row)
      col = reverse_multi[r["Position_Id"]]
      values[col].append(r["Column_Value"])

    # One UNION query for the 3 uncataloged categorical columns instead of 3.
    union_sql = " UNION ALL ".join(
        f"SELECT %s AS field, {quote_col(col)} AS val FROM uof_main_data WHERE {quote_col(col)} IS NOT NULL"
        for col in DISTINCT_VALUE_COLUMNS
    )
    cursor.execute(f"SELECT DISTINCT field, val FROM ({union_sql}) AS distinct_cols ORDER BY field, val", tuple(DISTINCT_VALUE_COLUMNS))
    for row in cursor.fetchall():
      r = dict(row)
      values[r["field"]].append(r["val"])

    response = {"values": values}
    _filter_values_cache = response  # only cache on success; an error should retry next request
  except Exception as e:
    response = {"error": str(e)}
  finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()

  return response

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
            # for genuinely multi-valued forms. Single-valued forms have no rows in
            # uof_dashboard_values_data at all (see clean_and_populate.py), so also
            # match those directly against uof_main_data, excluding any Form_ID that
            # does have tokenized rows for this position (those are the multi-valued
            # ones, already covered by the first branch, and their raw joined string
            # shouldn't be compared directly).
            if position_id is not None:
                if text_match == "partial":
                    token_clauses = " OR ".join(["Column_Value LIKE %s"] * len(values))
                    token_params = [f"%{v}%" for v in values]
                    main_clauses = " OR ".join([f"{quote_col(col)} LIKE %s"] * len(values))
                    main_params = [f"%{v}%" for v in values]
                else:
                    token_clauses = " OR ".join(["Column_Value = %s"] * len(values))
                    token_params = list(values)
                    main_clauses = " OR ".join([f"{quote_col(col)} = %s"] * len(values))
                    main_params = list(values)
                clauses.append(
                    "(Form_ID IN (SELECT Form_Id FROM uof_dashboard_values_data "
                    f"WHERE Position_Id = %s AND ({token_clauses})) "
                    f"OR (({main_clauses}) AND Form_ID NOT IN "
                    "(SELECT Form_Id FROM uof_dashboard_values_data WHERE Position_Id = %s)))"
                )
                params.append(position_id)
                params.extend(token_params)
                params.extend(main_params)
                params.append(position_id)
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
            # the rest. Single-valued forms have no tokenized rows in
            # uof_dashboard_values_data at all (see clean_and_populate.py), so also
            # match those directly against uof_main_data (same digit-only guard),
            # excluding any Form_ID that does have tokenized rows for this position.
            if position_id is not None:
                numeric_guard = "Column_Value REGEXP '^[0-9]+$'"
                main_numeric_guard = f"{quote_col(col)} REGEXP '^[0-9]+$'"
                not_tokenized = "Form_ID NOT IN (SELECT Form_Id FROM uof_dashboard_values_data WHERE Position_Id = %s)"
                if min_v not in (None, "") and max_v not in (None, ""):
                    clauses.append(
                        "(Form_ID IN (SELECT Form_Id FROM uof_dashboard_values_data "
                        f"WHERE Position_Id = %s AND {numeric_guard} "
                        "AND CAST(Column_Value AS UNSIGNED) BETWEEN %s AND %s) "
                        f"OR ({main_numeric_guard} AND CAST({quote_col(col)} AS UNSIGNED) BETWEEN %s AND %s "
                        f"AND {not_tokenized}))"
                    )
                    params.extend([position_id, min_v, max_v, min_v, max_v, position_id])
                elif min_v not in (None, ""):
                    clauses.append(
                        "(Form_ID IN (SELECT Form_Id FROM uof_dashboard_values_data "
                        f"WHERE Position_Id = %s AND {numeric_guard} "
                        "AND CAST(Column_Value AS UNSIGNED) >= %s) "
                        f"OR ({main_numeric_guard} AND CAST({quote_col(col)} AS UNSIGNED) >= %s "
                        f"AND {not_tokenized}))"
                    )
                    params.extend([position_id, min_v, min_v, position_id])
                elif max_v not in (None, ""):
                    clauses.append(
                        "(Form_ID IN (SELECT Form_Id FROM uof_dashboard_values_data "
                        f"WHERE Position_Id = %s AND {numeric_guard} "
                        "AND CAST(Column_Value AS UNSIGNED) <= %s) "
                        f"OR ({main_numeric_guard} AND CAST({quote_col(col)} AS UNSIGNED) <= %s "
                        f"AND {not_tokenized}))"
                    )
                    params.extend([position_id, max_v, max_v, position_id])
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
