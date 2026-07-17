-- =====================================================================
-- arrive_schema_addition.sql
-- Adds ARRIVE Together tables to the existing uof_project database.
-- Run this ONCE against your Aiven MySQL instance.
--
-- Usage (from MySQL Workbench, or via CLI):
--   mysql -u <user> -p -h <aiven-host> -P <port> uof_project < arrive_schema_addition.sql
-- =====================================================================

USE `uof_project`;

-- ─────────────────────────────────────────────────────────────────────
-- Table: arrive_main_data
-- One row per ARRIVE incident. Random_ID is a clean, unique key
-- already present in the source file — used directly as PRIMARY KEY.
-- Multi-value columns (originally Python list-literal strings, e.g.
-- "['Violence', 'Confused/disoriented persons']") are stored here as
-- plain comma-joined text for readability/display. For filtering on
-- individual selected values, see arrive_values_data below.
-- ─────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS `arrive_values_data`;   -- drop child first (FK)
DROP TABLE IF EXISTS `arrive_main_data`;

CREATE TABLE `arrive_main_data` (
  `Random_ID`                              INT NOT NULL,
  `Incident_Year`                          INT DEFAULT NULL,
  `Arrive_Model`                           TEXT,
  `Behaviors_Indicated_Prior_to_Arrival`    TEXT,
  `Other_Individuals_on_Scene`              TEXT,
  `Law_Enforcement_Observed_Behavior`        TEXT,
  `Law_Enforcement_Outcomes`                TEXT,
  `Outreach_Attempts`                       INT DEFAULT NULL,
  `Mental_Health_Outcome`                   TEXT,
  `Day_30_Outcomes`                         TEXT,
  PRIMARY KEY (`Random_ID`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE INDEX idx_arrive_year ON `arrive_main_data` (`Incident_Year`);

-- ─────────────────────────────────────────────────────────────────────
-- Table: arrive_values_data
-- One row per individually-selected value within a multi-value column.
-- Mirrors the existing uof_dashboard_values_data pattern in this
-- project, so multi-select fields (Behaviors_Indicated, Outcomes, etc.)
-- can actually be filtered on ("show me incidents where Violence was
-- one of the observed behaviors") rather than pattern-matched against
-- raw bracketed text.
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE `arrive_values_data` (
  `value_id`     INT NOT NULL AUTO_INCREMENT,
  `Random_ID`    INT NOT NULL,
  `column_name`  VARCHAR(64) NOT NULL,
  `column_value` TEXT NOT NULL,
  PRIMARY KEY (`value_id`),
  KEY `idx_arrive_values_random_id` (`Random_ID`),
  KEY `idx_arrive_values_column` (`column_name`(20)),
  CONSTRAINT `fk_arrive_values_random_id`
    FOREIGN KEY (`Random_ID`) REFERENCES `arrive_main_data` (`Random_ID`)
    ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

-- Done. Two new tables added: arrive_main_data, arrive_values_data.
-- Existing uof_* tables are untouched.
