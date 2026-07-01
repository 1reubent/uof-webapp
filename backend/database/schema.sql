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
  `Position_Id` smallint DEFAULT NULL,
  `Value_Id` int DEFAULT NULL,
  `Column_Value` text
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
  `Form_Id` int DEFAULT NULL,
  `Position_Id` smallint DEFAULT NULL,
  `Value_Id` int DEFAULT NULL,
  `Column_Value` text
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
  `Incident_Year` int DEFAULT NULL
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
  `Officer_Age` int DEFAULT NULL,
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
  `processed` TINYINT(1) NOT NULL DEFAULT 0 -- added for processing status by Reuben
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
-- Dump completed on 2026-06-18 17:29:24