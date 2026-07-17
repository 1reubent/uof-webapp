CREATE DATABASE IF NOT EXISTS `uof_project`
/*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */
/*!80016 DEFAULT ENCRYPTION='N' */
;

USE `uof_project`;

-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: localhost    Database: uof_project
-- ------------------------------------------------------
-- Server version	8.0.46
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */
;

/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */
;

/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */
;

/*!50503 SET NAMES utf8 */
;

/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */
;

/*!40103 SET TIME_ZONE='+00:00' */
;

/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */
;

/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */
;

/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */
;

/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */
;

--
-- Table structure for table `exceptions_table`
--
DROP TABLE IF EXISTS `exceptions_table`;

/*!40101 SET @saved_cs_client     = @@character_set_client */
;

/*!50503 SET character_set_client = utf8mb4 */
;

CREATE TABLE `exceptions_table` (
  `exception_id` int NOT NULL AUTO_INCREMENT,
  `form_id` text,
  `position_id` smallint DEFAULT NULL,
  `column_name` text,
  `original_value` text,
  `reason` text,
  PRIMARY KEY (`exception_id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

/*!40101 SET character_set_client = @saved_cs_client */
;

--
-- Table structure for table `standard_values_table`
--
DROP TABLE IF EXISTS `standard_values_table`;

/*!40101 SET @saved_cs_client     = @@character_set_client */
;

/*!50503 SET character_set_client = utf8mb4 */
;

CREATE TABLE standard_values_table (
  `standard_value_id` INT NOT NULL AUTO_INCREMENT,
  `position_id` SMALLINT DEFAULT NULL,
  `column_name` VARCHAR(64) NOT NULL,
  -- e.g. 'officer_rank'
  `raw_value` VARCHAR(255) NOT NULL,
  -- added by Reuben
  -- exactly as it appears in the source
  `standard_value` TEXT NOT NULL,
  -- the standardized form
  PRIMARY KEY (standard_value_id),
  UNIQUE KEY uq_column_raw (column_name, raw_value)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

/*!40101 SET character_set_client = @saved_cs_client */
;

--
-- Table structure for table `uof_column_values_data`
--
DROP TABLE IF EXISTS `uof_column_values_data`;

/*!40101 SET @saved_cs_client     = @@character_set_client */
;

/*!50503 SET character_set_client = utf8mb4 */
;

CREATE TABLE `uof_column_values_data` (
  `id` int NOT NULL AUTO_INCREMENT, -- surrogate PK added for Aiven (requires PK on all tables)
  `Position_Id` smallint DEFAULT NULL,
  `Value_Id` int DEFAULT NULL,
  `Column_Value` text,
  PRIMARY KEY (`id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

/*!40101 SET character_set_client = @saved_cs_client */
;

--
-- Table structure for table `uof_dashboard_values_data`
--
DROP TABLE IF EXISTS `uof_dashboard_values_data`;

/*!40101 SET @saved_cs_client     = @@character_set_client */
;

/*!50503 SET character_set_client = utf8mb4 */
;

CREATE TABLE `uof_dashboard_values_data` (
  `id` int NOT NULL AUTO_INCREMENT, -- surrogate PK added for Aiven (requires PK on all tables)
  `Form_Id` int DEFAULT NULL,
  `Position_Id` smallint DEFAULT NULL,
  `Value_Id` int DEFAULT NULL,
  `Column_Value` text,
  PRIMARY KEY (`id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

/*!40101 SET character_set_client = @saved_cs_client */
;

--
-- Table structure for table `uof_main_data`
--
DROP TABLE IF EXISTS `uof_main_data`;

/*!40101 SET @saved_cs_client     = @@character_set_client */
;

/*!50503 SET character_set_client = utf8mb4 */
;

CREATE TABLE `uof_main_data` (
  `id` int NOT NULL AUTO_INCREMENT, -- surrogate PK added for Aiven (requires PK on all tables)
  `Form_ID` int DEFAULT NULL,
  `County` text,
  `Agency_Name` text,
  `Officer_Name` text,
  `User_ID` int DEFAULT NULL,
  `Incident_ID` text,
  `Report_Number` text,
  `Incident_Case` text,
  `Incident_Date` date DEFAULT NULL,
  `Other_Officer_Involved` tinyint(1) DEFAULT NULL,
  `Officer_In_Uniform` tinyint(1) DEFAULT NULL,
  `Incident_Municipality` text,
  `Indoor_Or_Outdoor` text,
  `Incident_Weather` text,
  `Video_Footage` text,
  `Video_Type` text,
  `Incident_Lighting` text,
  `Location_Type` text,
  `Incident_Type` text,
  `Contact_Origin` text,
  `Planned_Contact` text,
  `Officer_Age` int DEFAULT NULL,
  `Officer_Race/Ethnicity` text,
  `Officer_Rank` text,
  `Officer_Gender` text,
  `Officer_Injury_Type` text,
  `Officer_Injuries_Injured` tinyint(1) DEFAULT NULL,
  `Officer_Medical_Treatment` text,
  `Officer_Hospital_Treatment` text,
  `Total_Sub_Injured` int DEFAULT NULL,
  `Subject_Injured` text,
  `Subject_Injured_Prior` text,
  `Perceived_Condition` text,
  `Subject_Actions` text,
  `Subject_Resistance` text,
  `Subject_Medical Treatment` text,
  `Subject_Injury Type` text,
  `Subject_Arrested` text DEFAULT NULL,
  -- changed from tinyint(1) to text by Reuben
  `Reason_Not_Arrested` text,
  `Subject_Type` text,
  `Subject_Age` text DEFAULT NULL,
  -- changed from int to text by Reuben
  `Subject_Race/Ethnicity` text,
  `Subject_Gender` text,
  `Force_Type` text,
  `Incident_Year` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

/*!40101 SET character_set_client = @saved_cs_client */
;

--
-- Table structure for table `uof_main_processing_table`
--
DROP TABLE IF EXISTS `uof_main_processing_table`;

/*!40101 SET @saved_cs_client     = @@character_set_client */
;

/*!50503 SET character_set_client = utf8mb4 */
;

CREATE TABLE `uof_main_processing_table` (
  `id` int NOT NULL AUTO_INCREMENT, -- surrogate PK added for Aiven (requires PK on all tables)
  `Form_ID` int DEFAULT NULL,
  `County` text,
  `Agency_Name` text,
  `Officer_Name` text,
  `User_ID` int DEFAULT NULL,
  `Incident_ID` text,
  `Report_Number` text,
  `Incident_Case` text,
  `Incident_Date` date DEFAULT NULL,
  `Other_Officer_Involved` text,
  `Officer_In_Uniform` tinyint(1) DEFAULT NULL,
  -- changed from text to tinyint(1) by Reuben
  `Incident_Municipality` text,
  `Indoor_Or_Outdoor` text,
  `Incident_Weather` text,
  `Video_Footage` text,
  `Video_Type` text,
  `Incident_Lighting` text,
  `Location_Type` text,
  `Incident_Type` text,
  `Contact_Origin` text,
  `Planned_Contact` text,
  `Officer_Age` text DEFAULT NULL,
  -- changed from int to text by Reuben; source data has non-numeric entries
  -- (e.g. "24 years old", "Twenty-nine"), cleaned/validated downstream
  `Officer_Race/Ethnicity` text,
  `Officer_Rank` text,
  `Officer_Gender` text,
  `Officer_Injury_Type` text,
  `Officer_Injuries_Injured` text,
  `Officer_Medical_Treatment` text,
  `Officer_Hospital_Treatment` text,
  `Total_Sub_Injured` int DEFAULT NULL,
  `Subject_Injured` text,
  `Subject_Injured_Prior` text,
  `Perceived_Condition` text,
  `Subject_Actions` text,
  `Subject_Resistance` text,
  `Subject_Medical Treatment` text,
  `Subject_Injury Type` text,
  `Subject_Arrested` text,
  `Reason_Not_Arrested` text,
  `Subject_Type` text,
  `Subject_Age` text DEFAULT NULL,
  -- changed from int to text by Reuben
  `Subject_Race/Ethnicity` text,
  `Subject_Gender` text,
  `Force_Type` text,
  `Incident_Year` int DEFAULT NULL,
  `processed` TINYINT(1) NOT NULL DEFAULT 0, -- added for processing status by Reuben
  PRIMARY KEY (`id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

/*!40101 SET character_set_client = @saved_cs_client */
;

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */
;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */
;

/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */
;

/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */
;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */
;

/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */
;

/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */
;

/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */
;

CREATE INDEX idx_form_id ON uof_main_processing_table (Form_ID);

CREATE INDEX idx_processed ON uof_main_processing_table(processed);

-- indices added by Reuben

-- uof_main_data / uof_main_processing_table
-- Both tables share the same query pattern: the frontend query builder requires
-- either an Incident_Date range or one or more Incident_ID values before a query
-- can run at all (the "launch gate"), so those two columns are hit on every query.
-- County, Agency_Name, Incident_Type, and Force_Type are the next most commonly
-- filtered fields (the "Geography & agency" and "Incident & force" groups, shown
-- first/near-top in the query builder), and Incident_Year is a common range filter
-- for year-over-year analysis. Text columns need a prefix length since MySQL
-- can't index a full TEXT column.
CREATE INDEX idx_main_data_incident_date ON uof_main_data (Incident_Date);
CREATE INDEX idx_main_data_incident_id ON uof_main_data (Incident_ID(191));
CREATE INDEX idx_main_data_county ON uof_main_data (County(191));
CREATE INDEX idx_main_data_agency_name ON uof_main_data (Agency_Name(191));
CREATE INDEX idx_main_data_incident_type ON uof_main_data (Incident_Type(191));
CREATE INDEX idx_main_data_force_type ON uof_main_data (Force_Type(191));
CREATE INDEX idx_main_data_incident_year ON uof_main_data (Incident_Year);

-- Incident_Municipality is scanned by bridge.py's /filter-values endpoint
-- (SELECT DISTINCT ... for the autocomplete suggestion list), which was a
-- full table scan across 105k+ rows without this. Only added on uof_main_data
-- (not uof_main_processing_table) since that's the only table /filter-values
-- queries -- unlike the columns above, this one isn't filtered anywhere
-- against uof_main_processing_table.
CREATE INDEX idx_main_data_incident_municipality ON uof_main_data (Incident_Municipality(191));

CREATE INDEX idx_processing_incident_date ON uof_main_processing_table (Incident_Date);
CREATE INDEX idx_processing_incident_id ON uof_main_processing_table (Incident_ID(191));
CREATE INDEX idx_processing_county ON uof_main_processing_table (County(191));
CREATE INDEX idx_processing_agency_name ON uof_main_processing_table (Agency_Name(191));
CREATE INDEX idx_processing_incident_type ON uof_main_processing_table (Incident_Type(191));
CREATE INDEX idx_processing_force_type ON uof_main_processing_table (Force_Type(191));
CREATE INDEX idx_processing_incident_year ON uof_main_processing_table (Incident_Year);

-- uof_dashboard_values_data
-- This is an EAV-style table: Form_Id ties a row back to a specific incident in
-- uof_main_data, and (Position_Id, Value_Id) is how a row's raw value gets decoded
-- against uof_column_values_data. Both access paths are joins, not full scans, so
-- they need to be indexed.
CREATE INDEX idx_dashboard_form_id ON uof_dashboard_values_data (Form_Id);
CREATE INDEX idx_dashboard_pos_val ON uof_dashboard_values_data (Position_Id, Value_Id);

-- uof_column_values_data
-- This is the value dictionary that uof_dashboard_values_data joins against via
-- (Position_Id, Value_Id) to resolve a stored value ID into its display value.
CREATE INDEX idx_column_values_pos_val ON uof_column_values_data (Position_Id, Value_Id);

-- standard_values_table
-- No new index needed here: the existing UNIQUE KEY uq_column_raw (column_name, raw_value)
-- already creates a composite index on (column_name, raw_value) as a side effect of
-- enforcing uniqueness, and that's the same lookup pattern the ETL standardization
-- step uses (look up a raw value within a given column).

-- exceptions_table
-- Not queried by the current frontend, but exceptions are logged per source record,
-- so form_id is the natural lookup key for a future "review exceptions for this
-- incident" admin view. TEXT column, so it needs a prefix length.
CREATE INDEX idx_exceptions_form_id ON exceptions_table (form_id(191));

-- Dump completed on 2026-06-18 17:29:24