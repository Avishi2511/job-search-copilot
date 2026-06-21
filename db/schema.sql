-- Run this once to initialize the database schema.
-- psql -U postgres -d job_copilot -f db/schema.sql

CREATE TABLE IF NOT EXISTS seen_jobs (
    id            SERIAL PRIMARY KEY,
    dedup_key     TEXT NOT NULL UNIQUE,   -- "{company}::{title}" normalized to lowercase
    company       TEXT NOT NULL,
    title         TEXT NOT NULL,
    source        TEXT NOT NULL,          -- "adzuna" | "remotive"
    url           TEXT,
    date_seen     DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE INDEX IF NOT EXISTS idx_seen_jobs_dedup_key ON seen_jobs (dedup_key);
CREATE INDEX IF NOT EXISTS idx_seen_jobs_date_seen  ON seen_jobs (date_seen);
