-- =====================================================================
-- 04_kpi_queries.sql — management KPIs
-- Synthetic data: results describe the demonstration scenario, not ODRES.
-- =====================================================================

-- Q00. Executive summary: one row, the numbers a manager asks for first
WITH mkt AS (
    SELECT SUM(impressions) AS impressions, SUM(clicks) AS clicks,
           SUM(sessions) AS sessions, SUM(spend) AS spend
    FROM fact_marketing_daily
),
funnel AS (
    SELECT COUNT(*) AS leads, SUM(is_mql) AS mqls, SUM(is_sql) AS sqls,
           SUM(has_opportunity) AS opportunities, SUM(is_customer) AS customers,
           SUM(won_value) AS won_revenue
    FROM vw_lead_outcomes
)
SELECT ROUND(m.spend, 0)                                  AS total_spend,
       m.sessions,
       f.leads, f.mqls, f.sqls, f.opportunities, f.customers,
       ROUND(f.won_revenue, 0)                            AS won_revenue,
       ROUND(100.0 * m.clicks / NULLIF(m.impressions, 0), 2) AS ctr_pct,
       ROUND(m.spend / NULLIF(f.leads, 0), 2)             AS blended_cpl,
       ROUND(m.spend / NULLIF(f.customers, 0), 2)         AS blended_cac,
       ROUND(100.0 * f.customers / NULLIF(f.leads, 0), 2) AS lead_to_customer_pct,
       ROUND(f.won_revenue / NULLIF(m.spend, 0), 2)       AS revenue_to_spend
FROM mkt m CROSS JOIN funnel f;

-- Q03. CPL by channel (paid channels only: CPL is not meaningful without spend)
SELECT channel_name, spend, leads, cpl
FROM vw_channel_performance
WHERE spend > 0
ORDER BY cpl;

-- Q04. CAC by channel, compared with the average deal value
--      A CAC above the first-year deal value means the channel does not pay back in year one.
SELECT channel_name,
       customers,
       cac,
       avg_deal_value,
       ROUND(avg_deal_value / NULLIF(cac, 0), 2) AS deal_value_to_cac,
       CASE WHEN cac IS NULL          THEN 'No paid spend'
            WHEN cac > avg_deal_value THEN 'Pays back after year 1'
            ELSE 'Pays back within year 1' END AS payback
FROM vw_channel_performance
ORDER BY cac IS NULL, cac;

-- Q20. Paid vs non-paid acquisition
SELECT CASE WHEN is_paid = 1 THEN 'Paid' ELSE 'Non-paid' END AS source_type,
       ROUND(SUM(spend), 0)                                  AS spend,
       SUM(leads)                                            AS leads,
       SUM(customers)                                        AS customers,
       ROUND(SUM(won_revenue), 0)                            AS won_revenue,
       ROUND(100.0 * SUM(won_revenue) / (SELECT SUM(won_revenue) FROM vw_channel_performance), 1) AS revenue_share_pct,
       ROUND(100.0 * SUM(customers) / NULLIF(SUM(leads), 0), 2) AS lead_to_customer_pct,
       ROUND(SUM(spend) / NULLIF(SUM(customers), 0), 0)       AS cac
FROM vw_channel_performance
GROUP BY source_type;

-- Q14. Lead score by source: does the channel bring qualified prospects?
SELECT ch.channel_name,
       COUNT(*)                                                    AS leads,
       COUNT(l.lead_score)                                         AS scored_leads,
       ROUND(AVG(l.lead_score), 1)                                 AS avg_score,
       ROUND(100.0 * SUM(CASE WHEN l.lead_score >= 70 THEN 1 ELSE 0 END) / COUNT(l.lead_score), 1) AS pct_high_score,
       ROUND(100.0 * SUM(CASE WHEN l.lead_score <  40 THEN 1 ELSE 0 END) / COUNT(l.lead_score), 1) AS pct_low_score
FROM fact_leads l
JOIN dim_channel ch ON ch.channel_id = l.channel_id
GROUP BY ch.channel_name
ORDER BY avg_score DESC;

-- Q15. Month-over-month lead growth (window function LAG)
WITH monthly AS (
    SELECT year_month, COUNT(*) AS leads
    FROM vw_lead_outcomes
    GROUP BY year_month
)
SELECT year_month,
       leads,
       LAG(leads) OVER (ORDER BY year_month)                                   AS previous_month,
       ROUND(100.0 * (leads - LAG(leads) OVER (ORDER BY year_month))
             / NULLIF(LAG(leads) OVER (ORDER BY year_month), 0), 1)            AS mom_growth_pct
FROM monthly
ORDER BY year_month;

-- Q16. Month-over-month won-revenue growth + 3-month rolling average
--      (revenue is lumpy in B2B: the rolling average is the better trend signal)
SELECT year_month,
       won_revenue,
       ROUND(100.0 * mom_revenue, 1)                                           AS mom_growth_pct,
       ROUND(AVG(won_revenue) OVER (ORDER BY year_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 0)
                                                                                AS rolling_3m_revenue
FROM vw_monthly_management
ORDER BY year_month;

-- Q23. MRR and active customers by month, with net new MRR
SELECT year_month,
       active_customers,
       mrr,
       ROUND(mrr - LAG(mrr) OVER (ORDER BY year_month), 2) AS net_new_mrr,
       ROUND(mrr * 12, 0)                                  AS arr_run_rate
FROM vw_monthly_management
ORDER BY year_month;

-- Q24. Churn: monthly logo churn rate and churn by acquisition channel
SELECT year_month, active_customers, churned_customers, ROUND(100.0 * churn_rate, 2) AS churn_rate_pct
FROM vw_monthly_management
ORDER BY year_month;

SELECT channel_name,
       COUNT(*)                                          AS customers,
       SUM(has_churned)                                  AS churned,
       ROUND(100.0 * SUM(has_churned) / COUNT(*), 1)     AS churned_pct,
       ROUND(AVG(starting_mrr), 2)                       AS avg_starting_mrr
FROM vw_customer_value
GROUP BY channel_name
ORDER BY churned_pct DESC;
