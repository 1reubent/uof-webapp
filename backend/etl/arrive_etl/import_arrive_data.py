# ETL SCRIPT to load raw ARRIVE Together data from Excel into MySQL database (arrive_main_data)
#
# Only the "Reports Download File" export is loaded here, not the "Demographic
# Download File" -- the demographic file has no unique key (its first column is
# a pre-aggregated count, not a row ID) and can't be joined back to individual
# incidents.
#
# This script does not tokenize multi-value columns into arrive_values_data --
# see tokenize_arrive_data.py, which reads back from arrive_main_data and
# rebuilds arrive_values_data. Run that after this one.
import ast
import os
import sys
import pandas as pd
import mysql.connector

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "config"))
from db_config import DB_CONFIG

# Pass the file path as a command-line arg, e.g.:
#   python import_arrive_data.py ../../../data/ARRIVE_Reports_Download_File_7_1_2026.xlsx
# Falls back to the full-dataset filename below if no arg is given.
DEFAULT_EXCEL_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "ARRIVE_Reports_Download_File_7_1_2026.xlsx")
EXCEL_FILE = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EXCEL_FILE

# --- Load ---
df = pd.read_excel(EXCEL_FILE)
print(f"Loaded {len(df)} rows from {EXCEL_FILE}")

# --- Rename columns to match schema ---
col_map = {
    "Year of Date_of_Incident": "Incident_Year",
    "ARRIVE Model": "Arrive_Model",
    "outreach_attempts": "Outreach_Attempts",
    "30_Day_Outcomes": "Day_30_Outcomes",
}
df = df.rename(columns=col_map)

# --- Sanity check: catch column-name drift between exports ---
valid_schema_cols = {
    "Random_ID",
    "Incident_Year",
    "Arrive_Model",
    "Behaviors_Indicated_Prior_to_Arrival",
    "Other_Individuals_on_Scene",
    "Law_Enforcement_Observed_Behavior",
    "Law_Enforcement_Outcomes",
    "Outreach_Attempts",
    "Mental_Health_Outcome",
    "Day_30_Outcomes",
}
unexpected = [c for c in df.columns if c not in valid_schema_cols]
missing = valid_schema_cols - set(df.columns)
if unexpected:
    print(f"WARNING: dropping columns not present in schema: {unexpected}")
    df = df.drop(columns=unexpected)
if missing:
    print(f"WARNING: schema columns not found in source file (will be omitted from insert): {sorted(missing)}")

# --- Multi-value columns and the separator used to join their tokens in the
# source file. Everything except Arrive_Model is a Python list-literal string
# (e.g. "['Violence', 'Confused/disoriented persons']"); Arrive_Model is a
# plain string joined with " & " instead (e.g. "Follow-up & Co-Response").
# Flattened here to plain separator-joined text so arrive_main_data holds
# readable values -- tokenize_arrive_data.py re-splits this same text later
# to populate arrive_values_data. ---
MULTI_VALUE_COLS = {
    "Arrive_Model": " & ",
    "Behaviors_Indicated_Prior_to_Arrival": ",",
    "Other_Individuals_on_Scene": ",",
    "Law_Enforcement_Observed_Behavior": ",",
    "Law_Enforcement_Outcomes": ",",
    "Mental_Health_Outcome": ",",
    "Day_30_Outcomes": ",",
}


def parse_list_cell(cell, separator=","):
    """Parse a multi-value cell into a list of tokens. Handles Python
    list-literal strings (e.g. "['A', 'B']") as well as plain
    separator-joined strings (e.g. "A & B"), falling back to a single-item
    list for anything else (e.g. a lone value with no separator present)."""
    if pd.isna(cell):
        return []
    if isinstance(cell, list):
        return cell
    s = str(cell).strip()
    if not s:
        return []
    try:
        parsed = ast.literal_eval(s)
        if isinstance(parsed, (list, tuple)):
            return list(parsed)
        return [str(parsed)]
    except (ValueError, SyntaxError):
        return [t.strip() for t in s.split(separator) if t.strip()]


for col, sep in MULTI_VALUE_COLS.items():
    if col not in df.columns:
        continue
    display_sep = ", " if sep == "," else sep
    df[col] = df[col].apply(lambda cell, sep=sep, display_sep=display_sep: display_sep.join(parse_list_cell(cell, sep)) or None)

# --- Connect to MySQL ---
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# --- Safe to re-run: rows already present (by Random_ID) are skipped ---
cursor.execute("SELECT Random_ID FROM arrive_main_data")
existing_ids = {r[0] for r in cursor.fetchall()}
df = df[~df["Random_ID"].isin(existing_ids)]
print(f"{len(df)} new rows to insert ({len(existing_ids)} already in database)")

if df.empty:
    print("Nothing new to insert.")
    cursor.close()
    conn.close()
else:
    # --- Build INSERT ---
    columns = ", ".join([f"`{c}`" for c in df.columns])
    placeholders = ", ".join(["%s"] * len(df.columns))
    sql = f"INSERT INTO arrive_main_data ({columns}) VALUES ({placeholders})"

    # --- Batch insert, with per-row fallback if a batch fails ---
    # also convert NaN to None in the data rows to ensure they are inserted as NULL in SQL
    batch_size = 500
    rows = [tuple(None if pd.isna(v) else v for v in r) for r in df.itertuples(index=False, name=None)]

    failed_rows = []
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        try:
            cursor.executemany(sql, batch)
            conn.commit()
            print(f"Inserted rows {i} to {min(i + batch_size, len(rows))}")
        except mysql.connector.Error as e:
            conn.rollback()
            print(f"Batch {i}-{i + batch_size} failed ({e}); retrying row by row to isolate the problem")
            for j, row in enumerate(batch):
                try:
                    cursor.execute(sql, row)
                    conn.commit()
                except mysql.connector.Error as row_err:
                    conn.rollback()
                    failed_rows.append((i + j, row, str(row_err)))
                    print(f"  Row {i + j} failed: {row_err}")

    cursor.close()
    conn.close()

    print(f"\nDone. {len(rows) - len(failed_rows)} of {len(rows)} rows inserted successfully.")
    if failed_rows:
        print(f"{len(failed_rows)} rows failed — see failed_rows list above for row indices and errors.")
