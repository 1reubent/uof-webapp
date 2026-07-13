-- =============================================================================
-- seed_standard_values.sql
-- Populates standard_values_table with known raw values and their standard forms.
--
-- PURPOSE:
--   This table is used during the cleaning procedure to overwrite synonyms
--   (misspellings, abbreviations, casing variants, trailing spaces) with their
--   canonical standard forms before inserting into uof_main_data.
--
-- DESIGN DECISIONS DOCUMENTED:
--   - Trailing spaces are stripped (e.g. 'Other ' -> 'Other'). Not treated as
--     synonyms; just whitespace normalization. Documented here for traceability.
--   - 'Used arms' and 'Used arms/hands' are treated as DISTINCT standard values
--     per project decision. No synonym mapping between them.
--   - 'Dispatched' and 'Officer Dispatched' are treated as DISTINCT standard
--     values per project decision.
--   - Officer Rank synonyms: see section below. Some ambiguous mappings are
--     flagged with -- REVIEW comments for human verification.
--
-- USAGE:
--   Run once before executing the cleaning stored procedure.
--   Safe to re-run: uses INSERT IGNORE to avoid duplicate key errors.
-- =============================================================================

-- Make sure the table exists with the correct schema before running.
-- Expected schema:
--   standard_value_id INT NOT NULL AUTO_INCREMENT,
--   position_id SMALLINT DEFAULT NULL,
--   column_name VARCHAR(64) NOT NULL,
--   raw_value VARCHAR(255) NOT NULL,
--   standard_value TEXT NOT NULL,
--   PRIMARY KEY (standard_value_id),
--   UNIQUE KEY uq_column_raw (column_name, raw_value)

-- =============================================================================
-- OFFICER RANK (position_id = 24)
-- Most complex column. Many abbreviations, misspellings, and agency-specific
-- titles that don't map cleanly to a universal standard.
-- Strategy: standardize clear duplicates; leave genuinely distinct ranks as-is.
-- =============================================================================

INSERT IGNORE INTO standard_values_table (position_id, column_name , raw_value, standard_value) VALUES

-- Sergeant variants
(24, 'Officer Rank', 'Sgt',               'Sergeant'),
(24, 'Officer Rank', 'Sgt.',              'Sergeant'),

-- Lieutenant variants
(24, 'Officer Rank', 'LT',               'Lieutenant'),
(24, 'Officer Rank', 'Lieutentant',       'Lieutenant'),   -- misspelling

-- Detective Sergeant variants
(24, 'Officer Rank', 'Det. Sgt.',         'Detective Sergeant'),
(24, 'Officer Rank', 'Det. Sergeant',     'Detective Sergeant'),

-- Correction Officer variants
(24, 'Officer Rank', 'Corrections Officer',      'Correction Officer'),
(24, 'Officer Rank', 'Correction Officer/Sgt',   'Correction Officer/Sgt.'),  -- normalize punctuation

-- Sheriff's Officer variants (capitalization)
(24,'Officer Rank',	 'Sheriff\'S Officer','Sheriff\'s Officer'),
(24,'Officer Rank','Sheriff\'S Officer Sergeant','Sheriff\'s Officer Sergeant'),

-- Police Officer casing
(24, 'Officer Rank', 'police officer',    'Police Officer'),

-- Staff Sergeant variants
(24, 'Officer Rank', 'Staff Sgt.',        'Staff Sergeant'),

-- Patrol Officer variants
-- REVIEW: 'PTL' is likely Patrolman/Patrol Officer. Confirm with mentors.
(24, 'Officer Rank', 'PTL',              'Patrol Officer'),

-- Sgt. First Class vs Sgt First Class
(24, 'Officer Rank', 'Sgt. First Class', 'Sgt. First Class');   -- already standard, no change needed

