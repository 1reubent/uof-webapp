# use_of_force_database_redesign_project

```
uof-webapp/
├── frontend/
│   ├── query-builder.html
│   └── results-viewer.html
│
├── backend/
│   ├── database/
│   │   ├── schema.sql                      ← full dump: builds DB from scratch
│   │   └── seeds/
│   │       ├── column*values_seed.sql      ← seeds uof_column_values_data
│   │       └── standard_values_seed.sql    ← seeds standard_values_table
│   │
│   ├── etl/
│   │   ├── import_script.py                ← Excel → uof_main_processing_table
│   │   └── clean_and_populate.py           ← UOFPythonExecutionProgram.py
│   │
│   ├── api/                                ← still the pending piece
│   │   └── (endpoints that take a query from the frontend,
│   │        run it against MySQL, return JSON results)
│   │
│   └── config/
│       └── db_config.py                    ← pull the hardcoded host/user/password
│                                               out of the two scripts into one place
│
├── data/
│   └── UoF_database_1k_subset_100120_to_053126.xlsx
│
└── docs/
    ├── Project_Charter_Document.pdf
    ├── Query_and_Response*-_Input_Form_design.docx
    └── Query_to_Claude_-\_Return_Data_Form.docx
```
