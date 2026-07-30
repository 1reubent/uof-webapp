# use_of_force_database_redesign_project

View live at: https://1reubent.github.io/uof-webapp/


```
uof-webapp/
├── frontend/
│   ├── query-builder.html
│   └── results-viewer.html
│
├── backend/
│   ├── database/
│   │   ├── schema_aiven.sql                ← full dump: builds DB from scratch (Aiven/managed MySQL)
│   │   ├── schema.sql                      ← earlier local-MySQL version, superseded by schema_aiven.sql
│   │   └── seeds/
│   │       ├── column_values_seed.sql      ← seeds uof_column_values_data
│   │       └── standard_values_seed.sql    ← seeds standard_values_table
│   │
│   ├── etl/
│   │   ├── import_script.py                ← Excel → uof_main_processing_table
│   │   └── clean_and_populate.py           ← UOFPythonExecutionProgram.py
│   │
│   ├── api/
│   │   └── bridge.py                       ← Flask API: takes a query from the frontend,
│   │                                           runs it against MySQL, returns JSON results
│   │
│   └── config/
│       ├── db_config.py                    ← builds DB_CONFIG from environment variables (committed, no secrets)
│       ├── .env.example                    ← checked-in template — copy to .env and fill in (local dev only)
│       └── ca.pem                          ← Aiven CA cert (gitignored, downloaded from Aiven Console)
│
├── data/
│   └── UoF_database_1k_subset_100120_to_053126.xlsx
│
└── docs/
    ├── Project_Charter_Document.pdf
    ├── Query_and_Response*-_Input_Form_design.docx
    └── Query_to_Claude_-\_Return_Data_Form.docx
```

# UOF Webapp — Project Documentation

- Our database schema design decisions - omar
- The code repository structure - reuben
- How to build the database from scratch, from running the SQL files, importing the data and running the data cleaning/ETL scripts - omar
   - schema.sql - builds the empty tables
   - column_values_seed.sql and standard_values_seed.sql - fills in the ref4rence table
   - UOF
      - import_script
      - clean_and_populate
   - ARRIVE
      - import_arrive_data
      - tokenize_arrive_data
- How to configure and run the website - reuben
- How to run the delta loader - omar


---


## What it is

A tool for turning a New Jersey **Use of Force (UoF)** incident dataset — currently distributed as an Excel file (`data/UoF_database_1k_subset_100120_to_053126.xlsx`, ~1k rows) — into a clean, queryable MySQL database, with a browser-based UI for building filtered queries and paging through results. The repo name (`use_of_force_database_redesign_project`) signals this is a **redesign** of an existing/prior UoF database, not a greenfield build — the messiness handled in the ETL layer (misspellings, inconsistent formats, multi-value fields) is inherited from that source data.

The project has three layers, built in this order:

1.  **Database schema**  (MySQL) — done
2.  **ETL pipeline**  (Python) — Excel → raw staging table → cleaned/standardized table + lookup tables — done
3.  **Frontend**  (static HTML/JS) — query builder + results viewer — done, but  **not yet wired to a live backend**
4.  **API layer**  (`backend/api/`) — the piece that would connect frontend ⟷ MySQL —  **not built yet**  (only a  `.gitkeep`  placeholder exists)

So today the frontend and backend are functionally disconnected demos: the query builder produces SQL/JSON you copy out manually, and the results viewer accepts pasted JSON/CSV rather than a live API response.

----------

## Running the app locally

