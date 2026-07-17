# =====================================================================
# import_arrive_data.py
# Loads the ARRIVE Together "Reports Download File" Excel export into
# arrive_main_data + arrive_values_data.
#
# The Demographic Download File is intentionally NOT loaded — it has
# no unique key (its first column is a pre-aggregated count, not a
# row ID) and cannot be joined back to individual incidents.
#
# Safe to re-run: rows already present (by Random_ID) are skipped,
# same delta pattern as etl_delta.py for the UoF data.
#
# Usage:
#   python import_arrive_data.py
#   python import_arrive_data.py --file "ARRIVE_Reports_Download_File_8_1_2026.xlsx"
# =====================================================================

import argparse
import ast
import sys
from pathlib import Path

import pandas as pd
import numpy as np
import mysql.connector

# Reuse the project's existing config location (backend/config/db_config.py)
sys.path.append(str(Path(__file__).parent / "config"))
try:
    from db_config import DB_CONFIG          # Aiven-style config, incl. SSL
except ImportError:
    # Fallback for teams still using secrets.toml / plain host-user-pass
    import tomllib
    secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
    with open(secrets_path, "rb") as f:
        cfg = tomllib.load(f)["mysql"]
    DB_CONFIG = {
        "host": cfg["host"], "port": cfg.get("port", 3306),
        "user": cfg["user"], "password": cfg["password"],
        "database": cfg["database"],
    }

# ── Column rename map: Excel header -> schema column name ───────────
COL_MAP = {
    "Random_ID":                              "Random_ID",
    "Year of Date_of_Incident":                "Incident_Year",
    "ARRIVE Model":                            "Arrive_Model",
    "Behaviors_Indicated_Prior_to_Arrival":    "Behaviors_Indicated_Prior_to_Arrival",
    "Other_Individuals_on_Scene":              "Other_Individuals_on_Scene",
    "Law_Enforcement_Observed_Behavior":       "Law_Enforcement_Observed_Behavior",
    "Law_Enforcement_Outcomes":                "Law_Enforcement_Outcomes",
    "outreach_attempts":                       "Outreach_Attempts",
    "Mental_Health_Outcome":                   "Mental_Health_Outcome",
    "30_Day_Outcomes":                         "Day_30_Outcomes",
}

# Columns whose values are Python list-literal strings, e.g.
# "['Violence', 'Confused/disoriented persons']" — everything except
# the key, year, model, and outreach-attempts columns.
MULTI_VALUE_COLS = [
    "Behaviors_Indicated_Prior_to_Arrival",
    "Other_Individuals_on_Scene",
    "Law_Enforcement_Observed_Behavior",
    "Law_Enforcement_Outcomes",
    "Mental_Health_Outcome",
    "Day_30_Outcomes",
]


def parse_list_cell(cell):
    """
    Convert a stored Python-list-literal string into an actual list.
    Returns [] for null/empty. Falls back to treating the raw string
    as a single-item list if it isn't valid list syntax (defensive —
    the source data has been consistent so far, but exports change).
    """
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
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
        # Not list syntax — treat whole cell as one value
        return [s]


def to_native(v):
    """Convert numpy/pandas scalar types to plain Python types for the
    MySQL connector (same fix noted in the project README for numpy.int64)."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return None if pd.isna(v) else float(v)
    return v


def load_excel(excel_file: str) -> pd.DataFrame:
    df = pd.read_excel(excel_file)
    df = df.rename(columns=COL_MAP)

    missing = set(COL_MAP.values()) - set(df.columns)
    if missing:
        print(f"  ⚠ WARNING: expected columns not found in file: {missing}")
        print("    The Excel export's headers may have changed — check before proceeding.")

    return df


def build_main_row(row: dict) -> dict:
    """Build the arrive_main_data row: multi-value columns become
    plain comma-joined display text instead of raw list-literal strings."""
    out = {
        "Random_ID": to_native(row.get("Random_ID")),
        "Incident_Year": to_native(row.get("Incident_Year")),
        "Arrive_Model": row.get("Arrive_Model"),
        "Outreach_Attempts": to_native(row.get("Outreach_Attempts")),
    }
    for col in MULTI_VALUE_COLS:
        values = parse_list_cell(row.get(col))
        out[col] = ", ".join(values) if values else None
    return out


def main(excel_file: str):
    print(f"\n{'='*55}")
    print(f"  ARRIVE Together loader — {excel_file}")
    print(f"{'='*55}")

    print("\n[1/5] Loading Excel file…")
    df = load_excel(excel_file)
    print(f"      {len(df):,} rows loaded")

    dup_ids = df["Random_ID"][df["Random_ID"].duplicated()].tolist()
    if dup_ids:
        print(f"  ⚠ WARNING: {len(dup_ids)} duplicate Random_ID values found within the file itself: {dup_ids[:5]}")

    print("\n[2/5] Connecting to database…")
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print("      Connected.")

    print("\n[3/5] Checking for existing Random_IDs…")
    cursor.execute("SELECT Random_ID FROM arrive_main_data")
    existing_ids = {r[0] for r in cursor.fetchall()}
    print(f"      {len(existing_ids):,} already in database")

    df_new = df[~df["Random_ID"].isin(existing_ids)]
    print(f"      {len(df_new):,} new rows to insert")
    print(f"      {len(df) - len(df_new):,} rows skipped (already exist)")

    if df_new.empty:
        print("\n[4/5] Nothing new to insert.")
        print("[5/5] Nothing new to insert.")
        cursor.close(); conn.close()
        print("\n✓ Done. Database already up to date.")
        return

    print(f"\n[4/5] Inserting {len(df_new):,} rows into arrive_main_data…")
    main_cols = ["Random_ID", "Incident_Year", "Arrive_Model", "Outreach_Attempts"] + MULTI_VALUE_COLS
    insert_sql = (
        f"INSERT INTO arrive_main_data ({', '.join(f'`{c}`' for c in main_cols)}) "
        f"VALUES ({', '.join(['%s'] * len(main_cols))})"
    )

    main_rows, value_rows = [], []
    for _, raw_row in df_new.iterrows():
        row_dict = raw_row.to_dict()
        main_row = build_main_row(row_dict)
        main_rows.append(tuple(main_row[c] for c in main_cols))

        # Build token rows for arrive_values_data
        for col in MULTI_VALUE_COLS:
            for token in parse_list_cell(row_dict.get(col)):
                token = token.strip()
                if token:
                    value_rows.append((to_native(main_row["Random_ID"]), col, token))

    batch_size = 100
    for i in range(0, len(main_rows), batch_size):
        cursor.executemany(insert_sql, main_rows[i:i + batch_size])
        print(f"  Inserted rows {i + 1}–{min(i + batch_size, len(main_rows))}")
    conn.commit()

    print(f"\n[5/5] Inserting {len(value_rows):,} tokenized values into arrive_values_data…")
    token_sql = (
        "INSERT INTO arrive_values_data (Random_ID, column_name, column_value) "
        "VALUES (%s, %s, %s)"
    )
    for i in range(0, len(value_rows), 500):
        cursor.executemany(token_sql, value_rows[i:i + 500])
    conn.commit()

    cursor.close()
    conn.close()

    print(f"\n✓ Done.")
    print(f"  New incidents inserted : {len(df_new):,}")
    print(f"  Tokenized values logged: {len(value_rows):,}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load ARRIVE Together data into MySQL.")
    parser.add_argument(
        "--file",
        default="ARRIVE_Reports_Download_File_7_1_2026.xlsx",
        help="Path to the ARRIVE Reports Download Excel file",
    )
    args = parser.parse_args()
    main(args.file)
