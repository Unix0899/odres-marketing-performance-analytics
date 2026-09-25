-- =====================================================================
-- 01_schema.sql — ODRES Marketing & Commercial Performance (SQLite)
-- Professional context based on a real ODRES Group experience.
-- Public technical reconstruction using synthetic data.
--
-- Star schema: 5 dimensions + 4 fact tables.
-- Business rules are enforced as CHECK constraints so that bad data
-- cannot be loaded silently (the clean layer must respect them).
-- =====================================================================
PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- dimensions
CREATE TABLE dim_date (
    date_key     INTEGER PRIMARY KEY,          -- YYYYMMDD
    date         TEXT    NOT NULL UNIQUE,
    year         INTEGER NOT NULL,
    quarter      TEXT    NOT NULL,
    month        INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    month_name   TEXT    NOT NULL,
    year_month   TEXT    NOT NULL,             -- YYYY-MM, used for monthly reporting
    week         INTEGER NOT NULL,
    day_of_week  TEXT    NOT NULL,
    is_weekend   INTEGER NOT NULL CHECK (is_weekend IN (0, 1))
);

CREATE TABLE dim_channel (
    channel_id    INTEGER PRIMARY KEY,
    channel_name  TEXT    NOT NULL UNIQUE,
    channel_group TEXT    NOT NULL,            -- Paid Search, Paid Social, Organic, Direct, Owned, Referral
    is_paid       INTEGER NOT NULL CHECK (is_paid IN (0, 1))
);

CREATE TABLE dim_campaign (
    campaign_id   INTEGER PRIMARY KEY,
    campaign_name TEXT    NOT NULL UNIQUE,
    channel_id    INTEGER NOT NULL REFERENCES dim_channel(channel_id),
    objective     TEXT    NOT NULL,
    start_date    TEXT    NOT NULL
);

CREATE TABLE dim_region (
    region_id     INTEGER PRIMARY KEY,
    region_name   TEXT    NOT NULL UNIQUE,
    region_group  TEXT    NOT NULL             -- Brussels-Capital, Flanders, Wallonia
);

CREATE TABLE dim_customer (
    customer_id          INTEGER PRIMARY KEY,
    opportunity_id       INTEGER NOT NULL UNIQUE REFERENCES fact_opportunities(opportunity_id),
    lead_id              INTEGER NOT NULL REFERENCES fact_leads(lead_id),
    acquisition_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    channel_id           INTEGER NOT NULL REFERENCES dim_channel(channel_id),
    campaign_id          INTEGER          REFERENCES dim_campaign(campaign_id),
    region_id            INTEGER NOT NULL REFERENCES dim_region(region_id),
    company_size         TEXT    NOT NULL CHECK (company_size IN ('1-9', '10-49', '50+')),
    business_type        TEXT    NOT NULL,
    plan                 TEXT    NOT NULL CHECK (plan IN ('Starter', 'Pro', 'Group')),
    starting_mrr         REAL    NOT NULL CHECK (starting_mrr > 0)
);

-- ---------------------------------------------------------------- facts
-- Grain: one row per campaign per day
CREATE TABLE fact_marketing_daily (
    date_key     INTEGER NOT NULL REFERENCES dim_date(date_key),
    campaign_id  INTEGER NOT NULL REFERENCES dim_campaign(campaign_id),
    channel_id   INTEGER NOT NULL REFERENCES dim_channel(channel_id),
    impressions  INTEGER NOT NULL CHECK (impressions >= 0),
    clicks       INTEGER NOT NULL CHECK (clicks >= 0),
    sessions     INTEGER NOT NULL CHECK (sessions >= 0),
    spend        REAL    NOT NULL CHECK (spend >= 0),
    PRIMARY KEY (date_key, campaign_id),
    CHECK (clicks <= impressions)
);

-- Grain: one row per lead (CRM)
CREATE TABLE fact_leads (
    lead_id          INTEGER PRIMARY KEY,
    created_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    channel_id       INTEGER NOT NULL REFERENCES dim_channel(channel_id),
    campaign_id      INTEGER          REFERENCES dim_campaign(campaign_id),   -- NULL = unassigned campaign
    region_id        INTEGER NOT NULL REFERENCES dim_region(region_id),
    company_size     TEXT    NOT NULL CHECK (company_size IN ('1-9', '10-49', '50+')),
    business_type    TEXT    NOT NULL,
    lead_score       INTEGER CHECK (lead_score BETWEEN 0 AND 100),            -- NULL = unknown
    is_mql           INTEGER NOT NULL CHECK (is_mql IN (0, 1)),
    is_sql           INTEGER NOT NULL CHECK (is_sql IN (0, 1)),
    CHECK (is_sql <= is_mql)                                                  -- SQL implies MQL
);

-- Grain: one row per sales opportunity
CREATE TABLE fact_opportunities (
    opportunity_id   INTEGER PRIMARY KEY,
    lead_id          INTEGER NOT NULL REFERENCES fact_leads(lead_id),
    created_date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    close_date_key   INTEGER          REFERENCES dim_date(date_key),         -- NULL = open or unknown
    channel_id       INTEGER NOT NULL REFERENCES dim_channel(channel_id),
    campaign_id      INTEGER          REFERENCES dim_campaign(campaign_id),
    region_id        INTEGER NOT NULL REFERENCES dim_region(region_id),
    company_size     TEXT    NOT NULL,
    plan             TEXT    NOT NULL CHECK (plan IN ('Starter', 'Pro', 'Group')),
    sites            INTEGER NOT NULL CHECK (sites >= 1),
    status           TEXT    NOT NULL CHECK (status IN ('Won', 'Lost', 'Open')),
    is_won           INTEGER NOT NULL CHECK (is_won IN (0, 1)),
    expected_value   REAL    NOT NULL CHECK (expected_value > 0),            -- first-year contract value (EUR)
    won_value        REAL    NOT NULL CHECK (won_value >= 0),
    sales_cycle_days INTEGER CHECK (sales_cycle_days >= 0),
    value_imputed    INTEGER NOT NULL DEFAULT 0 CHECK (value_imputed IN (0, 1)),
    CHECK (status <> 'Won' OR won_value > 0)                                  -- a Won deal has a value
);

-- Grain: one row per customer per month
CREATE TABLE fact_customer_monthly (
    customer_id  INTEGER NOT NULL REFERENCES dim_customer(customer_id),
    year_month   TEXT    NOT NULL,
    month_key    INTEGER NOT NULL REFERENCES dim_date(date_key),              -- first day of the month
    mrr          REAL    NOT NULL CHECK (mrr >= 0),
    is_active    INTEGER NOT NULL CHECK (is_active IN (0, 1)),
    is_churned   INTEGER NOT NULL CHECK (is_churned IN (0, 1)),
    PRIMARY KEY (customer_id, year_month)
);

-- ---------------------------------------------------------------- indexes
CREATE INDEX idx_mkt_channel    ON fact_marketing_daily(channel_id);
CREATE INDEX idx_leads_date     ON fact_leads(created_date_key);
CREATE INDEX idx_leads_channel  ON fact_leads(channel_id);
CREATE INDEX idx_leads_campaign ON fact_leads(campaign_id);
CREATE INDEX idx_opps_lead      ON fact_opportunities(lead_id);
CREATE INDEX idx_opps_channel   ON fact_opportunities(channel_id);
CREATE INDEX idx_opps_status    ON fact_opportunities(status);
CREATE INDEX idx_cm_month       ON fact_customer_monthly(year_month);
