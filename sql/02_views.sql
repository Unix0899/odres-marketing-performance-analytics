-- =====================================================================
-- 02_views.sql — reusable reporting views (semantic layer)
-- Synthetic data. Attribution rule: revenue is attributed to the lead's
-- source channel / campaign (first-touch, as recorded in the CRM).
-- Ratios use NULLIF(...) so that "not applicable" stays NULL, never 0
-- (e.g. CAC of a channel with no paid spend).
-- =====================================================================

-- ---------------------------------------------------------------------
-- vw_lead_outcomes: one row per lead with what happened downstream.
-- Base for every funnel calculation (avoids repeating the same joins).
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS vw_lead_outcomes;
CREATE VIEW vw_lead_outcomes AS
WITH opp AS (                                   -- at most one row per lead
    SELECT lead_id,
           COUNT(*)                                   AS opportunities,
           MAX(is_won)                                AS is_customer,
           SUM(CASE WHEN is_won = 1 THEN won_value ELSE 0 END) AS won_value,
           AVG(CASE WHEN is_won = 1 THEN sales_cycle_days END) AS won_cycle_days
    FROM fact_opportunities
    GROUP BY lead_id
)
SELECT l.lead_id,
       l.created_date_key,
       d.year_month,
       l.channel_id,
       l.campaign_id,
       l.region_id,
       l.company_size,
       l.business_type,
       l.lead_score,
       l.is_mql,
       l.is_sql,
       CASE WHEN o.opportunities > 0 THEN 1 ELSE 0 END AS has_opportunity,
       COALESCE(o.is_customer, 0)                      AS is_customer,
       COALESCE(o.won_value, 0)                        AS won_value,
       o.won_cycle_days
FROM fact_leads l
JOIN dim_date d ON d.date_key = l.created_date_key
LEFT JOIN opp o ON o.lead_id = l.lead_id;

-- ---------------------------------------------------------------------
-- vw_channel_performance: full funnel + efficiency per acquisition channel
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS vw_channel_performance;
CREATE VIEW vw_channel_performance AS
WITH mkt AS (
    SELECT channel_id,
           SUM(impressions) AS impressions,
           SUM(clicks)      AS clicks,
           SUM(sessions)    AS sessions,
           SUM(spend)       AS spend
    FROM fact_marketing_daily
    GROUP BY channel_id
),
funnel AS (
    SELECT channel_id,
           COUNT(*)              AS leads,
           SUM(is_mql)           AS mqls,
           SUM(is_sql)           AS sqls,
           SUM(has_opportunity)  AS opportunities,
           SUM(is_customer)      AS customers,
           SUM(won_value)        AS won_revenue,
           AVG(lead_score)       AS avg_lead_score,    -- NULL scores ignored by AVG
           AVG(won_cycle_days)   AS avg_sales_cycle_days
    FROM vw_lead_outcomes
    GROUP BY channel_id
)
SELECT ch.channel_id,
       ch.channel_name,
       ch.channel_group,
       ch.is_paid,
       m.impressions,
       m.clicks,
       m.sessions,
       ROUND(m.spend, 2)                                             AS spend,
       f.leads, f.mqls, f.sqls, f.opportunities, f.customers,
       ROUND(f.won_revenue, 2)                                       AS won_revenue,
       ROUND(f.avg_lead_score, 1)                                    AS avg_lead_score,
       ROUND(f.avg_sales_cycle_days, 1)                              AS avg_sales_cycle_days,
       ROUND(1.0 * m.clicks   / NULLIF(m.impressions, 0), 4)          AS ctr,
       ROUND(m.spend          / NULLIF(m.clicks, 0), 2)               AS cpc,
       ROUND(1.0 * f.leads    / NULLIF(m.sessions, 0), 4)             AS session_to_lead_rate,
       ROUND(1.0 * f.sqls     / NULLIF(f.leads, 0), 4)                AS lead_to_sql_rate,
       ROUND(1.0 * f.customers / NULLIF(f.leads, 0), 4)               AS lead_to_customer_rate,
       ROUND(NULLIF(m.spend, 0) / NULLIF(f.leads, 0), 2)              AS cpl,     -- NULL if no spend
       ROUND(NULLIF(m.spend, 0) / NULLIF(f.customers, 0), 2)          AS cac,     -- NULL if no spend
       ROUND(f.won_revenue / NULLIF(m.spend, 0), 2)                   AS revenue_to_spend,
       ROUND(f.won_revenue / NULLIF(f.customers, 0), 2)               AS avg_deal_value,
       ROUND(1.0 * f.won_revenue / SUM(f.won_revenue) OVER (), 4)     AS revenue_share
