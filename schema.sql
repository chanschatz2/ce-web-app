DROP TABLE IF EXISTS responses;
DROP TABLE IF EXISTS companies;

CREATE TABLE companies (
    id TEXT PRIMARY KEY,
    sector TEXT,
    password TEXT
);

CREATE TABLE responses (
    id SERIAL PRIMARY KEY,
    company_id TEXT REFERENCES companies(id),
    year INTEGER,
    question_id TEXT,
    response TEXT,
    UNIQUE(company_id, year, question_id)
);