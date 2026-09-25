-- =====================================================================
-- integrity_tests.sql — automated tests (run by src/run_sql_tests.py)
-- Contract: every query returns ONE row with columns (test_name, failures).
-- The build fails if any failures > 0.
-- =====================================================================

SELECT 'sql_implies_mql' AS test_name, COUNT(*) AS failures FROM fact_leads WHERE is_sql = 1 AND is_mql = 0;

SELECT 'spend_not_negative', COUNT(*) FROM fact_marketing_daily WHERE spend < 0;

SELECT 'lead_score_in_range', COUNT(*) FROM fact_leads WHERE lead_score IS NOT NULL AND lead_score NOT BETWEEN 0 AND 100;

SELECT 'won_value_not_negative', COUNT(*) FROM fact_opportunities WHERE won_value < 0;

SELECT 'won_deal_has_value', COUNT(*) FROM fact_opportunities WHERE status = 'Won' AND won_value <= 0;

SELECT 'no_missing_critical_ids',
       (SELECT COUNT(*) FROM fact_leads WHERE lead_id IS NULL)
     + (SELECT COUNT(*) FROM fact_opportunities WHERE opportunity_id IS NULL OR lead_id IS NULL)
     + (SELECT COUNT(*) FROM dim_customer WHERE customer_id IS NULL OR opportunity_id IS NULL);

SELECT 'opportunity_has_lead', COUNT(*)
FROM fact_opportunities o LEFT JOIN fact_leads l ON l.lead_id = o.lead_id WHERE l.lead_id IS NULL;

SELECT 'customer_has_won_opportunity', COUNT(*)
FROM dim_customer c LEFT JOIN fact_opportunities o ON o.opportunity_id = c.opportunity_id AND o.is_won = 1
WHERE o.opportunity_id IS NULL;

SELECT 'customers_equal_won_opportunities',
       ABS((SELECT COUNT(*) FROM dim_customer) - (SELECT COUNT(*) FROM fact_opportunities WHERE is_won = 1));

SELECT 'funnel_is_monotonic', COUNT(*)
FROM vw_channel_performance
WHERE mqls > leads OR sqls > mqls OR customers > opportunities;

SELECT 'view_totals_match_facts',
       ABS((SELECT SUM(leads) FROM vw_channel_performance) - (SELECT COUNT(*) FROM fact_leads))
     + ABS(ROUND((SELECT SUM(spend) FROM vw_channel_performance) - (SELECT SUM(spend) FROM fact_marketing_daily), 0));

SELECT 'revenue_reconciles',
       ABS(ROUND((SELECT SUM(won_revenue) FROM vw_monthly_management)
               - (SELECT SUM(won_value) FROM fact_opportunities WHERE is_won = 1), 0));

SELECT 'no_cac_for_unpaid_channels', COUNT(*) FROM vw_channel_performance WHERE is_paid = 0 AND spend = 0 AND cac IS NOT NULL;

SELECT 'close_after_create', COUNT(*) FROM fact_opportunities WHERE close_date_key < created_date_key;