FROM dim_channel ch
LEFT JOIN mkt m    ON m.channel_id = ch.channel_id
LEFT JOIN funnel f ON f.channel_id = ch.channel_id;

-- ---------------------------------------------------------------------
-- vw_campaign_performance: same KPIs per campaign + budget recommendation
-- Recommendation rule (paid campaigns, first-year revenue vs spend):
--   SCALE     revenue/spend >= 1.5 and SQL rate above channel average
--   MAINTAIN  revenue/spend >= 1.0
--   OPTIMISE  revenue/spend between 0.5 and 1.0
--   REDUCE    revenue/spend <  0.5
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS vw_campaign_performance;
CREATE VIEW vw_campaign_performance AS
WITH mkt AS (
    SELECT campaign_id, SUM(sessions) AS sessions, SUM(spend) AS spend
    FROM fact_marketing_daily
    GROUP BY campaign_id
),
funnel AS (
    SELECT campaign_id,
           COUNT(*) AS leads, SUM(is_mql) AS mqls, SUM(is_sql) AS sqls,
           SUM(has_opportunity) AS opportunities, SUM(is_customer) AS customers,
           SUM(won_value) AS won_revenue, AVG(lead_score) AS avg_lead_score
    FROM vw_lead_outcomes
    WHERE campaign_id IS NOT NULL
    GROUP BY campaign_id
),
base AS (
    SELECT c.campaign_id, c.campaign_name, ch.channel_name, ch.is_paid, c.objective,
           COALESCE(m.sessions, 0) AS sessions, ROUND(COALESCE(m.spend, 0), 2) AS spend,
           COALESCE(f.leads, 0) AS leads, COALESCE(f.mqls, 0) AS mqls, COALESCE(f.sqls, 0) AS sqls,
           COALESCE(f.opportunities, 0) AS opportunities, COALESCE(f.customers, 0) AS customers,
           ROUND(COALESCE(f.won_revenue, 0), 2) AS won_revenue,
           ROUND(f.avg_lead_score, 1) AS avg_lead_score,
           1.0 * f.sqls / NULLIF(f.leads, 0) AS lead_to_sql_rate,
           AVG(1.0 * f.sqls / NULLIF(f.leads, 0)) OVER (PARTITION BY c.channel_id) AS channel_avg_sql_rate
    FROM dim_campaign c
    JOIN dim_channel ch ON ch.channel_id = c.channel_id
    LEFT JOIN mkt m     ON m.campaign_id = c.campaign_id
    LEFT JOIN funnel f  ON f.campaign_id = c.campaign_id
)
SELECT campaign_id, campaign_name, channel_name, objective, sessions, spend,
       leads, mqls, sqls, opportunities, customers, won_revenue, avg_lead_score,
       ROUND(lead_to_sql_rate, 4)                                   AS lead_to_sql_rate,
       ROUND(1.0 * customers / NULLIF(leads, 0), 4)                 AS lead_to_customer_rate,
       ROUND(NULLIF(spend, 0) / NULLIF(leads, 0), 2)                AS cpl,
       ROUND(NULLIF(spend, 0) / NULLIF(customers, 0), 2)            AS cac,
       ROUND(won_revenue / NULLIF(spend, 0), 2)                     AS revenue_to_spend,
       CASE
           WHEN is_paid = 0                                        THEN 'NON-PAID'
           WHEN won_revenue / NULLIF(spend, 0) >= 1.5
                AND lead_to_sql_rate >= channel_avg_sql_rate       THEN 'SCALE'
           WHEN won_revenue / NULLIF(spend, 0) >= 1.0              THEN 'MAINTAIN'
           WHEN won_revenue / NULLIF(spend, 0) >= 0.5              THEN 'OPTIMISE'
           ELSE 'REDUCE'
       END                                                          AS recommendation,
       DENSE_RANK() OVER (ORDER BY won_revenue DESC)                AS revenue_rank
