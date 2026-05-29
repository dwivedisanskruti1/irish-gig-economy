-- ============================================================
-- Irish Gig Economy Project — SQL Schema & Analytical Queries
-- ============================================================
-- Compatible with: MySQL 8+, PostgreSQL 14+, SQLite 3.35+
-- Data sources: CSO LFS, Revenue, WRC, Pobal
-- ============================================================


-- ============================================================
-- SCHEMA
-- ============================================================

CREATE TABLE IF NOT EXISTS counties (
    county_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    county_name     TEXT NOT NULL UNIQUE,
    deprivation_score   REAL,
    deprivation_category TEXT,
    urbanisation_rate   REAL,
    population_weight   REAL
);

CREATE TABLE IF NOT EXISTS lfs_employment (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    county          TEXT NOT NULL,
    year            INTEGER NOT NULL,
    age_band        TEXT NOT NULL,        -- '15-19','20-24','25-29','30-34'
    employed        INTEGER,
    unemployed      INTEGER,
    self_employed   INTEGER,
    employment_rate REAL,
    self_emp_rate   REAL,
    FOREIGN KEY (county) REFERENCES counties(county_name)
);

CREATE TABLE IF NOT EXISTS revenue_filings (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    county                      TEXT NOT NULL,
    year                        INTEGER NOT NULL,
    total_self_assessed_under30 INTEGER,
    estimated_platform_workers  INTEGER,
    platform_share_pct          REAL,
    median_platform_income_eur  INTEGER,
    top_platform                TEXT,
    FOREIGN KEY (county) REFERENCES counties(county_name)
);

CREATE TABLE IF NOT EXISTS wrc_cases (
    case_id         TEXT PRIMARY KEY,
    year            INTEGER NOT NULL,
    county          TEXT NOT NULL,
    sector          TEXT,
    platform        TEXT,
    claimant_age_band TEXT,
    outcome         TEXT,
    worker_won      INTEGER,   -- 1/0 boolean
    claim_type      TEXT,
    duration_weeks  INTEGER,
    FOREIGN KEY (county) REFERENCES counties(county_name)
);

CREATE TABLE IF NOT EXISTS county_master (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    county                      TEXT NOT NULL,
    year                        INTEGER NOT NULL,
    official_employed_u27       REAL,
    official_self_emp_u27       REAL,
    avg_employment_rate_u27     REAL,
    estimated_platform_workers  INTEGER,
    estimated_true_gig_workers  INTEGER,
    hidden_work_gap_pct         REAL,
    gap_score                   REAL,
    risk_category               TEXT,
    deprivation_score           REAL,
    urbanisation_rate           REAL,
    total_wrc_cases             INTEGER,
    worker_win_rate             REAL,
    FOREIGN KEY (county) REFERENCES counties(county_name)
);


-- ============================================================
-- ANALYTICAL QUERIES
-- ============================================================

-- Q1: Hidden Work Gap by county (most recent year)
-- Shows which counties have the highest proportion of under-27s
-- in work not captured by official ILO employment statistics.
-- -------------------------------------------------------
SELECT
    county,
    hidden_work_gap_pct,
    gap_score,
    risk_category,
    deprivation_score,
    urbanisation_rate,
    total_wrc_cases
FROM county_master
WHERE year = (SELECT MAX(year) FROM county_master)
ORDER BY hidden_work_gap_pct DESC;


-- Q2: National gig growth trend 2018–2025
-- Tracks how platform/gig work has grown year-on-year
-- as a share of official youth employment.
-- -------------------------------------------------------
SELECT
    year,
    SUM(estimated_true_gig_workers)        AS total_gig_workers,
    SUM(official_employed_u27)             AS total_official_employed,
    ROUND(
        SUM(estimated_true_gig_workers) * 100.0 /
        SUM(official_employed_u27), 2
    )                                      AS national_gap_pct,
    SUM(total_wrc_cases)                   AS total_wrc_cases
FROM county_master
GROUP BY year
ORDER BY year;


-- Q3: Deprivation vs gig work correlation
-- Does higher deprivation predict higher gig participation?
-- -------------------------------------------------------
SELECT
    county,
    deprivation_score,
    deprivation_category,
    AVG(hidden_work_gap_pct)   AS avg_gap_pct,
    AVG(worker_win_rate)       AS avg_wrc_win_rate
FROM county_master
GROUP BY county, deprivation_score, deprivation_category
ORDER BY deprivation_score DESC;


-- Q4: WRC cases — platform worker disputes by sector and outcome
-- Which sectors have the worst worker outcomes?
-- -------------------------------------------------------
SELECT
    sector,
    COUNT(*)                                        AS total_cases,
    SUM(worker_won)                                 AS worker_wins,
    ROUND(AVG(worker_won) * 100, 1)                 AS win_rate_pct,
    ROUND(AVG(duration_weeks), 1)                   AS avg_duration_weeks,
    COUNT(CASE WHEN claim_type='Misclassification'
               THEN 1 END)                          AS misclass_cases
FROM wrc_cases
GROUP BY sector
ORDER BY total_cases DESC;


-- Q5: Counties at highest risk post-EU Directive (Dec 2026)
-- Composite risk score = high gap + high deprivation + low win rate
-- -------------------------------------------------------
SELECT
    cm.county,
    cm.hidden_work_gap_pct,
    cm.deprivation_score,
    COALESCE(cm.worker_win_rate, 0)                 AS worker_win_rate,
    cm.risk_category,
    -- Composite vulnerability score (higher = more vulnerable)
    ROUND(
        (cm.hidden_work_gap_pct / 15.0 * 40) +
        (cm.deprivation_score / 40.0 * 40) +
        ((100 - COALESCE(cm.worker_win_rate, 50)) / 100.0 * 20),
    1)                                              AS vulnerability_score
FROM county_master cm
WHERE cm.year = (SELECT MAX(year) FROM county_master)
ORDER BY vulnerability_score DESC
LIMIT 10;
