import os
import sys
import mysql.connector
import pandas as pd
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from db_config import DB_CONFIG

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def populate_subtables_and_standardize(conn, df):
    cursor = conn.cursor(dictionary=True)
    pos_map = {
        'Video_Footage': 15, 'Officer_Race/Ethnicity': 23, 'Officer_Rank': 24, 'Officer_Gender': 25, 'Officer_Hospital_Treatment': 29,
        'Indoor_Or_Outdoor': 13, 'Incident_Weather': 14, 'Video_Type': 16, 'Incident_Lighting': 17, 'Location_Type': 18, 
        'Incident_Type': 19, 'Contact_Origin': 20, 'Planned_Contact': 21, 'Officer_Injury_Type': 26, 'Officer_Medical_Treatment': 28, 
        'Subject_Injured': 31, 'Subject_Injured_Prior': 32, 'Perceived_Condition': 33, 
        'Subject_Actions': 34, 'Subject_Resistance': 35, 'Subject_Medical Treatment': 36, 'Subject_Injury Type': 37, 
        'Subject_Arrested': 38, 'Subject_Type': 40, 'Subject_Age': 41, 'Subject_Race/Ethnicity': 42, 'Subject_Gender': 43, 'Force_Type': 44
    }
    single_cols = {'Video_Footage', 'Officer_Race_Ethnicity', 'Officer_Rank', 'Officer_Gender', 'Officer_Hospital_Treatment'}
    embedded_commas = [
        ('Location_Type', 'Alcohol Establishment (bar, club, casino)'), ('Incident_Type', 'Disturbance (drinking, fighting, disorderly)'),
        ('Planned_Contact', 'Judicial Order Service (TRO, FRO, etc.)'), ('Subject_Actions', 'Attack with Hands,fists,legs'),
        ('Subject_Actions', 'Threat with Hands,fists,legs'), ('Subject_Actions', 'Threat to Strike with open hand, fist, or elbow'),
        ('Subject_Actions', 'Strike with open hand, fist, or elbow'),
        # ('Subject_Resistance', 'Resistive tension (stiffening, tightening muscles)')
        # NOTE: both the raw source data and the uof_column_values_data seed table
        # (Position_Id 35, Value_Id 3) consistently spell this "tighening" (missing
        # a "t"), not "tightening". The correctly-spelled pattern here never matched,
        # so the embedded comma was never protected and got split into two bogus
        # tokens ("Resistive tension (stiffening" / "tighening muscles)"), both
        # logged as exceptions. Fixed to match the actual (mis-)spelling in use.
        ('Subject_Resistance', 'Resistive tension (stiffening, tighening muscles)')
    ]

    cursor.execute("SELECT column_name, raw_value, standard_value FROM standard_values_table")
    std_lookup = {(r['column_name'].strip().lower(), r['raw_value'].strip().lower()): r['standard_value'] for r in cursor.fetchall()}
    cursor.execute("SELECT Position_Id, Column_Value, Value_Id FROM uof_column_values_data")
    mv_lookup = {(r['Position_Id'], r['Column_Value'].strip().lower()): r['Value_Id'] for r in cursor.fetchall()}

    dash_records, exceptions, processed_ids = [], [], []

    for i, row in df.iterrows():
        fid = row['Form_ID']
        processed_ids.append((int(fid),))
        for col, pid in pos_map.items():
            if col not in df.columns or pd.isna(df.at[i, col]) or str(df.at[i, col]).strip() == "": continue
            raw_str = str(df.at[i, col]).strip()

            if col in single_cols:
                db_col = col.replace("_", " ").strip().lower()
                if (db_col, raw_str.lower()) in std_lookup:
                    df.at[i, col] = std_lookup[(db_col, raw_str.lower())]
                else:
                    exceptions.append((str(fid), pid, col, raw_str, f"No match found in standard_values_table for {raw_str}"))
            else:
                temp_str = raw_str
                for c_name, pattern in embedded_commas:
                    if col == c_name and pattern in temp_str: temp_str = temp_str.replace(pattern, pattern.replace(',', '||'))
                
                tokens = [t.strip().replace('||', ',') for t in temp_str.split(',') if t.strip()]
                for idx, token in enumerate(tokens, start=1):
                    db_val_id = mv_lookup.get((pid, token.lower()), idx)
                    dash_records.append((int(fid), pid, db_val_id, token))
                    
                    if col == 'Subject_Age' and (not token.isdigit() or int(token) < 0):
                        exceptions.append((str(fid), pid, col, token, f"Non-integer value '{token}' logged for Subject_Age"))
                    elif col != 'Subject_Age' and (pid, token.lower()) not in mv_lookup:
                        exceptions.append((str(fid), pid, col, token, f"Token '{token}' failed reference seed match verification"))

    if dash_records: cursor.executemany("INSERT INTO uof_dashboard_values_data (Form_Id, Position_Id, Value_Id, Column_Value) VALUES (%s, %s, %s, %s)", dash_records)
    if exceptions: cursor.executemany("INSERT INTO exceptions_table (form_id, position_id, column_name, original_value, reason) VALUES (%s, %s, %s, %s, %s)", exceptions)
    cursor.executemany("UPDATE uof_main_processing_table SET processed = 1 WHERE Form_ID = %s", processed_ids)
    cursor.close()
    return df

