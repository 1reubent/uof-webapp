import mysql.connector
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

# 1. Database Connection Configuration
db_config = {
  "host": "localhost",
  "user": "root",
  "password": "Omarislam07!",
  "database": "uof_project",
}

engine = create_engine(
  f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"
)


def get_db_connection():
  return mysql.connector.connect(**db_config)


def clean_uof_data():
  conn = get_db_connection()

  print("Reading data from uof_main_processing_table...")
  # 2. Extract raw data into a Pandas DataFrame
  query = "SELECT * FROM uof_main_processing_table"
  df = pd.read_sql(query, engine)

  if df.empty:
    print("No data found to clean.")
    conn.close()
    return

  print(f"Processing {len(df)} rows...")

  # Drop staging-only columns that don't exist in the destination table
  df = df.drop(columns=["processed"], errors="ignore")

  # 3. Data Cleaning Pipeline

  # Text Normalization (Trimming whitespace and unifying casing)
  text_cols = df.select_dtypes(include=["object", "str"]).columns
  for col in text_cols:
    df[col] = df[col].astype(str).str.strip()
    # Replace 'None', 'NaN', 'null' strings with actual NaN
    df[col] = df[col].replace(["None", "NaN", "null", "nan", ""], np.nan)

    # Preserve multiple numeric ages and derive the Under_18 flag
  def normalize_under_18(value):
    if pd.isna(value):
      return None

    value_text = str(value).strip().lower()

    if value_text in ["1", "1.0", "true", "yes"]:
      return 1

    if value_text in ["0", "0.0", "false", "no"]:
      return 0

    return None

  def clean_subject_age(raw_age, existing_under_18):
    existing_flag = normalize_under_18(existing_under_18)

    if pd.isna(raw_age):
      return None, existing_flag

    tokens = [
      token.strip()
      for token in str(raw_age).split(",")
      if token.strip()
    ]

    if not tokens:
      return None, existing_flag

    has_under_18 = any(
      token.lower() == "under 18"
      for token in tokens
    )

    numeric_ages = [
      token
      for token in tokens
      if token.isdigit()
    ]

    has_unknown_value = any(
      not token.isdigit()
      and token.lower() != "under 18"
      for token in tokens
    )

    cleaned_age = ", ".join(numeric_ages) if numeric_ages else None

    if has_under_18:
      under_18 = 1
    elif existing_flag is not None:
      under_18 = existing_flag
    elif has_unknown_value:
      under_18 = None
    else:
      under_18 = 0

    return cleaned_age, under_18

  if "Under_18" not in df.columns:
    df["Under_18"] = None

  parsed_ages = [
    clean_subject_age(age, under_18)
    for age, under_18 in zip(
      df["Subject_Age"],
      df["Under_18"]
    )
  ]

  df[["Subject_Age", "Under_18"]] = pd.DataFrame(
    parsed_ages,
    index=df.index,
    columns=["Subject_Age", "Under_18"],
  )
  
  # Convert Booleans (Handling variations of True/False/Yes/No/1/0)
  bool_cols = [
    "Other_Officer_Involved",
    "Officer_In_Uniform",
    "Officer_Injuries_Injured",
    ]

  def map_boolean(val):
    if pd.isna(val):
      return None

    # Handle Python/Pandas booleans
    if isinstance(val, (bool, np.bool_)):
      return int(val)

    # Handle numeric 1, 0, 1.0, and 0.0
    if isinstance(val, (int, float, np.integer, np.floating)):
      if val == 1:
        return 1
      if val == 0:
        return 0

    val_str = str(val).lower().strip()

    if val_str in ["yes", "true", "1", "1.0", "y"]:
      return 1

    if val_str in ["no", "false", "0", "0.0", "n"]:
      return 0

    if val_str in ["not provided", "unknown", "none", "null", ""]:
      return None

    return None

  for col in bool_cols:
    if col in df.columns:
      df[col] = df[col].apply(map_boolean)

  # Convert Dates
  if "Incident_Date" in df.columns:
    df["Incident_Date"] = pd.to_datetime(df["Incident_Date"], errors="coerce").dt.date

  # Convert Integers (Coercing errors to NaN, then filling or leaving as NULL)
  int_cols = [
    "Form_ID",
    "User_ID",
    "Officer_Age",
    "Total_Sub_Injured",
    "Incident_Year",
  ]
  for col in int_cols:
    if col in df.columns:
      df[col] = pd.to_numeric(df[col], errors="coerce").astype(
        "Int64"
      )  # Capital 'I' allows NaN in int columns

  # 4. Load Cleaned Data into uof_main_data
  cursor = conn.cursor()

  # Create the insert query dynamically based on dataframe columns
  columns = ", ".join(f"`{col}`" for col in df.columns)
  placeholders = ", ".join(["%s"] * len(df.columns))
  insert_query = f"INSERT INTO uof_main_data ({columns}) VALUES ({placeholders})"

  # Convert DataFrame to native Python types for MySQL compatibility
  records_list = [
    tuple(None if pd.isna(v) else v.item() if hasattr(v, "item") else v for v in row)
    for row in df.itertuples(index=False, name=None)
  ]

  print("Writing cleaned records to uof_main_data...")

  try:
    source_count = len(df)

    if df["Form_ID"].isna().any():
      raise ValueError("Source contains rows with a missing Form_ID.")

    source_distinct_ids = int(df["Form_ID"].nunique())

    if source_count != source_distinct_ids:
      raise ValueError(
        f"Source contains duplicate Form_ID values: "
        f"{source_count} rows but {source_distinct_ids} distinct Form_ID values."
      )

    # DELETE is transactional for these InnoDB tables.
    # If validation fails, rollback restores the previous uof_main_data rows.
    conn.start_transaction()

    cursor.execute("DELETE FROM uof_main_data")
    cursor.executemany(insert_query, records_list)

    cursor.execute("""
      SELECT
        COUNT(*) AS total_rows,
        COUNT(DISTINCT Form_ID) AS distinct_form_ids
      FROM uof_main_data
    """)

    target_count, target_distinct_ids = cursor.fetchone()

    if target_count != source_count:
      raise ValueError(
        f"Row-count validation failed: source={source_count}, "
        f"destination={target_count}"
      )

    if target_distinct_ids != source_distinct_ids:
      raise ValueError(
        f"Form_ID validation failed: source={source_distinct_ids}, "
        f"destination={target_distinct_ids}"
      )

    conn.commit()

    print(
      f"Success: committed {target_count} rows "
      f"with {target_distinct_ids} distinct Form_ID values."
    )

  except (mysql.connector.Error, ValueError) as err:
    conn.rollback()
    print(f"Import failed and was rolled back: {err}")

  finally:
    cursor.close()
    conn.close()
    engine.dispose()


if __name__ == "__main__":
  clean_uof_data()
