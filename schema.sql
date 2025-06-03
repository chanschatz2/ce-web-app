CREATE TABLE companies (
    id TEXT PRIMARY KEY,
    sector TEXT
);

CREATE TABLE responses (
    id SERIAL PRIMARY KEY,
    company_id TEXT REFERENCES companies(id),
    year INTEGER,
    question_id TEXT,
    response TEXT,
    UNIQUE(company_id, year, question_id)
);