-- Identity mappings for ranks confirmed in the data that had no entry:
INSERT IGNORE INTO standard_values_table (position_id, column_name, raw_value, standard_value) VALUES
(24, 'Officer Rank', 'Not Provided',  'Not Provided'),
(24, 'Officer Rank', 'Officer',       'Officer'),
(24, 'Officer Rank', 'Trooper',       'Trooper'),
(24, 'Officer Rank', 'Detective',     'Detective'),
(24, 'Officer Rank', 'Agency User',   'Agency User'),
(24, 'Officer Rank', 'Patrolman',     'Patrolman'),
(24, 'Officer Rank', 'Sergeant',      'Sergeant'),
(24, 'Officer Rank', 'SLEO II',       'SLEO II'),
(24, 'Officer Rank', 'Corporal',      'Corporal'),
(24, 'Officer Rank', 'Captain',       'Captain'),
(24, 'Officer Rank', 'Other',         'Other'),
(24, 'Officer Rank', 'Investigator',  'Investigator');

-- REVIEW: The following abbreviations are still ambiguous and may need mentor input:
--   'COP'   - Chief of Police? Map to 'Chief'? Left as-is for now.
--   'DSFC'  - Detective Sergeant First Class? No confident mapping.
--   'LEO'   - Law Enforcement Officer (generic). No confident mapping.
--   'PPO'   - Probationary Police Officer? No confident mapping.
--   'SFC'   - Sergeant First Class? No confident mapping.
--   'SRO'   - School Resource Officer? No confident mapping.
--   'SWAT'  - Team role, not a rank. Leave as-is.
--   'Class II', 'SLEO I/II/III' - NJ-specific classifications. Leave as-is.
--   'Major Crimes Division' - division name, not a rank. REVIEW.

-- =============================================================================
-- OFFICER GENDER (position_id = 25)
-- Clean in the current dataset. Entries included for longevity against future
-- dirty imports. Standard values confirmed from data: 'Female', 'Male', 'Other'
-- =============================================================================

INSERT IGNORE INTO standard_values_table (position_id, column_name, raw_value, standard_value) VALUES
(25, 'Officer Gender', 'Female', 'Female'),
(25, 'Officer Gender', 'Male',   'Male'),
(25, 'Officer Gender', 'Other',  'Other');

-- =============================================================================
-- OFFICER RACE/ETHNICITY (position_id = 23)
-- Clean in the current dataset. Entries included for longevity.
-- =============================================================================

INSERT IGNORE INTO standard_values_table (position_id, column_name, raw_value, standard_value) VALUES
(23, 'Officer Race/Ethnicity', 'American Indian',                          'American Indian'),
(23, 'Officer Race/Ethnicity', 'Asian',                                    'Asian'),
(23, 'Officer Race/Ethnicity', 'Black or African American',                'Black or African American'),
(23, 'Officer Race/Ethnicity', 'Hispanic',                                 'Hispanic'),
(23, 'Officer Race/Ethnicity', 'Native Hawaiian or other Pacific Islander','Native Hawaiian or other Pacific Islander'),
(23, 'Officer Race/Ethnicity', 'Not Provided',                             'Not Provided'),
(23, 'Officer Race/Ethnicity', 'Other',                                    'Other'),
(23, 'Officer Race/Ethnicity', 'Two or more races',                        'Two or more races'),
(23, 'Officer Race/Ethnicity', 'White',                                    'White');

-- =============================================================================
-- VIDEO FOOTAGE (position_id = 15)
-- Clean in the current dataset. Entries included for longevity.
-- =============================================================================

INSERT IGNORE INTO standard_values_table (position_id, column_name, raw_value, standard_value) VALUES
(15, 'Video Footage', 'Yes',     'Yes'),
(15, 'Video Footage', 'No',      'No'),
(15, 'Video Footage', 'Unknown', 'Unknown');

-- =============================================================================
-- OFFICER INJURIES INJURED (position_id = 27)
-- Clean in the current dataset. Entries included for longevity.
-- =============================================================================

