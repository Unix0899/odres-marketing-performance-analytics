-- =====================================================================
-- 05_campaign_analysis.sql — which campaigns deserve budget?
-- Synthetic data: results describe the demonstration scenario, not ODRES.
-- =====================================================================

-- Q02. Funnel by campaign (including leads whose campaign tag was unknown)
SELECT COALESCE(c.campaign_name, 'Unassigned')                      AS campaign_name,
       ch.channel_name,
       COUNT(*)                                                      AS leads,
       SUM(lo.is_mql)                                                AS mqls,
       SUM(lo.is_sql)                                                AS sqls,
       SUM(lo.has_opportunity)                                       AS opportunities,
       SUM(lo.is_customer)                                           AS customers,
       ROUND(100.0 * SUM(lo.is_sql) / COUNT(*), 1)                   AS lead_to_sql_pct,
       ROUND(100.0 * SUM(lo.is_customer) / COUNT(*), 2)              AS lead_to_customer_pct
FROM vw_lead_outcomes lo
JOIN dim_channel ch       ON ch.channel_id = lo.channel_id
LEFT JOIN dim_campaign c  ON c.campaign_id = lo.campaign_id
GROUP BY COALESCE(c.campaign_name, 'Unassigned'), ch.channel_name
ORDER BY leads DESC;

-- Q10. Revenue by campaign, with rank overall and rank inside its channel
SELECT campaign_name,
       channel_name,
       won_revenue,
       DENSE_RANK() OVER (ORDER BY won_revenue DESC)                          AS rank_overall,
       DENSE_RANK() OVER (PARTITION BY channel_name ORDER BY won_revenue DESC) AS rank_in_channel
FROM vw_campaign_performance
ORDER BY won_revenue DESC;

-- Q17. Best paid campaigns: revenue per euro spent, only campaigns with enough evidence
SELECT campaign_name, channel_name, spend, customers, won_revenue, cac, revenue_to_spend, recommendation
FROM vw_campaign_performance
WHERE spend > 0
  AND customers >= 5                                   -- avoid ranking on 1-2 lucky deals
ORDER BY revenue_to_spend DESC;

-- Q18. Campaigns with high spend and weak conversion (budget waste candidates)
--      high spend = above the average paid-campaign spend (subquery)
--      weak conversion = lead-to-SQL rate below the overall rate
SELECT campaign_name,
       channel_name,
       spend,
       leads,
       sqls,
       ROUND(100.0 * lead_to_sql_rate, 1)  AS lead_to_sql_pct,
       customers,
       cac,
       recommendation
FROM vw_campaign_performance
WHERE spend > (SELECT AVG(spend) FROM vw_campaign_performance WHERE spend > 0)
  AND lead_to_sql_rate < (SELECT 1.0 * SUM(is_sql) / COUNT(*) FROM fact_leads)
ORDER BY spend DESC;

-- Q18b. Budget recommendation per paid campaign (SCALE / MAINTAIN / OPTIMISE / REDUCE)
SELECT recommendation,
       COUNT(*)                         AS campaigns,
       ROUND(SUM(spend), 0)             AS spend,
       ROUND(SUM(won_revenue), 0)       AS won_revenue,
       GROUP_CONCAT(campaign_name, ', ') AS campaign_list
FROM vw_campaign_performance
WHERE recommendation <> 'NON-PAID'
GROUP BY recommendation
ORDER BY CASE recommendation WHEN 'SCALE' THEN 1 WHEN 'MAINTAIN' THEN 2 WHEN 'OPTIMISE' THEN 3 ELSE 4 END;

-- Q17b. Monthly spend and leads for the top-3 revenue campaigns (trend check before scaling)
WITH top3 AS (
    SELECT campaign_id FROM vw_campaign_performance
    WHERE spend > 0
    ORDER BY revenue_to_spend DESC
    LIMIT 3
)
SELECT c.campaign_name,
       d.year_month,
       ROUND(SUM(m.spend), 0)                      AS spend,
       SUM(m.sessions)                             AS sessions,
       (SELECT COUNT(*) FROM vw_lead_outcomes lo
         WHERE lo.campaign_id = c.campaign_id AND lo.year_month = d.year_month) AS leads
FROM fact_marketing_daily m
JOIN top3 t          ON t.campaign_id = m.campaign_id
JOIN dim_campaign c  ON c.campaign_id = m.campaign_id
JOIN dim_date d      ON d.date_key    = m.date_key
GROUP BY c.campaign_name, c.campaign_id, d.year_month
ORDER BY c.campaign_name, d.year_month;
