-- =============================================================================
-- seed_column_values.sql
-- Populates uof_column_values_data with the full set of valid individual values
-- for every multi-value column in the UoF dataset.
--
-- PURPOSE:
--   This is a static reference/lookup table. It catalogs every possible value
--   for each multi-value column. It is NOT used during cleaning directly, but
--   serves downstream users (dashboards, analysts, validation checks).
--
-- DESIGN DECISIONS DOCUMENTED:
--   - position_id = 1-based column position in the Excel source file.
--   - value_id = sequential integer within each column (no global uniqueness req).
--   - Values with embedded commas (e.g. 'Disturbance (drinking, fighting, disorderly)')
--     are hardcoded as single entries -- NOT split on comma.
--   - Trailing spaces stripped from all values per project decision.
--   - 'Used arms' and 'Used arms/hands' are separate standard values (not synonyms).
--   - Per-subject repeating columns (Subject Arrested, Subject Type, Subject Gender,
--     Subject Race/Ethnicity, Subject Injured In Incident, Subject Injured Prior)
--     are treated as multi-value columns. Their individual possible values are:
--     Subject Arrested        : 'True', 'False', 'Not Provided'
--     Subject Type            : 'Person', 'Animal', 'Unknown Subject(s)', 'Other', 'Not Provided'
--     Subject Gender          : 'Male', 'Female', 'Non-Binary/X', 'Not Provided'
--     Subject Race/Ethnicity  : (same set as Officer Race/Ethnicity)
--     Subject Injured In Incident     : 'Yes', 'No', 'Unknown'
--     Subject Injured Prior To Incident : 'Yes', 'No', 'Unknown'
--
-- USAGE:
--   Run once after creating the schema, before any data import.
--   Safe to re-run: table should be truncated and reloaded if values change.
-- =============================================================================

-- Truncate before reloading to avoid duplicates
TRUNCATE TABLE uof_column_values_data;

-- =============================================================================
-- COLUMN 10: Other Officer Involved
-- Single-value boolean column. Included here for completeness.
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(10, 1, 'True'),
(10, 2, 'False'),
(10, 3, 'Not Provided');

-- =============================================================================
-- COLUMN 13: Indoor Or Outdoor (position_id = 13)
-- Multi-value: officers can select both
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(13, 1, 'Indoors'),
(13, 2, 'Outdoors');

-- =============================================================================
-- COLUMN 14: Incident Weather (position_id = 14)
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(14, 1, 'Clear'),
(14, 2, 'Cloudy'),
(14, 3, 'Rain'),
(14, 4, 'Snow/Sleet/Ice'),
(14, 5, 'Fog'),
(14, 6, 'N/A'),
(14, 7, 'Not Provided');

-- =============================================================================
-- COLUMN 15: Video Footage (position_id = 15)
-- Single-value. Included for completeness.
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(15, 1, 'Yes'),
(15, 2, 'No'),
(15, 3, 'Unknown');

-- =============================================================================
-- COLUMN 16: Video Type (position_id = 16)
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(16, 1, 'Body Worn'),
(16, 2, 'Motor Vehicle'),
(16, 3, 'Station House'),
(16, 4, 'Cell Phone'),
(16, 5, 'Commercial Building'),
(16, 6, 'Residential/Home'),
(16, 7, 'CED Camera'),
(16, 8, 'Other'),
(16, 9, 'Unknown');

-- =============================================================================
-- COLUMN 17: Incident Lighting (position_id = 17)
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(17, 1, 'Daylight'),
(17, 2, 'Artificial'),
(17, 3, 'Dawn/Dusk'),
(17, 4, 'Darkness');

-- =============================================================================
-- COLUMN 18: Location Type (position_id = 18)
-- NOTE: 'Alcohol Establishment (bar, club, casino)' contains embedded commas.
-- Hardcoded as a single value.
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(18, 1,  'Street'),
(18, 2,  'Residence'),
(18, 3,  'Business'),
(18, 4,  'Hospital'),
(18, 5,  'School'),
(18, 6,  'Police Station'),
(18, 7,  'Jail/Prison'),
(18, 8,  'Court House'),
(18, 9,  'Restaurant'),
(18, 10, 'Alcohol Establishment (bar, club, casino)'),
(18, 11, 'Other');