-- ignore the following commented-out entries; they are boolean columns  

-- TINYINT(1) column in uof_main_data. Same pattern as Other Officer Involved.
-- 'Not Provided' handled as NULL by the procedure (no entry needed here).
-- INSERT IGNORE INTO standard_values_table (position_id, column_name, raw_value, standard_value) VALUES
-- (27, 'Officer Injuries Injured', 'True',  '1'),
-- (27, 'Officer Injuries Injured', 'False', '0');

-- =============================================================================
-- OTHER OFFICER INVOLVED (position_id = 10)
-- TINYINT(1) column in uof_main_data. Standard values map to '1' or '0'.
-- 'Not Provided' is omitted here — the procedure checks for a NULL lookup
-- result and inserts NULL directly into the tinyint column.
-- The procedure casts '1'/'0' to SIGNED before inserting.
-- =============================================================================

-- ignore the following commented-out entries; they are boolean columns 

-- INSERT IGNORE INTO standard_values_table (position_id, column_name, raw_value, standard_value) VALUES
-- (10, 'Other Officer Involved', 'True',  '1'),
-- (10, 'Other Officer Involved', 'False', '0');

-- =============================================================================
-- OFFICER HOSPITAL TREATMENT (position_id = 29)
-- Clean in the current dataset. Entries included for longevity.
-- NOTE: 'Unknown' included as a standard value even though not seen in current
-- subset -- it is a logically valid value for this field.
-- =============================================================================

INSERT IGNORE INTO standard_values_table (position_id, column_name, raw_value, standard_value) VALUES
(29, 'Officer Hospital Treatment', 'Admitted',            'Admitted'),
(29, 'Officer Hospital Treatment', 'Treated and Released','Treated and Released'),
(29, 'Officer Hospital Treatment', 'Unknown',             'Unknown');

-- =============================================================================
-- OFFICER IN UNIFORM (position_id = 11)
-- Now tinyint(1) in uof_main_processing_table. Imports correctly as a boolean
-- directly from Excel. No cleaning needed; not included in standard_values_table.
-- =============================================================================

-- No entries needed.

-- =============================================================================
-- TRAILING SPACE NORMALIZATION
-- The following raw values appear in multi-value columns with trailing spaces.
-- They are normalized by stripping whitespace, not treated as synonym mapping.
-- This table entry ensures the cleaning procedure maps them to their trimmed form.
-- Affected columns and values:
--   Planned Contact    : 'Other '
--   Incident Type      : 'Trespassing '
--   Subject Resistance : 'Attempt to flee '
--   Subject Actions    : 'Other Threat '  (appears with trailing space in some rows)
-- =============================================================================

-- not needed; traiilng spaces handled by the cleaning procedure. Documented here for traceability

-- -- Planned Contact trailing spaces (position_id = 21)
-- INSERT IGNORE INTO standard_values_table (position_id, column_name, raw_value, standard_value) VALUES
-- (21, 'Planned Contact', 'Other ',    'Other');

-- -- Incident Type trailing spaces (position_id = 19)
-- INSERT IGNORE INTO standard_values_table (position_id, column_name, raw_value, standard_value) VALUES
-- (19, 'Incident Type', 'Trespassing ',  'Trespassing');

-- -- Subject Resistance trailing spaces (position_id = 35)
-- INSERT IGNORE INTO standard_values_table (position_id, column_name, raw_value, standard_value) VALUES
-- (35, 'Subject Resistance', 'Attempt to flee ',  'Attempt to flee');

-- -- Subject Actions trailing spaces (position_id = 34)
-- INSERT IGNORE INTO standard_values_table (position_id, column_name, raw_value, standard_value) VALUES
-- (34, 'Subject Actions', 'Other Threat ',  'Other Threat');

-- =============================================================================
-- SUBJECT GENDER (position_id = 43)
-- Per-subject repeating field. Clean in current dataset. Included for longevity.
-- =============================================================================

