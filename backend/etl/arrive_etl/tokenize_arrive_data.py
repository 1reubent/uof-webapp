# ETL SCRIPT to tokenize arrive_main_data's multi-value columns into
# arrive_values_data, for filtering on individual selected values.
#
# Reads back from arrive_main_data (run import_arrive_data.py first) rather
# than the source Excel file, same as clean_and_populate.py reads from
# uof_main_processing_table instead of re-reading the UoF Excel file.
#
# Safe to re-run: arrive_values_data is fully rebuilt from the current
# contents of arrive_main_data each time, so there's no partial-completion
# state to track and no risk of duplicate rows.
import os
import sys
import mysql.connector

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "config"))
from db_config import DB_CONFIG

# --- Multi-value columns and the separator used to join their tokens in
# arrive_main_data (see import_arrive_data.py, which writes them in this
# joined form). Everything except Arrive_Model is comma-joined; Arrive_Model
# is joined with " & " instead (e.g. "Follow-up & Co-Response"). ---
MULTI_VALUE_COLS = {
    "Arrive_Model": " & ",
    "Behaviors_Indicated_Prior_to_Arrival": ",",
    "Other_Individuals_on_Scene": ",",
    "Law_Enforcement_Observed_Behavior": ",",
    "Law_Enforcement_Outcomes": ",",
    "Mental_Health_Outcome": ",",
    "Day_30_Outcomes": ",",
}

# Known values for each multi-value column. There's no exceptions table for
# ARRIVE data, so this isn't used to reject or log anything -- it's just a
# console sanity check below that flags drift (a typo, or a new value added
# in a later export) without blocking the tokenization.
VALID_VALUES = {
    "Arrive_Model": {
        "Follow-up", "Close Follow-up", "Co-Response",
        "Non-Law Enforcement Response", "Telehealth",
    },
    "Behaviors_Indicated_Prior_to_Arrival": {
        "Welfare check", "Emotional dysregulation", "Suicidal ideation/thoughts/threats",
        "Other", "Confused/disoriented persons", "Disorderly persons", "Housing instability",
        "Medication non-adherence", "Threats of harm to others", "Alcohol Misuse", "Violence",
        "Domestic Violence", "Medical assist", "Attempted Suicide", "Weapon", "Drug Overdose",
    },
    "Other_Individuals_on_Scene": {
        "Family Member", "Other Familiar Person", "Non Familiar Person",
    },
    "Law_Enforcement_Observed_Behavior": {
        "Welfare check", "Emotional dysregulation", "Emotional outbursts",
        "Suicidal ideation/thoughts/threats", "Confused/disoriented persons", "Other",
        "Hallucination/Delusions", "Housing instability", "Medication non-adherence",
        "Disorderly persons", "Threats of harm to others", "Under the influence of Alcohol",
        "Medical assist", "Violence", "Domestic Violence", "Under the influence of Drugs",
        "Attempted Suicide", "Weapon", "Drug Overdose",
    },
    "Law_Enforcement_Outcomes": {
        "Referred to Services", "Otherwise Resolved Without Transport",
        "Voluntary Transport to Hospital",
        "Involuntary Transport to Hospital at Direction of Screener",
        "Involuntary Transport to Hospital Without Direction of Screener", "Arrest",
    },
    "Mental_Health_Outcome": {
        "Linked to Services and Remained in Community", "Voluntary Transport to Hospital",
        "Involuntary Transport Order to Hospital", "Refused Services", "Not Home",
        "Admitted to Hospital", "Shelter Placement Request", "Transport to Mental Health Services",
        "Friend/Family Home Transfer Request",
    },
    "Day_30_Outcomes": {
        "Ongoing participation in services", "Unknown", "Participated in in-patient program",
        "Attempted Contact Failed", "Referred to Services - Unreachable",
        "Pursued consistent medication", "Presented to ER", "No Contact Information",
        "No Attempt to Contact Made",
    },
}


def parse_cell(cell, separator):
    if cell is None:
        return []
    s = str(cell).strip()
    if not s:
        return []
    return [t.strip() for t in s.split(separator) if t.strip()]


# --- Connect to MySQL ---
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# --- Read back the multi-value columns from arrive_main_data ---
select_cols = ["Random_ID"] + list(MULTI_VALUE_COLS.keys())
cursor.execute(f"SELECT {', '.join(f'`{c}`' for c in select_cols)} FROM arrive_main_data")
main_rows = cursor.fetchall()
print(f"Read {len(main_rows)} rows from arrive_main_data")

# --- Build (Random_ID, column_name, column_value) tokens. Only genuinely
# multi-valued cells get a row; single-valued cells are left as-is in
# arrive_main_data and matched there directly at query time. Same convention
# as populate_subtables_and_standardize()'s handling of
# uof_dashboard_values_data. ---
value_rows = []
unexpected_tokens = {}

for row in main_rows:
    random_id = row[0]
    for col, cell in zip(MULTI_VALUE_COLS.keys(), row[1:]):
        tokens = parse_cell(cell, MULTI_VALUE_COLS[col])
        is_multi_value = len(tokens) > 1
        for token in tokens:
            if token not in VALID_VALUES[col]:
                unexpected_tokens.setdefault(col, set()).add(token)
            if is_multi_value:
                value_rows.append((random_id, col, token))

for col, tokens in unexpected_tokens.items():
    print(f"WARNING: {col} has values not in the known set (inserted anyway): {sorted(tokens)}")

# --- Rebuild arrive_values_data from scratch ---
cursor.execute("DELETE FROM arrive_values_data")
conn.commit()
print("Cleared arrive_values_data")

token_sql = "INSERT INTO arrive_values_data (Random_ID, column_name, column_value) VALUES (%s, %s, %s)"

batch_size = 500
failed_rows = []
for i in range(0, len(value_rows), batch_size):
    batch = value_rows[i : i + batch_size]
    try:
        cursor.executemany(token_sql, batch)
        conn.commit()
        print(f"Inserted rows {i} to {min(i + batch_size, len(value_rows))}")
    except mysql.connector.Error as e:
        conn.rollback()
        print(f"Batch {i}-{i + batch_size} failed ({e}); retrying row by row to isolate the problem")
        for j, row in enumerate(batch):
            try:
                cursor.execute(token_sql, row)
                conn.commit()
            except mysql.connector.Error as row_err:
                conn.rollback()
                failed_rows.append((i + j, row, str(row_err)))
                print(f"  Row {i + j} failed: {row_err}")

cursor.close()
conn.close()

print(f"\nDone. {len(value_rows) - len(failed_rows)} of {len(value_rows)} tokenized values inserted successfully.")
if failed_rows:
    print(f"{len(failed_rows)} rows failed — see failed_rows list above for row indices and errors.")
