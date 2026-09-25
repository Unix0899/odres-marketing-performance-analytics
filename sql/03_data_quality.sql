-- =====================================================================
-- 03_data_quality.sql — data-quality controls on the loaded database
-- Synthetic data. Every query should return 0 in the "failures" column,
-- except the documented warnings (unknown lead score, unassigned campaign).
-- =====================================================================

-- Q25a. Row counts per table (first thing to check after a load)
SELECT 'dim_date' AS table_name, COUNT(*) AS row_count FROM dim_date
UNION ALL SELECT 'dim_channel',           COUNT(*) FROM dim_channel
UNION ALL SELECT 'dim_campaign',          COUNT(*) FROM dim_campaign
UNION ALL SELECT 'dim_region',            COUNT(*) FROM dim_region
UNION ALL SELECT 'dim_customer',          COUNT(*) FROM dim_customer
UNION ALL SELECT 'fact_marketing_daily',  COUNT(*) FROM fact_marketing_daily
UNION ALL SELECT 'fact_leads',            COUNT(*) FROM fact_leads
UNION ALL SELECT 'fact_opportunities',    COUNT(*) FROM fact_opportunities
UNION ALL SELECT 'fact_customer_monthly', COUNT(*) FROM fact_customer_monthly;

-- Q25b. Business-rule checks: one row per rule, failures must be 0
SELECT 'SQL implies MQL'            AS rule, COUNT(*) AS failures FROM fact_leads WHERE is_sql = 1 AND is_mql = 0
UNION ALL
SELECT 'Spend >= 0',                COUNT(*) FROM fact_marketing_daily WHERE spend < 0
UNION ALL
SELECT 'Clicks <= impressions',     COUNT(*) FROM fact_marketing_daily WHERE clicks > impressions
UNION ALL
SELECT 'Lead score 0-100',          COUNT(*) FROM fact_leads WHERE lead_score NOT BETWEEN 0 AND 100
UNION ALL
SELECT 'Won value >= 0',            COUNT(*) FROM fact_opportunities WHERE won_value < 0
UNION ALL
SELECT 'Won deal has a value',      COUNT(*) FROM fact_opportunities WHERE status = 'Won' AND won_value <= 0
UNION ALL
SELECT 'Close date after creation', COUNT(*) FROM fact_opportunities WHERE close_date_key < created_date_key
UNION ALL
SELECT 'Status is Won/Lost/Open',   COUNT(*) FROM fact_opportunities WHERE status NOT IN ('Won', 'Lost', 'Open');

-- Q25c. Referential integrity: facts pointing to missing dimension rows (LEFT JOIN ... IS NULL)
SELECT 'lead -> channel' AS relation, COUNT(*) AS orphans
FROM fact_leads l LEFT JOIN dim_channel c ON c.channel_id = l.channel_id WHERE c.channel_id IS NULL
UNION ALL
SELECT 'lead -> region', COUNT(*)
FROM fact_leads l LEFT JOIN dim_region r ON r.region_id = l.region_id WHERE r.region_id IS NULL
UNION ALL
SELECT 'opportunity -> lead', COUNT(*)
FROM fact_opportunities o LEFT JOIN fact_leads l ON l.lead_id = o.lead_id WHERE l.lead_id IS NULL
UNION ALL
SELECT 'customer -> won opportunity', COUNT(*)
FROM dim_customer cu LEFT JOIN fact_opportunities o ON o.opportunity_id = cu.opportunity_id AND o.is_won = 1
WHERE o.opportunity_id IS NULL
UNION ALL
SELECT 'marketing -> date', COUNT(*)
FROM fact_marketing_daily m LEFT JOIN dim_date d ON d.date_key = m.date_key WHERE d.date_key IS NULL;

-- Q25d. Uniqueness of business keys (GROUP BY ... HAVING COUNT(*) > 1)
SELECT 'fact_marketing_daily (date, campaign)' AS grain, COUNT(*) AS duplicated_keys
FROM (SELECT date_key, campaign_id FROM fact_marketing_daily GROUP BY date_key, campaign_id HAVING COUNT(*) > 1)
UNION ALL
SELECT 'fact_customer_monthly (customer, month)', COUNT(*)
FROM (SELECT customer_id, year_month FROM fact_customer_monthly GROUP BY customer_id, year_month HAVING COUNT(*) > 1)
UNION ALL
SELECT 'dim_customer (opportunity)', COUNT(*)
FROM (SELECT opportunity_id FROM dim_customer GROUP BY opportunity_id HAVING COUNT(*) > 1);

-- Q25e. Documented warnings: kept on purpose, but monitored
SELECT 'Lead score unknown (NULL)' AS warning, COUNT(*) AS rows_affected,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM fact_leads), 2) AS pct_of_leads
FROM fact_leads WHERE lead_score IS NULL
UNION ALL
SELECT 'Lead with unassigned campaign', COUNT(*),
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM fact_leads), 2)
FROM fact_leads WHERE campaign_id IS NULL
UNION ALL
SELECT 'Won value imputed from expected value', COUNT(*),
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM fact_opportunities WHERE is_won = 1), 2)
FROM fact_opportunities WHERE value_imputed = 1;

-- Q25f. Completeness by month: a month with missing marketing days would bias trends
SELECT d.year_month,
       COUNT(DISTINCT d.date_key)              AS calendar_days,
       COUNT(DISTINCT m.date_key)              AS days_with_marketing_data,
       COUNT(DISTINCT d.date_key) - COUNT(DISTINCT m.date_key) AS missing_days
FROM dim_date d
LEFT JOIN fact_marketing_daily m ON m.date_key = d.date_key
WHERE d.date_key BETWEEN 20251101 AND 20260630
GROUP BY d.year_month
ORDER BY d.year_month;
