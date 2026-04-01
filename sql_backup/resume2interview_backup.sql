BEGIN TRANSACTION;
CREATE TABLE interviews (
	id INTEGER NOT NULL, 
	feedback_level VARCHAR(50) NOT NULL, 
	score INTEGER NOT NULL, 
	summary TEXT NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);
INSERT INTO "interviews" VALUES(1,'Needs Improvement',20,'Interview completed. Score: 20/100 — Needs Improvement. Topics covered: Problem Solving, Behavioral, Technical.','2026-02-20 08:48:13.294307');
CREATE TABLE question_answers (
	id INTEGER NOT NULL, 
	interview_id INTEGER NOT NULL, 
	question TEXT NOT NULL, 
	answer TEXT NOT NULL, 
	category VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(interview_id) REFERENCES interviews (id) ON DELETE CASCADE
);
INSERT INTO "question_answers" VALUES(1,1,'Tell me about yourself','I am a software engineer with 3 years of experience building mobile and backend applications using Kotlin and Python.','Behavioral');
INSERT INTO "question_answers" VALUES(2,1,'What is your strongest skill?','Python','Technical');
INSERT INTO "question_answers" VALUES(3,1,'Describe a challenge you faced','I once had to migrate a live database with zero downtime by carefully planning a rolling migration strategy over several weekends.','Problem Solving');
CREATE TABLE skills (
	id INTEGER NOT NULL, 
	interview_id INTEGER NOT NULL, 
	skill_name VARCHAR(150) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(interview_id) REFERENCES interviews (id) ON DELETE CASCADE
);
INSERT INTO "skills" VALUES(1,1,'Problem Solving');
INSERT INTO "skills" VALUES(2,1,'Behavioral');
INSERT INTO "skills" VALUES(3,1,'Technical');
CREATE INDEX ix_interviews_id ON interviews (id);
CREATE INDEX ix_question_answers_id ON question_answers (id);
CREATE INDEX ix_skills_id ON skills (id);
COMMIT;