INSERT IGNORE INTO standard_values_table (position_id, column_name, raw_value, standard_value) VALUES
(43, 'Subject Gender', 'Male',         'Male'),
(43, 'Subject Gender', 'Female',       'Female'),
(43, 'Subject Gender', 'Non-Binary/X', 'Non-Binary/X'),
(43, 'Subject Gender', 'Not Provided', 'Not Provided');

-- =============================================================================
-- SUBJECT RACE/ETHNICITY (position_id = 42)
-- Per-subject repeating field. Clean in current dataset. Included for longevity.
-- Same value set as Officer Race/Ethnicity.
-- =============================================================================

INSERT IGNORE INTO standard_values_table (position_id, column_name, raw_value, standard_value) VALUES
(42, 'Subject Race/Ethnicity', 'American Indian',                          'American Indian'),
(42, 'Subject Race/Ethnicity', 'Asian',                                    'Asian'),
(42, 'Subject Race/Ethnicity', 'Black or African American',                'Black or African American'),
(42, 'Subject Race/Ethnicity', 'Hispanic',                                 'Hispanic'),
(42, 'Subject Race/Ethnicity', 'Native Hawaiian or other Pacific Islander','Native Hawaiian or other Pacific Islander'),
(42, 'Subject Race/Ethnicity', 'Not Provided',                             'Not Provided'),
(42, 'Subject Race/Ethnicity', 'Other',                                    'Other'),
(42, 'Subject Race/Ethnicity', 'Two or more races',                        'Two or more races'),
(42, 'Subject Race/Ethnicity', 'White',                                    'White');

-- =============================================================================
-- SUBJECT TYPE (position_id = 40)
-- Per-subject repeating field. Clean in current dataset. Included for longevity.
-- NOTE: 'Other' and 'Not Provided' included as logically valid values even if
-- not seen in current subset.
-- =============================================================================

INSERT IGNORE INTO standard_values_table (position_id, column_name, raw_value, standard_value) VALUES
(40, 'Subject Type', 'Person',             'Person'),
(40, 'Subject Type', 'Animal',             'Animal'),
(40, 'Subject Type', 'Unknown Subject(s)', 'Unknown Subject(s)'),
(40, 'Subject Type', 'Other',              'Other'),
(40, 'Subject Type', 'Not Provided',       'Not Provided');

-- =============================================================================
-- SUBJECT ARRESTED (position_id = 38)
-- Per-subject repeating field. Clean in current dataset. Included for longevity.
-- =============================================================================

INSERT IGNORE INTO standard_values_table (position_id, column_name, raw_value, standard_value) VALUES
(38, 'Subject Arrested', 'True',         'True'),
(38, 'Subject Arrested', 'False',        'False'),
(38, 'Subject Arrested', 'Not Provided', 'Not Provided');

-- =============================================================================
-- SUBJECT INJURED IN INCIDENT (position_id = 31)
-- Per-subject repeating field. Clean in current dataset. Included for longevity.
-- =============================================================================

INSERT IGNORE INTO standard_values_table (position_id, column_name, raw_value, standard_value) VALUES
(31, 'Subject Injured In Incident', 'Yes',     'Yes'),
(31, 'Subject Injured In Incident', 'No',      'No'),
(31, 'Subject Injured In Incident', 'Unknown', 'Unknown');

-- =============================================================================
-- SUBJECT INJURED PRIOR TO INCIDENT (position_id = 32)
-- Per-subject repeating field. Clean in current dataset. Included for longevity.
-- =============================================================================

INSERT IGNORE INTO standard_values_table (position_id, column_name, raw_value, standard_value) VALUES
(32, 'Subject Injured Prior To Incident', 'Yes',     'Yes'),
(32, 'Subject Injured Prior To Incident', 'No',      'No'),
(32, 'Subject Injured Prior To Incident', 'Unknown', 'Unknown');