-- =============================================================================
-- COLUMN 19: Incident Type (position_id = 19)
-- NOTE: 'Disturbance (drinking, fighting, disorderly)' contains embedded commas.
-- Hardcoded as a single value. 'Trespassing ' (trailing space) normalized to
-- 'Trespassing'.
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(19, 1,  'Welfare Check'),
(19, 2,  'Potential Mental Health Incident'),
(19, 3,  'Disturbance (drinking, fighting, disorderly)'),
(19, 4,  'Medical Emergency'),
(19, 5,  'Assault'),
(19, 6,  'Domestic'),
(19, 7,  'Suspicious person'),
(19, 8,  'Subject with other weapon'),
(19, 9,  'Subject with a gun'),
(19, 10, 'Eluding'),
(19, 11, 'MV/Traffic Stop'),
(19, 12, 'MV Accident/Aid'),
(19, 13, 'Wanted Person'),
(19, 14, 'Burglary'),
(19, 15, 'Robbery'),
(19, 16, 'Theft/Shoplifting'),
(19, 17, 'Trespassing'),
(19, 18, 'Terroristic Threats'),
(19, 19, 'Pedestrian Stop'),
(19, 20, 'Possession of CDS'),
(19, 21, 'Distribution of CDS'),
(19, 22, 'Report of Gunfire'),
(19, 23, 'Assisting another officer'),
(19, 24, 'Aggressive/Injured Animal'),
(19, 25, 'Other'),
(19, 26, 'Not Provided');

-- =============================================================================
-- COLUMN 20: Contact Origin (position_id = 20)
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(20, 1, 'Citizen Initiated'),
(20, 2, 'Officer Initiated'),
(20, 3, 'Dispatched'),
(20, 4, 'Officer Dispatched'),
(20, 5, 'Pre-Planned Contact'),
(20, 6, 'Not Provided');

-- =============================================================================
-- COLUMN 21: Planned Contact (position_id = 21)
-- NOTE: 'Judicial Order Service (TRO, FRO, etc.)' contains embedded commas.
-- Hardcoded as a single value. 'Other ' (trailing space) normalized to 'Other'.
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(21, 1, 'Arrest'),
(21, 2, 'Processing'),
(21, 3, 'Prisoner Transfer'),
(21, 4, 'Search Warrant Execution'),
(21, 5, 'No Knock Warrant'),
(21, 6, 'Judicial Order Service (TRO, FRO, etc.)'),
(21, 7, 'Other');

-- =============================================================================
-- COLUMN 27: Officer Injuries Injured (position_id = 27)
-- Single-value boolean. Included for completeness.
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(27, 1, 'True'),
(27, 2, 'False'),
(27, 3, 'Not Provided');

-- =============================================================================
-- COLUMN 28: Officer Medical Treatment (position_id = 28)
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(28, 1, 'EMS on scene'),
(28, 2, 'Hospital'),
(28, 3, 'Officer Administered First Aid'),
(28, 4, 'Urgent Care'),
(28, 5, 'Refused');

-- =============================================================================
-- COLUMN 31: Subject Injured In Incident (position_id = 31)
-- Per-subject repeating field. Individual possible values:
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(31, 1, 'Yes'),
(31, 2, 'No'),
(31, 3, 'Unknown');

-- =============================================================================
-- COLUMN 32: Subject Injured Prior To Incident (position_id = 32)
-- Per-subject repeating field.
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(32, 1, 'Yes'),
(32, 2, 'No'),
(32, 3, 'Unknown');

-- =============================================================================
-- COLUMN 33: Perceived Condition Of Subject (position_id = 33)
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(33, 1, 'Under influence of alcohol/drugs/both'),
(33, 2, 'Potential Mental Health Incident'),
(33, 3, 'No unusual condition noted'),
(33, 4, 'Other unusual condition noted'),
(33, 5, 'Not Provided');

