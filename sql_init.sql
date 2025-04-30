--Create table queries

CREATE TABLE mm_user (
    UserID INT AUTO_INCREMENT PRIMARY KEY, Fname VARCHAR(50) NOT NULL,
    Lname VARCHAR(50) NOT NULL,   email VARCHAR(50) NOT NULL,
    role VARCHAR(50) NOT NULL, password VARCHAR(100) NOT NULL,
   CreatedTime DATETIME NOT NULL) ENGINE=MyISAM;

CREATE TABLE mm_experiment (
    ExperimentID INT AUTO_INCREMENT PRIMARY KEY,  ExperimentName VARCHAR(100) NOT NULL,
    StartDate DATETIME NOT NULL, EndDate DATETIME NOT NULL,
    Description VARCHAR(100) NOT NULL, CreatedTime DATETIME NOT NULL,
    UpdatedDate DATETIME NULL) ENGINE=MyISAM;

CREATE TABLE mm_media (
    MediaID INT AUTO_INCREMENT PRIMARY KEY, FilePath VARCHAR(100) NOT NULL,
    AutomobileType VARCHAR(50) NOT NULL,  Duration FLOAT NOT NULL,
    CreatedTime DATETIME NOT NULL,  ExperimentID INT NOT NULL,
    FOREIGN KEY (ExperimentID) REFERENCES mm_experiment(ExperimentID)) ENGINE=MyISAM;

CREATE TABLE mm_question (
    QuestionID INT AUTO_INCREMENT PRIMARY KEY,  QuestionText VARCHAR(1000) NOT NULL,
    QuestionType VARCHAR(50) NOT NULL,   CreatedTime DATETIME NOT NULL,
    ExperimentID INT NOT NULL,    MediaID INT NOT NULL,
    FOREIGN KEY (ExperimentID) REFERENCES mm_experiment(ExperimentID),
    FOREIGN KEY (MediaID) REFERENCES mm_media(MediaID)) ENGINE=MyISAM;

CREATE TABLE mm_response (
    ResponseID INT AUTO_INCREMENT PRIMARY KEY,  Value INT NOT NULL,
    VehicleGuess VARCHAR(50) NOT NULL,    CorrectGuess CHAR(1) NOT NULL,
    CreatedTime DATETIME NOT NULL,    Duration DATETIME NOT NULL,
    UserID INT NOT NULL,    QuestionID INT NOT NULL,    FOREIGN KEY (UserID) REFERENCES mm_user(UserID),
    FOREIGN KEY (QuestionID) REFERENCES mm_question(QuestionID)) ENGINE=MyISAM;

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