FROM base;

-- ---------------------------------------------------------------------
-- vw_funnel: long format (one row per channel x stage) for funnel charts
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS vw_funnel;
CREATE VIEW vw_funnel AS
WITH stages AS (
    SELECT channel_name, 1 AS stage_order, 'Sessions' AS stage, sessions AS volume FROM vw_channel_performance
    UNION ALL SELECT channel_name, 2, 'Leads',         leads         FROM vw_channel_performance
    UNION ALL SELECT channel_name, 3, 'MQL',           mqls          FROM vw_channel_performance
    UNION ALL SELECT channel_name, 4, 'SQL',           sqls          FROM vw_channel_performance
    UNION ALL SELECT channel_name, 5, 'Opportunity',   opportunities FROM vw_channel_performance
    UNION ALL SELECT channel_name, 6, 'Customer',      customers     FROM vw_channel_performance
)
SELECT channel_name,
       stage_order,
       stage,
       volume,
       LAG(volume) OVER (PARTITION BY channel_name ORDER BY stage_order)            AS previous_volume,
       ROUND(1.0 * volume / NULLIF(LAG(volume) OVER (PARTITION BY channel_name ORDER BY stage_order), 0), 4)
                                                                                     AS conversion_from_previous,
       ROUND(1.0 - 1.0 * volume / NULLIF(LAG(volume) OVER (PARTITION BY channel_name ORDER BY stage_order), 0), 4)
                                                                                     AS drop_off
FROM stages;

-- ---------------------------------------------------------------------
-- vw_monthly_management: the monthly table a manager reads first
-- Customers and revenue are counted in their close month.
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS vw_monthly_management;
CREATE VIEW vw_monthly_management AS
WITH months AS (
    SELECT DISTINCT year_month FROM dim_date
    WHERE date_key BETWEEN 20251101 AND 20260630
),
mkt AS (
    SELECT d.year_month, SUM(m.sessions) AS sessions, SUM(m.spend) AS spend
    FROM fact_marketing_daily m JOIN dim_date d ON d.date_key = m.date_key
    GROUP BY d.year_month
),
leads AS (
    SELECT year_month, COUNT(*) AS leads, SUM(is_mql) AS mqls, SUM(is_sql) AS sqls
    FROM vw_lead_outcomes GROUP BY year_month
),
won AS (
    SELECT d.year_month, COUNT(*) AS customers, SUM(o.won_value) AS won_revenue
    FROM fact_opportunities o
    JOIN dim_date d ON d.date_key = COALESCE(o.close_date_key, o.created_date_key)
    WHERE o.is_won = 1
    GROUP BY d.year_month
),
mrr AS (
    SELECT year_month,
           SUM(CASE WHEN is_active = 1 THEN mrr ELSE 0 END) AS mrr,
           SUM(is_active)  AS active_customers,
           SUM(is_churned) AS churned_customers
    FROM fact_customer_monthly GROUP BY year_month
),
joined AS (
    SELECT mo.year_month,
           COALESCE(mk.sessions, 0) AS sessions,
           ROUND(COALESCE(mk.spend, 0), 2) AS spend,
           COALESCE(l.leads, 0) AS leads, COALESCE(l.mqls, 0) AS mqls, COALESCE(l.sqls, 0) AS sqls,
           COALESCE(w.customers, 0) AS customers,
           ROUND(COALESCE(w.won_revenue, 0), 2) AS won_revenue,
           ROUND(COALESCE(r.mrr, 0), 2) AS mrr,
           COALESCE(r.active_customers, 0) AS active_customers,
           COALESCE(r.churned_customers, 0) AS churned_customers
    FROM months mo
    LEFT JOIN mkt mk  ON mk.year_month = mo.year_month
    LEFT JOIN leads l ON l.year_month  = mo.year_month
    LEFT JOIN won w   ON w.year_month  = mo.year_month
    LEFT JOIN mrr r   ON r.year_month  = mo.year_month
)
SELECT *,
       ROUND(spend / NULLIF(leads, 0), 2)                                              AS cpl,
       ROUND(spend / NULLIF(customers, 0), 2)                                          AS blended_cac,
       ROUND(1.0 * churned_customers / NULLIF(active_customers + churned_customers, 0), 4) AS churn_rate,
       ROUND(1.0 * (leads - LAG(leads) OVER w) / NULLIF(LAG(leads) OVER w, 0), 4)      AS mom_leads,
       ROUND((won_revenue - LAG(won_revenue) OVER w) / NULLIF(LAG(won_revenue) OVER w, 0), 4) AS mom_revenue
