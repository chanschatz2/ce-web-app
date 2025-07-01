DROP TABLE IF EXISTS responses;
DROP TABLE IF EXISTS companies; -- legacy name for users
DROP TABLE IF EXISTS assessments;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id TEXT PRIMARY KEY,
    password TEXT
);

CREATE TABLE assessments (
    id SERIAL PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sector TEXT,
    industry TEXT,
    score NUMERIC
);

CREATE TABLE responses (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER REFERENCES assessments(id) ON DELETE CASCADE,
    year INTEGER,
    question_id TEXT,
    response TEXT,
    UNIQUE(assessment_id, year, question_id)
);