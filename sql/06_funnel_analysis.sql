-- =====================================================================
-- 06_funnel_analysis.sql — where does the funnel lose value?
-- Synthetic data: results describe the demonstration scenario, not ODRES.
-- =====================================================================

-- Q01. Full funnel by channel, with the conversion at each stage
SELECT channel_name,
       sessions,
       leads,
       mqls,
       sqls,
       opportunities,
       customers,
       ROUND(100.0 * leads         / NULLIF(sessions, 0), 2)      AS session_to_lead_pct,
       ROUND(100.0 * mqls          / NULLIF(leads, 0), 1)         AS lead_to_mql_pct,      -- Q05
       ROUND(100.0 * sqls          / NULLIF(mqls, 0), 1)          AS mql_to_sql_pct,       -- Q06
       ROUND(100.0 * customers     / NULLIF(sqls, 0), 1)          AS sql_to_customer_pct,  -- Q07
       ROUND(100.0 * customers     / NULLIF(leads, 0), 2)         AS lead_to_customer_pct  -- Q08
FROM vw_channel_performance
ORDER BY customers DESC;

-- Q05-Q08. Company-wide stage conversions in long format (feeds a funnel chart)
SELECT stage,
       SUM(volume)                                                                   AS volume,
       ROUND(100.0 * SUM(volume) / NULLIF(SUM(previous_volume), 0), 1)               AS conversion_from_previous_pct,
       ROUND(100.0 * (SUM(previous_volume) - SUM(volume)) / NULLIF(SUM(previous_volume), 0), 1) AS drop_off_pct
FROM vw_funnel
GROUP BY stage_order, stage
ORDER BY stage_order;

-- Q01b. Biggest drop-off per channel: which stage should each channel fix first?
WITH ranked AS (
    SELECT channel_name, stage, drop_off,
           RANK() OVER (PARTITION BY channel_name ORDER BY drop_off DESC) AS rnk
    FROM vw_funnel
    WHERE stage_order >= 3                   -- from Lead onwards: sessions -> lead is a website topic
)
SELECT channel_name, stage AS weakest_transition_into, ROUND(100.0 * drop_off, 1) AS drop_off_pct
FROM ranked
WHERE rnk = 1
ORDER BY drop_off_pct DESC;

-- Q19. Channels with strong lead quality but low volume (candidates to scale)
--      quality above the company-wide SQL rate, volume below the average channel volume
SELECT channel_name,
       leads,
       ROUND(100.0 * lead_to_sql_rate, 1)       AS lead_to_sql_pct,
       ROUND(100.0 * lead_to_customer_rate, 1)  AS lead_to_customer_pct,
       avg_lead_score
FROM vw_channel_performance
WHERE lead_to_sql_rate > (SELECT 1.0 * SUM(is_sql) / COUNT(*) FROM fact_leads)
  AND leads < (SELECT AVG(leads) FROM vw_channel_performance)
ORDER BY lead_to_sql_rate DESC;

-- Q19b. The opposite: high volume, low quality (volume alone is misleading)
SELECT channel_name,
       leads,
       ROUND(100.0 * leads / (SELECT SUM(leads) FROM vw_channel_performance), 1) AS share_of_leads_pct,
       ROUND(100.0 * customers / (SELECT SUM(customers) FROM vw_channel_performance), 1) AS share_of_customers_pct,
       ROUND(100.0 * lead_to_sql_rate, 1) AS lead_to_sql_pct
FROM vw_channel_performance
ORDER BY share_of_leads_pct - share_of_customers_pct DESC;

-- Q14b. Lead-score bands: is the score predictive of conversion?
SELECT CASE
           WHEN lead_score IS NULL THEN 'Unknown'
           WHEN lead_score >= 80   THEN '80-100'
           WHEN lead_score >= 60   THEN '60-79'
           WHEN lead_score >= 40   THEN '40-59'
           ELSE '0-39'
       END                                                  AS score_band,
       COUNT(*)                                             AS leads,
       ROUND(100.0 * SUM(is_mql) / COUNT(*), 1)             AS mql_pct,
       ROUND(100.0 * SUM(is_sql) / COUNT(*), 1)             AS sql_pct,
       ROUND(100.0 * SUM(is_customer) / COUNT(*), 2)        AS customer_pct
FROM vw_lead_outcomes
GROUP BY score_band
ORDER BY MIN(COALESCE(lead_score, -1));

-- Q01c. Funnel trend: monthly stage conversions (is quality improving over time?)
SELECT year_month,
       COUNT(*)                                        AS leads,
       ROUND(100.0 * SUM(is_mql) / COUNT(*), 1)        AS lead_to_mql_pct,
       ROUND(100.0 * SUM(is_sql) / NULLIF(SUM(is_mql), 0), 1) AS mql_to_sql_pct,
       ROUND(AVG(lead_score), 1)                       AS avg_score
FROM vw_lead_outcomes
GROUP BY year_month
ORDER BY year_month;
