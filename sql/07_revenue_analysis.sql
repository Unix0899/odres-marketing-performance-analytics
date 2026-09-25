-- =====================================================================
-- 07_revenue_analysis.sql — pipeline, revenue and customer value
-- Synthetic data: results describe the demonstration scenario, not ODRES.
-- Revenue = first-year contract value of Won opportunities (EUR).
-- =====================================================================

-- Q09 + Q11. Revenue by channel and revenue share, with cumulative share (Pareto)
SELECT channel_name,
       won_revenue,
       ROUND(100.0 * revenue_share, 1)                                                AS revenue_share_pct,
       ROUND(100.0 * SUM(revenue_share) OVER (ORDER BY won_revenue DESC
                                              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 1)
                                                                                      AS cumulative_share_pct
FROM vw_channel_performance
ORDER BY won_revenue DESC;

-- Q12. Average deal value and win rate by channel
SELECT channel_name,
       COUNT(*)                                                             AS closed_opportunities,
       SUM(CASE WHEN status = 'Won' THEN 1 ELSE 0 END)                      AS won,
       ROUND(100.0 * SUM(CASE WHEN status = 'Won' THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_rate_pct,
       ROUND(AVG(CASE WHEN status = 'Won' THEN won_value END), 0)          AS avg_deal_value
FROM vw_revenue_pipeline
WHERE status IN ('Won', 'Lost')
GROUP BY channel_name
ORDER BY avg_deal_value DESC;

-- Q13. Sales cycle: won vs lost, by company size (days from opportunity to close)
SELECT company_size,
       ROUND(AVG(CASE WHEN status = 'Won'  THEN sales_cycle_days END), 1) AS won_cycle_days,
       ROUND(AVG(CASE WHEN status = 'Lost' THEN sales_cycle_days END), 1) AS lost_cycle_days,
       COUNT(sales_cycle_days)                                              AS deals_with_known_cycle
FROM vw_revenue_pipeline
WHERE status IN ('Won', 'Lost')
GROUP BY company_size
ORDER BY won_cycle_days;

-- Q21. Performance by region
SELECT r.region_group,
       r.region_name,
       COUNT(*)                                                AS leads,
       SUM(lo.is_customer)                                     AS customers,
       ROUND(100.0 * SUM(lo.is_customer) / COUNT(*), 2)        AS lead_to_customer_pct,
       ROUND(SUM(lo.won_value), 0)                             AS won_revenue,
       ROUND(SUM(lo.won_value) / NULLIF(SUM(lo.is_customer), 0), 0) AS avg_deal_value
FROM vw_lead_outcomes lo
JOIN dim_region r ON r.region_id = lo.region_id
GROUP BY r.region_group, r.region_name
ORDER BY won_revenue DESC;

-- Q22. Performance by company size: volume vs value
SELECT company_size,
       COUNT(*)                                                AS leads,
       SUM(is_customer)                                        AS customers,
       ROUND(100.0 * SUM(is_customer) / COUNT(*), 2)           AS lead_to_customer_pct,
       ROUND(SUM(won_value) / NULLIF(SUM(is_customer), 0), 0)  AS avg_deal_value,
       ROUND(100.0 * SUM(won_value) / (SELECT SUM(won_value) FROM vw_lead_outcomes), 1) AS revenue_share_pct
FROM vw_lead_outcomes
GROUP BY company_size
ORDER BY avg_deal_value DESC;

-- Q13b. Pipeline status: won, lost and still-open value
SELECT status,
       COUNT(*)                        AS opportunities,
       ROUND(SUM(expected_value), 0)   AS expected_value,
       ROUND(SUM(won_value), 0)        AS won_value,
       ROUND(AVG(expected_value), 0)   AS avg_expected_value
FROM vw_revenue_pipeline
GROUP BY status
ORDER BY opportunities DESC;

-- Q13c. Open pipeline by campaign at the end of the period (what is coming next)
SELECT campaign_name, channel_name,
       COUNT(*)                          AS open_opportunities,
       ROUND(SUM(open_pipeline_value), 0) AS open_pipeline_value
FROM vw_revenue_pipeline
WHERE status = 'Open'
GROUP BY campaign_name, channel_name
HAVING SUM(open_pipeline_value) > 0
ORDER BY open_pipeline_value DESC;

-- Q12b. Plan mix: which plan drives revenue?
SELECT plan,
       COUNT(*)                                             AS customers,
       ROUND(AVG(starting_mrr), 2)                          AS avg_starting_mrr,
       ROUND(SUM(starting_mrr), 2)                          AS starting_mrr_total,
       ROUND(100.0 * SUM(has_churned) / COUNT(*), 1)        AS churned_pct
FROM vw_customer_value
GROUP BY plan
ORDER BY avg_starting_mrr DESC;

-- Q23b. New customers and new MRR by acquisition month and channel group
SELECT cv.acquisition_month,
       CASE WHEN ch.is_paid = 1 THEN 'Paid' ELSE 'Non-paid' END AS source_type,
       COUNT(*)                                                 AS new_customers,
       ROUND(SUM(cv.starting_mrr), 2)                           AS new_mrr
FROM vw_customer_value cv
JOIN dim_channel ch ON ch.channel_name = cv.channel_name
GROUP BY cv.acquisition_month, source_type
ORDER BY cv.acquisition_month, source_type;
