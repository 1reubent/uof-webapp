# ETL SCRIPT to load raw subset of UoF data from Excel into MySQL database, processing table
import os
import sys
import pandas as pd
import mysql.connector

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from db_config import DB_CONFIG

EXCEL_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'UoF_database_1k_subset_100120_to_053126.xlsx')

# --- Load ---
df = pd.read_excel(EXCEL_FILE)

# --- Drop the KEEP/DROP column ---
df = df.drop(columns=["KEEP/DROP"])

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
df = df.rename(columns=col_map)

# --- Fix Officer_In_Uniform (bool -> tinyint 1/0) ---
df["Officer_In_Uniform"] = df["Officer_In_Uniform"].map({True: 1, False: 0})

# --- Connect to MySQL ---
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# --- Build INSERT ---
cols = ", ".join([f"`{c}`" for c in df.columns])
placeholders = ", ".join(["%s"] * len(df.columns))
sql = f"INSERT INTO uof_main_processing_table ({cols}) VALUES ({placeholders})"

# --- Batch insert ---
# also convert NaN to None in the data rows to ensure they are inserted as NULL in SQL
batch_size = 100
rows = [
  tuple(None if pd.isna(v) else v for v in r)
  for r in df.itertuples(index=False, name=None)
]
for i in range(0, len(rows), batch_size):
  cursor.executemany(sql, rows[i : i + batch_size])
  conn.commit()
  print(f"Inserted rows {i} to {min(i + batch_size, len(rows))}")

cursor.close()
conn.close()
print("Done.")
