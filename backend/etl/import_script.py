# ETL SCRIPT to load raw UoF data from Excel into MySQL database, processing table
import os
import sys
import pandas as pd
import mysql.connector

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "config"))
from db_config import DB_CONFIG

# Pass the file path as a command-line arg, e.g.:
#   python import_script.py ../../data/UoF_full_dataset.xlsx
# Falls back to the full-dataset filename below if no arg is given.
DEFAULT_EXCEL_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "UoF_full_dataset.xlsx")
EXCEL_FILE = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EXCEL_FILE

# --- Load ---
df = pd.read_excel(EXCEL_FILE)
print(f"Loaded {len(df)} rows from {EXCEL_FILE}")

# --- Rename columns to match schema ---
col_map = {
    "Form ID": "Form_ID",
    "Agency Name": "Agency_Name",
    "Officer Name": "Officer_Name",
    "User ID": "User_ID",
    "Incident ID": "Incident_ID",
    "Report Number": "Report_Number",
    "Incident Case Number": "Incident_Case",
    "Incident Date": "Incident_Date",
    "Other Officer Involved": "Other_Officer_Involved",
    "Officer In Uniform": "Officer_In_Uniform",
    "Incident Municipality": "Incident_Municipality",
    "Indoor Or Outdoor": "Indoor_Or_Outdoor",
    "Incident Weather": "Incident_Weather",
    "Video Footage": "Video_Footage",
    "Video Type": "Video_Type",
    "Incident Lighting": "Incident_Lighting",
    "Location Type": "Location_Type",
    "Incident Type": "Incident_Type",
    "Contact Origin": "Contact_Origin",
    "Planned Contact": "Planned_Contact",
    "Officer Age": "Officer_Age",
    "Officer Race/Ethnicity": "Officer_Race/Ethnicity",
    "Officer Rank": "Officer_Rank",
    "Officer Gender": "Officer_Gender",
    "Officer Injury Type": "Officer_Injury_Type",
    "Officer Injuries Injured": "Officer_Injuries_Injured",
    "Officer Medical Treatment": "Officer_Medical_Treatment",
    "Officer Hospital Treatment": "Officer_Hospital_Treatment",
    "Total Sub Injured In Incident": "Total_Sub_Injured",
    "Subject Injured In Incident": "Subject_Injured",
    "Subject Injured Prior To Incident": "Subject_Injured_Prior",
    "Perceived Condition Of Subject": "Perceived_Condition",
    "Subject Actions": "Subject_Actions",
    "Subject Resistance": "Subject_Resistance",
    "Subject Medical Treatment": "Subject_Medical Treatment",
    "Subject Injury Type": "Subject_Injury Type",
    "Subject Arrested": "Subject_Arrested",
    "Reason Subject Not Arrested": "Reason_Not_Arrested",
    "Subject Type": "Subject_Type",
    "Subject Age": "Subject_Age",
    "Subject Race/Ethnicity": "Subject_Race/Ethnicity",
    "Subject Gender": "Subject_Gender",
    "Force Type": "Force_Type",
    "Incident Year": "Incident_Year",
}

# --- Drop the KEEP/DROP column (if present) and rename ---
df = df.drop(columns=["KEEP/DROP"], errors="ignore")
df = df.rename(columns=col_map)

# --- Sanity check: catch column-name drift between the subset and full dataset ---
# Compared against the ACTUAL target schema columns (post-rename), not col_map's keys -
# columns like County are already correctly named in the source and were never meant
# to be in col_map, so checking against col_map alone would wrongly flag them as extra.
valid_schema_cols = {
    "Form_ID",
    "County",
    "Agency_Name",
    "Officer_Name",
    "User_ID",
    "Incident_ID",
    "Report_Number",
    "Incident_Case",
    "Incident_Date",
    "Other_Officer_Involved",
    "Officer_In_Uniform",
    "Incident_Municipality",
    "Indoor_Or_Outdoor",
    "Incident_Weather",
    "Video_Footage",
    "Video_Type",
    "Incident_Lighting",
    "Location_Type",
    "Incident_Type",
    "Contact_Origin",
    "Planned_Contact",
    "Officer_Age",
    "Officer_Race/Ethnicity",
    "Officer_Rank",
    "Officer_Gender",
    "Officer_Injury_Type",
    "Officer_Injuries_Injured",
    "Officer_Medical_Treatment",
    "Officer_Hospital_Treatment",
    "Total_Sub_Injured",
    "Subject_Injured",
    "Subject_Injured_Prior",
    "Perceived_Condition",
    "Subject_Actions",
    "Subject_Resistance",
    "Subject_Medical Treatment",
    "Subject_Injury Type",
    "Subject_Arrested",
    "Reason_Not_Arrested",
    "Subject_Type",
    "Subject_Age",
    "Subject_Race/Ethnicity",
    "Subject_Gender",
    "Force_Type",
    "Incident_Year",
}
unexpected = [c for c in df.columns if c not in valid_schema_cols]
missing = valid_schema_cols - set(df.columns)
if unexpected:
    print(f"WARNING: dropping columns not present in schema: {unexpected}")
    df = df.drop(columns=unexpected)
if missing:
    print(f"WARNING: schema columns not found in source file (will be omitted from insert): {sorted(missing)}")

# --- Fix Officer_In_Uniform (bool -> tinyint 1/0) ---
df["Officer_In_Uniform"] = df["Officer_In_Uniform"].map({True: 1, False: 0})

# --- Connect to MySQL ---
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# --- Build INSERT ---
cols = ", ".join([f"`{c}`" for c in df.columns])
placeholders = ", ".join(["%s"] * len(df.columns))
sql = f"INSERT INTO uof_main_processing_table ({cols}) VALUES ({placeholders})"

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
    print("Consider logging these into exceptions_table for review.")
