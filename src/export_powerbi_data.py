"""
Export the star schema for Power BI to powerbi/data/ (UTF-8 CSV, one file per table).

Power BI-specific adjustments (documented in powerbi/DATA_MODEL.md):
- leads/opportunities/customers with an unknown campaign get campaign_id 0 = "Unassigned"
  so slicers show an explicit member instead of (Blank)
- FactOpportunities gets a close_or_created_date_key used for revenue-by-month
- DimChannel gets a sort column (funnel order of the business, paid first)
"""
import sqlite3

import pandas as pd

from common import DB, POWERBI_DATA, PROCESSED, get_logger

log = get_logger("powerbi")

EXPORTS = {
    "DimDate": "SELECT * FROM dim_date",
    "DimChannel": "SELECT *, channel_id AS sort_order FROM dim_channel",
    "DimCampaign": """SELECT campaign_id, campaign_name, channel_id, objective, start_date FROM dim_campaign
                      UNION ALL SELECT 0, 'Unassigned', NULL, 'Unknown', NULL""",
    "DimRegion": "SELECT * FROM dim_region",
    "DimCustomer": "SELECT customer_id, opportunity_id, acquisition_date_key, channel_id, "
                   "COALESCE(campaign_id, 0) AS campaign_id, region_id, company_size, business_type, plan, "
                   "starting_mrr FROM dim_customer",
    "FactMarketingDaily": "SELECT * FROM fact_marketing_daily",
    "FactLeads": "SELECT lead_id, created_date_key, channel_id, COALESCE(campaign_id, 0) AS campaign_id, region_id, "
                 "company_size, business_type, lead_score, is_mql, is_sql FROM fact_leads",
    "FactOpportunities": "SELECT opportunity_id, lead_id, created_date_key, close_date_key, "
                         "COALESCE(close_date_key, created_date_key) AS revenue_date_key, channel_id, "
                         "COALESCE(campaign_id, 0) AS campaign_id, region_id, company_size, plan, sites, status, "
                         "is_won, expected_value, won_value, sales_cycle_days, value_imputed FROM fact_opportunities",
    "FactCustomerMonthly": "SELECT * FROM fact_customer_monthly",
}
FROM_PROCESSED = {"DataQualityChecks": "data_quality_results.csv", "DataQualityRowCounts": "row_counts.csv",
                  "CleaningLog": "cleaning_log.csv"}


def main():
    POWERBI_DATA.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    tables = {name: pd.read_sql_query(sql, conn) for name, sql in EXPORTS.items()}
    tables.update({name: pd.read_csv(PROCESSED / f) for name, f in FROM_PROCESSED.items()})
    for name, df in tables.items():
        for col in df.columns:                       # integer columns with blanks: write 20260315, not 20260315.0
            if df[col].dtype == "float64" and (df[col].dropna() % 1 == 0).all():
                df[col] = df[col].astype("Int64")
        df.to_csv(POWERBI_DATA / f"{name}.csv", index=False, encoding="utf-8")
        log.info(f"{name:<22} {len(df):>6,} rows")
    conn.close()


if __name__ == "__main__":
    main()