FROM joined
WINDOW w AS (ORDER BY year_month);

-- ---------------------------------------------------------------------
-- vw_revenue_pipeline: one row per opportunity, enriched for pipeline analysis
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS vw_revenue_pipeline;
CREATE VIEW vw_revenue_pipeline AS
SELECT o.opportunity_id,
       ch.channel_name,
       COALESCE(c.campaign_name, 'Unassigned')                        AS campaign_name,
       r.region_name,
       o.company_size,
       o.plan,
       o.sites,
       o.status,
       dc.year_month                                                  AS created_month,
       dx.year_month                                                  AS close_month,
       o.expected_value,
       o.won_value,
       CASE WHEN o.status = 'Open' THEN o.expected_value ELSE 0 END   AS open_pipeline_value,
       CASE WHEN o.status = 'Lost' THEN o.expected_value ELSE 0 END   AS lost_value,
       o.sales_cycle_days,
       o.value_imputed
FROM fact_opportunities o
JOIN dim_channel ch      ON ch.channel_id = o.channel_id
LEFT JOIN dim_campaign c ON c.campaign_id = o.campaign_id
JOIN dim_region r        ON r.region_id   = o.region_id
JOIN dim_date dc         ON dc.date_key   = o.created_date_key
LEFT JOIN dim_date dx    ON dx.date_key   = o.close_date_key;

-- ---------------------------------------------------------------------
-- vw_customer_value: one row per customer with MRR history summarised
-- ---------------------------------------------------------------------
DROP VIEW IF EXISTS vw_customer_value;
CREATE VIEW vw_customer_value AS
WITH hist AS (
    SELECT customer_id,
           COUNT(*)                       AS months_billed,
           SUM(mrr)                       AS revenue_to_date,
           MAX(is_churned)                AS has_churned,
           MAX(year_month)                AS last_month
    FROM fact_customer_monthly
    GROUP BY customer_id
)
SELECT cu.customer_id,
       ch.channel_name,
       r.region_name,
       r.region_group,
       cu.company_size,
       cu.business_type,
       cu.plan,
       d.year_month                   AS acquisition_month,
       cu.starting_mrr,
       h.months_billed,
       ROUND(h.revenue_to_date, 2)    AS revenue_to_date,
       h.has_churned,
       h.last_month
FROM dim_customer cu
JOIN dim_channel ch ON ch.channel_id = cu.channel_id
JOIN dim_region r   ON r.region_id   = cu.region_id
JOIN dim_date d     ON d.date_key    = cu.acquisition_date_key
LEFT JOIN hist h    ON h.customer_id = cu.customer_id;
