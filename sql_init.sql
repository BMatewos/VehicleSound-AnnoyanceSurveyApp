--Create table queries

CREATE TABLE `mm_user` (
  `UserID` int NOT NULL,
  `Fname` varchar(50) NOT NULL,
  `Lname` varchar(50) NOT NULL,
  `email` varchar(50) NOT NULL,
  `role` varchar(50) NOT NULL,
  `password` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `CreatedTime` datetime NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `mm_experiment` (
  `ExperimentID` int NOT NULL,
  `ExperimentCode` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `StartDate` datetime NOT NULL,
  `EndDate` datetime NOT NULL,
  `Description` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `CreatedTime` datetime NOT NULL,
  `UpdatedDate` datetime DEFAULT NULL,
  `Creator_UserID` int NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `mm_media` (
  `MediaID` int NOT NULL,
  `FilePath` varchar(100) NOT NULL,
  `AutomobileType` varchar(50) NOT NULL,
  `Duration` float DEFAULT NULL,
  `CreatedTime` datetime NOT NULL,
  `ExperimentID` int NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `mm_question` (
  `QuestionID` int NOT NULL,
  `QuestionText` varchar(1000) NOT NULL,
  `QuestionType` varchar(50) NOT NULL,
  `CreatedTime` datetime NOT NULL,
  `ExperimentID` int NOT NULL,
  `MediaID` int NOT NULL,
  `Choices` text
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `mm_response` (
  `ResponseID` int NOT NULL,
  `Answer` text NOT NULL,
  `Duration` int NOT NULL,
  `ExperimentID` int NOT NULL,
  `QuestionID` int NOT NULL,
  `CreatedTime` datetime NOT NULL,
  `UserID` int NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Analytical queries

-- Experiments by participant
    
        SELECT e.ExperimentCode, e.Description, COUNT(r.ResponseID) AS total_responses
        FROM mm_response r
        JOIN mm_experiment e ON r.ExperimentID = e.ExperimentID
        GROUP BY e.ExperimentCode, e.Description
        ORDER BY total_responses DESC


-- Recent responses

        SELECT e.ExperimentCode, q.QuestionText, r.Answer, r.Duration, r.CreatedTime
        FROM mm_response r
        JOIN mm_experiment e ON r.ExperimentID = e.ExperimentID
        JOIN mm_question q ON r.QuestionID = q.QuestionID
        ORDER BY r.CreatedTime DESC
        LIMIT 10