-- =============================================================================
-- COLUMN 34: Subject Actions (position_id = 34)
-- NOTE: Several values contain embedded commas — hardcoded as single values:
--   'Attack with Hands,fists,legs'
--   'Threat with Hands,fists,legs'
--   'Threat to Strike with open hand, fist, or elbow'
--   'Strike with open hand, fist, or elbow'
-- 'Other Threat ' (trailing space) normalized to 'Other Threat'.
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(34, 1,  'Resisted arrest/police officer control'),
(34, 2,  'Verbal/Fighting stance Threat'),
(34, 3,  'Biting'),
(34, 4,  'Kick'),
(34, 5,  'Push or shove'),
(34, 6,  'Spitting'),
(34, 7,  'Attempt to escape from Custody'),
(34, 8,  'Attempt to self-harm'),
(34, 9,  'Fired Gun'),
(34, 10, 'Attack with Hands,fists,legs'),            -- embedded comma: hardcoded
(34, 11, 'Attack with Blunt object'),
(34, 12, 'Attack with Edge Weapon'),
(34, 13, 'Attack with Other Weapon'),
(34, 14, 'Attack with Motor Vehicle'),
(34, 15, 'Attack with Bodily fluids'),
(34, 16, 'Threat with Gun'),
(34, 17, 'Threat with Hands'),
(34, 18, 'Threat with Hands,fists,legs'),            -- embedded comma: hardcoded
(34, 19, 'Threat with Blunt object'),
(34, 20, 'Threat with Edge Weapon'),
(34, 21, 'Threat with Other Weapon'),
(34, 22, 'Threat with Motor vehicle'),
(34, 23, 'Threat with Bodily Fluids'),
(34, 24, 'Threat to Strike with open hand, fist, or elbow'),  -- embedded comma: hardcoded
(34, 25, 'Strike with open hand, fist, or elbow'),            -- embedded comma: hardcoded
(34, 26, 'Threat to Kick'),
(34, 27, 'Threat to Push or shove'),
(34, 28, 'Attempt to commit crime'),
(34, 29, 'Attempt to destroy evidence'),
(34, 30, 'Prevent harm to another'),
(34, 31, 'Failure to Disperse'),
(34, 32, 'Other Attack'),
(34, 33, 'Other Threat'),
(34, 34, 'Not Provided');

-- =============================================================================
-- COLUMN 35: Subject Resistance (position_id = 35)
-- NOTE: 'Resistive tension (stiffening, tighening muscles)' contains an
-- embedded comma. Hardcoded as a single value.
-- 'Attempt to flee ' (trailing space) normalized to 'Attempt to flee'.
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(35, 1,  'Passive Resistor'),
(35, 2,  'Active Resistor'),
(35, 3,  'Resistive tension (stiffening, tighening muscles)'),  -- embedded comma: hardcoded
(35, 4,  'Attempt to flee'),
(35, 5,  'Dead-weight tactics (going limp)'),
(35, 6,  'Verbal'),
(35, 7,  'Aggressive resistance (attempt to attack or harm)'),
(35, 8,  'Active Assailant'),
(35, 9,  'Threatening Assailant'),
(35, 10, 'Non-response (consciously ignoring)'),
(35, 11, 'Other'),
(35, 12, 'Not Provided');

-- =============================================================================
-- COLUMN 36: Subject Medical Treatment (position_id = 36)
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(36, 1, 'EMS on scene'),
(36, 2, 'Hospital'),
(36, 3, 'Officer Administered First Aid'),
(36, 4, 'Urgent Care'),
(36, 5, 'Refused'),
(36, 6, 'Mental Health Facility'),
(36, 7, 'Unknown');

-- =============================================================================
-- COLUMN 37: Subject Injury Type (position_id = 37)
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(37, 1,  'Abrasion/Laceration/Puncture'),
(37, 2,  'Contusion/bruise'),
(37, 3,  'Complaint of pain'),
(37, 4,  'Chest pains/shortness of breath'),
(37, 5,  'Fracture/dislocation'),
(37, 6,  'Concussion'),
(37, 7,  'Gunshot wound'),
(37, 8,  'Other'),
(37, 9,  'Unknown'),
(37, 10, 'Not Provided');

-- =============================================================================
-- COLUMN 38: Subject Arrested (position_id = 38)
-- Per-subject repeating field.
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(38, 1, 'True'),
(38, 2, 'False'),
(38, 3, 'Not Provided');