def clean_uof_data():
    conn = get_db_connection()
    
    print("Reading data from uof_main_processing_table...")
    # 2. Extract unprocessed raw data into a Pandas DataFrame
    query = "SELECT * FROM uof_main_processing_table WHERE processed = 0"
    df = pd.read_sql(query, conn)
    
    if df.empty:
        print("No data found to clean.")
        conn.close()
        return

    print(f"Processing {len(df)} rows...")

    # 3. Data Cleaning Pipeline
    
    # Text Normalization (Trimming whitespace and unifying casing)
    text_cols = df.select_dtypes(include=['object', 'str']).columns
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()
        # Replace 'None', 'NaN', 'null' strings with actual NaN
        df[col] = df[col].replace(['None', 'NaN', 'null', 'nan', ''], np.nan)

    # Convert Booleans (Handling variations of True/False/Yes/No/1/0)
    # bool_cols = ['Other_Officer_Involved', 'Officer_In_Uniform',
    #              'Officer_Injuries_Injured', 'Subject_Arrested']
    # NOTE: Subject_Arrested is a `text` column in uof_main_data whose values are
    # matched against the literal strings 'True'/'False'/'Not Provided' in
    # uof_column_values_data (Position_Id 38). Converting it to 1/0/None here
    # corrupted it to numpy floats ("1.0"/"0.0") by the time it reached the
    # multi-value tokenizer, so it never matched the seed table and got logged
    # as an exception for ~986 rows. Removed it from bool_cols; it should stay
    # as the original text and be handled by populate_subtables_and_standardize
    # like the other pos_map columns.
    bool_cols = ['Other_Officer_Involved', 'Officer_In_Uniform',
                 'Officer_Injuries_Injured']
    
    def map_boolean(val):
        if pd.isna(val):
            return None
        val_str = str(val).lower().strip()
        if val_str in ['yes', 'true', '1', 'y']:
            return 1
        if val_str in ['no', 'false', '0', 'n']:
            return 0
        return None

    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].apply(map_boolean)

    # Convert Dates
    if 'Incident_Date' in df.columns:
        df['Incident_Date'] = pd.to_datetime(df['Incident_Date'], errors='coerce').dt.date

    # Convert Integers (Coercing errors to NaN, then filling or leaving as NULL)
    # int_cols = ['Form_ID', 'User_ID', 'Officer_Age', 'Total_Sub_Injured', 'Subject_Age', 'Incident_Year']
    # NOTE: Subject_Age is a `text` column in uof_main_data and is a multivalue
    # field (single int, comma-separated ints, or text like "Unknown"/"Under 18").
    # Forcing it through pd.to_numeric(errors='coerce') here wiped out every
    # non-single-integer entry to NaN before populate_subtables_and_standardize()
    # ever ran, even though that function already tokenizes Subject_Age per-value
    # and logs an exception for any non-digit token. Removed it from int_cols so
    # the raw text is preserved and reaches that per-token validation instead.
    int_cols = ['Form_ID', 'User_ID', 'Officer_Age', 'Total_Sub_Injured', 'Incident_Year']
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64') # Capital 'I' allows NaN in int columns

    # Run subtables processor and single value lookup standardization
    df = populate_subtables_and_standardize(conn, df)

    # Drop processing flag column so it is excluded from uof_main_data
    if 'processed' in df.columns:
        df = df.drop(columns=['processed'])

    # 4. Load Cleaned Data into uof_main_data
    cursor = conn.cursor()
    
    # Create the insert query dynamically based on dataframe columns
    # columns = ", ".join(df.columns)
    # NOTE: some column names contain '/' or spaces (e.g. Officer_Race/Ethnicity,
    # Subject_Medical Treatment), which is invalid bare SQL syntax and threw
    # "You have an error in your SQL syntax ... near '/Ethnicity, ...'". Backtick-
    # quoting each identifier (as import_script.py already does) fixes it.
    columns = ", ".join([f"`{c}`" for c in df.columns])
    placeholders = ", ".join(["%s"] * len(df.columns))
    insert_query = f"INSERT INTO uof_main_data ({columns}) VALUES ({placeholders})"
    
    # Convert DataFrame back to list of tuples, replacing NaN with None for MySQL NULL compliance
    # records = df.replace({np.nan: None}).to_records(index=False)
    # records_list = [tuple(x) for x in records]

    # NOTE: the above produced numpy scalar types (e.g. numpy.int64) that this
    # environment's mysql-connector-python could not convert directly, causing
    # "Python type numpy.int64 cannot be converted". Coercing to native Python
    # types below as a fix; leaving the original commented out in case it works
    # fine in other environments (e.g. different mysql-connector version).
    def to_native(v):
        if pd.isna(v):
            return None
        if isinstance(v, np.generic):
            return v.item()
        return v

    records_list = [
        tuple(to_native(v) for v in row)
        for row in df.itertuples(index=False, name=None)
    ]

    print("Writing cleaned records to uof_main_data...")
    try:
        cursor.executemany(insert_query, records_list)
        conn.commit()
        print(f"Successfully cleaned and inserted {cursor.rowcount} records.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    clean_uof_data()