The database is a managed MySQL instance hosted on [Aiven](https://aiven.io) — there's no local MySQL server to install and no schema to build. `backend/database/schema_aiven.sql` and the seed scripts only need to be (re-)run against Aiven directly if you're standing up a *new* database; if one already exists, skip straight to configuring the connection.

Assumes only Python (3.9+) is already installed. Steps are the same on macOS and Windows except where noted.

### 1. Set up Python

Create a virtual environment and install dependencies:

- **macOS**:
  ```
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
- **Windows** (PowerShell or Command Prompt):
  ```
  python -m venv .venv
  .venv\Scripts\activate
  pip install -r requirements.txt
  ```

Re-activate this environment (`source .venv/bin/activate` / `.venv\Scripts\activate`) in any new terminal you use for the remaining steps.

### 2. Configure the Aiven connection

`backend/config/db_config.py` builds its `DB_CONFIG` from environment variables (loaded from `backend/config/.env` via `python-dotenv` if present), so it's safe to commit — no real credentials live in it. Copy the example env file:

```
cp backend/config/.env.example backend/config/.env      # macOS
copy backend\config\.env.example backend\config\.env    # Windows
```

Then, from the Aiven Console → your MySQL service → **Overview → Quick connect**:

1. Note the host, port, user, and password shown there and fill in `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` in `.env` (leave `DB_NAME` as-is — it's already set up for this project's schema).
2. Download the service's **CA certificate** and save it as `backend/config/ca.pem` (leave `DB_SSL_CA_PATH=ca.pem` as-is).

Both `.env` and `ca.pem` are gitignored on purpose — never commit real credentials or the cert. (This is also how the app is configured on Render — see [Deploying to Render](#deploying-to-render) — except there the values are set directly as environment variables/secret files, no `.env` file involved.)

### 3. Load the incident data

Only needed if the target database doesn't already have data loaded, or you're importing a new Excel export. Safe to re-run either way — each script only processes rows it hasn't seen yet:

```
python backend/etl/import_script.py
python backend/etl/clean_and_populate.py
```

### 4. Start the API

```
python backend/api/bridge.py
```

Leave this running in its own terminal — it serves on `http://localhost:5001`. (macOS-specific note: this project deliberately avoids port 5000 because macOS's AirPlay Receiver listens there by default and silently intercepts requests meant for a local Flask server.)

### 5. Open the frontend

Open `frontend/uof_program_v2.html` directly in a browser (double-click it, or File → Open in your browser). No build step or dev server needed — it's a static file that talks to the API over HTTP from `file://`.

----------

## Data flow / pipeline

```
Excel (.xlsx)
   │  import_script.py
   ▼
uof_main_processing_table   (raw staging table, 1:1 with Excel columns, `processed` flag)
   │  clean_and_populate.py
   ▼
uof_main_data                (cleaned, standardized, one row per incident form)
   +  uof_dashboard_values_data   (tokenized multi-value fields, one row per token)
   +  exceptions_table            (rows/values that failed cleaning/standardization — logged, not dropped)

```

Two static reference tables support the cleaning step and are loaded once via seed scripts, independent of any Excel import:

-   `standard_values_table`  — maps raw value spellings/abbreviations → canonical form (e.g.  `"Sgt."`  →  `"Sergeant"`), used for single-value columns.
-   `uof_column_values_data`  — the master catalog of every valid value for every multi-value column, keyed by  `(Position_Id, Value_Id)`. Also used to validate tokens produced by the multi-value tokenizer.

### `import_script.py`  (Excel → staging)

-   Reads the Excel file with pandas, drops a  `KEEP/DROP`  scratch column from the source spreadsheet.
-   Renames ~40 Excel headers (human-readable, spaced) to the schema's  `Snake_Case`/underscore column names via an explicit  `col_map`  dict.
-   Converts  `Officer_In_Uniform`  from Python bool to MySQL tinyint (1/0).
-   Batch-inserts (100 rows/batch) into  `uof_main_processing_table`, converting NaN →  `None`  so MySQL gets real  `NULL`s.

### `clean_and_populate.py`  (staging → clean)

This is the core of the project and where most of the design decisions live. It:

1.  Pulls only unprocessed rows (`WHERE processed = 0`) from the staging table.
2.  Normalizes whitespace/casing on all text columns; coerces string forms of null (`"None"`,  `"NaN"`,  `"null"`,  `""`) to real NaN.
3.  Maps loose boolean-ish text (`yes/true/1/y`,  `no/false/0/n`) to 1/0 for a small set of genuinely-boolean columns (`Other_Officer_Involved`,  `Officer_In_Uniform`,  `Officer_Injuries_Injured`).
4.  Parses  `Incident_Date`  to a real date.
5.  Coerces a small set of genuinely-integer columns.
6.  Runs  `populate_subtables_and_standardize()`, which is the interesting part:
    -   **Single-value columns**  (`Video_Footage`,  `Officer_Race/Ethnicity`,  `Officer_Rank`,  `Officer_Gender`,  `Officer_Hospital_Treatment`) are looked up in  `standard_values_table`  and rewritten to their canonical spelling. Unmatched values are logged to  `exceptions_table`  rather than silently dropped.
    -   **Multi-value columns**  (most of the rest —  `Subject_Actions`,  `Location_Type`,  `Force_Type`, etc.) are comma-split into individual tokens, each becoming a row in  `uof_dashboard_values_data`. A small hardcoded list (`embedded_commas`) protects specific known values that legitimately contain a comma (e.g.  `"Disturbance (drinking, fighting, disorderly)"`) from being split by temporarily swapping the comma for  `||`  before splitting, then restoring it.
    -   Each token is validated against  `uof_column_values_data`; a miss is logged as an exception (with special-cased messaging for  `Subject_Age`, which is nominally numeric but stored as text because it can contain "Unknown"/"Under 18"/etc.).
7.  Writes the cleaned DataFrame into  `uof_main_data`  (all identifiers backtick-quoted, since several column names contain  `/`  or spaces — e.g.  `Officer_Race/Ethnicity`).
8.  Marks source rows  `processed = 1`  so re-running the script is idempotent / incremental.

**Notable bugs found and fixed during development** (documented inline as comments — worth knowing if you extend this):

-   A misspelling mismatch: both the raw source data and the seed table consistently spell "tightening" as  **"tighening"**  (missing a "t") for one  `Subject_Resistance`  value. The embedded-comma protection pattern originally used the correct spelling and silently never matched, so that value's comma was never protected. Fixed by matching the actual misspelling in use.
-   `Subject_Arrested`  was originally in the boolean-coercion list, which corrupted it to numpy floats (`1.0`/`0.0`) before it reached the tokenizer/lookup stage (which expects the literal strings  `'True'`/`'False'`/`'Not Provided'`) — this silently broke matching for ~986 rows. Fixed by removing it from  `bool_cols`  and letting it flow through as plain text into the standard lookup pipeline like other  `pos_map`  columns.
-   `Subject_Age`  was originally in the integer-coercion list, which wiped every non-single-integer entry (ranges, "Unknown", "Under 18") to NaN before the per-token validator ever got to see it — even though that validator already has bespoke logic to check each token. Fixed by removing it from  `int_cols`.
-   Backtick-quoting was required for  `INSERT`  column lists because some column names contain  `/`  and spaces — unquoted, MySQL threw a syntax error.
-   Raw pandas/numpy scalar types (e.g.  `numpy.int64`) weren't accepted directly by  `mysql-connector-python`  in this environment; added a  `to_native()`  coercion step before insert.

This trail of comments is itself a good signal for an AI picking up the project: it explains _why_ the code looks the way it does, not just what it does — preserve that context if refactoring.

----------

## Database schema (`backend/database/schema.sql`)

MySQL 8, `utf8mb4`/`utf8mb4_0900_ai_ci`. Six tables:


| Table | Purpose |
|-------|---------|
| `uof_main_processing_table` | Raw staging table, 1:1 with Excel columns, plus a `processed` flag. Indexed on `Form_ID` and `processed`. |
| `uof_main_data` | Cleaned/standardized "final" table — same shape as staging minus `processed`. This is the table the frontend's query builder currently targets in its generated SQL comments (though the UI itself says `uof_main_processing_table` — see note below). |
| `uof_dashboard_values_data` | Tokenized multi-value fields: one row per `(Form_Id, Position_Id, Value_Id, Column_Value)` — the normalized/exploded form of columns like `Subject_Actions` that can hold multiple selections per incident. |
| `uof_column_values_data` | Static catalog of every valid value per column position — reference/lookup data, not incident data. |
| `standard_values_table` | Raw-value → standard-value synonym map used during cleaning. |
| `exceptions_table` | Audit log of values that failed cleaning/standardization, keyed to the original form/column, with a human-readable `reason`. Nothing is silently dropped — everything that doesn't clean cleanly is preserved here for review. |
Design choices worth calling out:

-   **Text-typed fields deliberately overridden from more "natural" numeric/boolean types.**  E.g.  `Subject_Arrested`  and  `Subject_Age`  are  `text`  in  `uof_main_data`/`uof_main_processing_table`, annotated inline with  `-- changed from tinyint(1)/int to text by Reuben`  — because the real-world data isn't strictly boolean/numeric (arrest status has a  `"Not Provided"`  state; age can be a range or "Unknown").
-   **Wide, denormalized  `uof_main_data`/`uof_main_processing_table`**  (45 columns) rather than a fully normalized incident/officer/subject schema — this seems to mirror the source Excel form 1:1 for traceability, with normalization happening only for the genuinely multi-value fields (via  `uof_dashboard_values_data`).
-   Schema file is a literal  `mysqldump`  structure dump (`CREATE DATABASE IF NOT EXISTS`  +  `DROP TABLE IF EXISTS`  +  `CREATE TABLE`) — meant to be run once to build the DB from scratch, not a migration-managed schema.

----------

## Frontend (`frontend/`)

Two **standalone, dependency-free HTML files** (single-file, inline `<style>`/`<script>`, no build step, no framework) — designed to be opened directly in a browser or served as static files.

### `query-builder.html`

A form-based SQL query constructor over the 45-column schema.

-   **"Launch gate" pattern**: the Build button stays disabled until the user provides  _either_  an incident date range  _or_  at least one Incident ID — a deliberate guardrail against generating an unbounded  `SELECT *`  over the whole table. This mirrors a real operational concern (don't let someone accidentally dump the entire incident table).
-   Fields are grouped into 7 collapsible sections (Geography & agency, Incident & force, Subject, Officer, Environment, Video, Records & IDs) mirroring the schema groupings used later in the results viewer, using  `<details>`/`<summary>`  for progressive disclosure with live "N set" badges per group.
-   Field types:  `tags`  (chip-based multi-value → SQL  `IN (...)`),  `tags-num`  (numeric IDs),  `range`  (min/max →  `BETWEEN`/`>=`/`<=`).
-   A "Partial text match (LIKE)" toggle switches text-tag filters from exact  `IN`  matching to  `OR`-chained  `LIKE '%value%'`  clauses.
-   Live-renders both a human-readable criteria list and syntax-highlighted SQL as filters are added; "Copy SQL" and "Copy JSON" buttons let the user hand the query off elsewhere (there's no live execution — this is intentionally just a query  _constructor_).
-   Values are inserted via naive string interpolation with manual quote-escaping (`sqlStr`  doubles single quotes) — acceptable for a client-side query  _previewer_  that a human copies out, but  **not safe to point directly at a live DB connection without parameterization**  if/when the API layer executes it.

### `results-viewer.html`

A paged record/table viewer for result sets.

-   No live query execution — instead has a "Load results" panel where you paste a JSON array or CSV/TSV, which gets column-mapped onto the canonical 45-column schema (case/punctuation-insensitive header matching via a normalized lookup, so  `officer race ethnicity`,  `Officer_Race/Ethnicity`, etc. all resolve to the same canonical column).
-   Two view modes:  **Record**  (one incident per screen, grouped into the same 7 categories as the query builder, with keyboard paging — arrow keys/Home/End) and  **Table**  (dense sortable-looking grid with a sticky header and frozen row-number column).
-   Ships with 4 clearly-synthetic sample rows (`SAMPLE-0001`  etc., "Sample Township PD") shown by default so the page isn't blank before any data is loaded — explicitly labeled as sample data in the UI copy.
-   Export to CSV (hand-rolled CSV writer, BOM-prefixed for Excel compatibility) and to XLSX (lazy-loads SheetJS from a CDN on first use, falls back to CSV export if that fails).

Both pages share a consistent visual language (teal/ink palette, monospace for schema/code references, card-based layout) despite being two separate files with no shared CSS/JS — they were clearly designed as a matched pair, not just independently.

----------

## Config & environment

-   `backend/config/db_config.py`  holds  `DB_CONFIG`  (host/port/user/password/database, plus Aiven's SSL settings), built entirely from environment variables (`DB_HOST`,  `DB_PORT`,  `DB_USER`,  `DB_PASSWORD`,  `DB_NAME`,  `DB_SSL_CA_PATH`) — no real credentials in the file itself, so it's committed.  `.env.example`  is the checked-in template for local dev, copied to  `.env`  (gitignored) and loaded via  `python-dotenv`. `import_script.py`, `clean_and_populate.py`, and `bridge.py` all  `sys.path.append`  their way to  `../config`  to import it.
-   `backend/config/ca.pem`  is the Aiven-issued CA certificate, gitignored, downloaded once from the Aiven Console and referenced by `db_config.py`'s `ssl_ca` (a relative  `DB_SSL_CA_PATH`  is resolved relative to the config directory, not the process's working directory, so an absolute path — e.g. Render's mounted Secret File — also works unchanged).
-   `db_config.py`  also sets  `use_pure: True`  — the default C-extension connector unconditionally calls  `SSL_CTX_set_default_verify_paths()`, which fails on macOS (no Linux-style default cert store paths); the pure-Python implementation avoids that call and uses `ssl_ca` directly.
-   Python deps pinned in  `requirements.txt`:  `pandas`,  `numpy`,  `mysql-connector-python`,  `openpyxl`  (Excel reading),  `flask`/`flask-cors`  (API),  `python-dotenv`  (loads  `.env`  locally),  `gunicorn`  (production WSGI server, used on Render),  `et_xmlfile`/`python-dateutil`/`six`  (transitive).
-   No  `package.json`/Node tooling anywhere — frontend is deliberately zero-build.

----------

## Deploying to Render

The repo includes a `render.yaml` [Blueprint](https://render.com/docs/blueprint-spec) that defines a single web service (`uof-webapp-api`) running `bridge.py` behind `gunicorn`.

1. In the Render dashboard: **New → Blueprint**, point it at this repo/branch. Render reads `render.yaml` and creates the service.
2. The blueprint declares `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` with `sync: false` — Render will prompt you to fill these in (same values as your local `.env`). `FLASK_SECRET_KEY` is auto-generated.
3. **CA cert**: `render.yaml` can't upload file contents, so add it by hand once — in the service's **Environment** tab, add a **Secret File** named `ca.pem` with the path `/etc/secrets/ca.pem` and paste in the contents of your local `backend/config/ca.pem`. The blueprint already sets `DB_SSL_CA_PATH=/etc/secrets/ca.pem` to match.
4. Deploy. Render runs `pip install -r requirements.txt` then `gunicorn backend.api.bridge:app`, binding to the `$PORT` it provides automatically.
5. Once live, update `BRIDGE_URL` in `frontend/uof_program_v2.html` (currently hardcoded to `http://localhost:5001/query`) to point at the deployed service's `/query` URL.

If you'd rather configure it by hand instead of via the blueprint: **New → Web Service**, build command `pip install -r requirements.txt`, start command `gunicorn backend.api.bridge:app`, and set the same env vars/secret file as above.

----------

## What's explicitly unfinished

Per the README's own annotations:

-   `backend/api/`  — the layer that would take a query from the frontend, execute it against MySQL, and return JSON to the results viewer. Currently just a  `.gitkeep`.
-   `docs/`  contains a Project Charter PDF and two Word docs (`Query_and_Response_-_Input_Form_design.docx`,  `Query_to_Claude_-_Return_Data_Form.docx`) describing the intended query/response form design — these weren't machine-readable in this pass (no  `poppler`/docx parser available) but are likely the authoritative spec for what the API layer should look like, if you want an AI to consult them.

If you're handing this to another AI to continue the work, the natural next step is clearly **building the API layer** to connect `query-builder.html`'s generated query to a live MySQL execution, returning JSON that `results-viewer.html` can consume directly instead of via copy-paste — at which point the query builder's string-interpolated SQL construction should be replaced with parameterized queries server-side.

---