-- =============================================================================
-- COLUMN 39: Reason Not Arrested (position_id = 39)
-- Multi-value: GROUP BY on uof_main_data showed comma-joined values (e.g.
-- 'Already in Custody, Medical/Mental Health Incident'), so this was missing
-- from the seed even though it needs the same tokenization as the other
-- multi-value columns. NULL (not comma-joined) rows are subjects who were
-- arrested, so no 'Not Provided'/'N/A' token is needed here.
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(39, 1, 'Already in Custody'),
(39, 2, 'Deceased'),
(39, 3, 'Insufficient Probable Cause-includes continuing investigation'),
(39, 4, 'Medical/Mental Health Incident'),
(39, 5, 'No Probable Cause- Crime Unfounded'),
(39, 6, 'No Probable Cause- Subject Not Involved'),
(39, 7, 'Other'),
(39, 8, 'Subject Fled');

-- =============================================================================
-- COLUMN 40: Subject Type (position_id = 40)
-- Per-subject repeating field.
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(40, 1, 'Person'),
(40, 2, 'Animal'),
(40, 3, 'Unknown Subject(s)'),
(40, 4, 'Other'),
(40, 5, 'Not Provided');

-- =============================================================================
-- COLUMN 42: Subject Race/Ethnicity (position_id = 42)
-- Per-subject repeating field. Same value set as Officer Race/Ethnicity.
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(42, 1, 'White'),
(42, 2, 'Black or African American'),
(42, 3, 'Hispanic'),
(42, 4, 'Asian'),
(42, 5, 'American Indian'),
(42, 6, 'Native Hawaiian or other Pacific Islander'),
(42, 7, 'Two or more races'),
(42, 8, 'Other'),
(42, 9, 'Not Provided');

-- =============================================================================
-- COLUMN 43: Subject Gender (position_id = 43)
-- Per-subject repeating field.
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(43, 1, 'Male'),
(43, 2, 'Female'),
(43, 3, 'Non-Binary/X'),
(43, 4, 'Not Provided');

-- =============================================================================
-- COLUMN 44: Force Type (position_id = 44)
-- NOTE: 'Used arms' and 'Used arms/hands' are DISTINCT values per project decision.
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(44, 1,  'Used arms/hands'),
(44, 2,  'Used arms'),
(44, 3,  'Used take down on'),
(44, 4,  'Used arm bar on'),
(44, 5,  'Used pressure points on'),
(44, 6,  'Used legs/kicks'),
(44, 7,  'Used fists/punch'),
(44, 8,  'Used head'),
(44, 9,  'Used CED on'),
(44, 10, 'CED Spark Display'),
(44, 11, 'Used Less-lethal device on'),
(44, 12, 'Pointing Firearm'),
(44, 13, 'Discharged Firearm at'),
(44, 14, 'Discharged Chemical at'),
(44, 15, 'High Volume OC Spray'),
(44, 16, 'CS Gas'),
(44, 17, 'Canine bit (apprehension)'),
(44, 18, 'Canine bit (spontaneous)'),
(44, 19, 'Compliance hold with impact weapon- not a strike'),
(44, 20, 'Struck'),
(44, 21, 'Back'),
(44, 22, 'Back for prolonged period'),
(44, 23, 'Kneeling on Chest'),
(44, 24, 'Carotid artery restraint'),
(44, 25, 'Chokehold'),
(44, 26, 'Intent to strike with a motor vehicle'),
(44, 27, 'Other'),
(44, 28, 'Not Provided');

-- =============================================================================
-- COLUMN 26: Officer Injury Type (position_id = 26)
-- Includes 'Not injured' as a valid value (distinct from Subject Injury Type).
-- =============================================================================
INSERT INTO uof_column_values_data (Position_Id, Value_Id, Column_Value) VALUES
(26, 1,  'Not injured'),
(26, 2,  'Abrasion/Laceration/Puncture'),
(26, 3,  'Contusion/bruise'),
(26, 4,  'Complaint of pain'),
(26, 5,  'Chest pains/shortness of breath'),
(26, 6,  'Fracture/dislocation'),
(26, 7,  'Concussion'),
(26, 8,  'Gunshot wound'),
(26, 9,  'Other'),
(26, 10, 'Unknown');
