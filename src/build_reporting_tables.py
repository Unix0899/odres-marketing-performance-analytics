"""
Export the reporting views to data/processed/ (CSV) and a KPI summary (JSON),
plus small samples of the raw exports in data/samples/ for quick browsing on GitHub.
"""
import json
import sqlite3

import pandas as pd

from common import DB, DISCLOSURE, PROCESSED, RAW, SAMPLES, get_logger

log = get_logger("reporting")
VIEWS = ["vw_channel_performance", "vw_campaign_performance", "vw_monthly_management",
         "vw_funnel", "vw_revenue_pipeline", "vw_customer_value"]


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    SAMPLES.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    for v in VIEWS:
        df = pd.read_sql_query(f"SELECT * FROM {v}", conn)
        df.to_csv(PROCESSED / f"{v.removeprefix('vw_')}.csv", index=False)
        log.info(f"{v:<26} -> {len(df):>5,} rows")

    k = conn.execute("""
        SELECT SUM(spend), SUM(impressions), SUM(clicks), SUM(sessions) FROM fact_marketing_daily""").fetchone()
    f = conn.execute("""
        SELECT COUNT(*), SUM(is_mql), SUM(is_sql), SUM(has_opportunity), SUM(is_customer), SUM(won_value)
        FROM vw_lead_outcomes""").fetchone()
    mrr = conn.execute("SELECT mrr, active_customers FROM vw_monthly_management ORDER BY year_month DESC LIMIT 1").fetchone()
    ch = pd.read_sql_query("SELECT * FROM vw_channel_performance", conn)
    conn.close()
    paid = ch[ch.is_paid == 1]
    summary = {
        "disclosure": DISCLOSURE,
        "period": "2025-11-01 to 2026-06-30",
        "total_spend": round(k[0], 2), "impressions": k[1], "clicks": k[2], "sessions": k[3],
        "leads": f[0], "mqls": f[1], "sqls": f[2], "opportunities": f[3], "customers": f[4],
        "won_revenue": round(f[5], 2),
        "ctr_pct": round(100 * k[2] / k[1], 2),
        "blended_cpl": round(k[0] / f[0], 2), "blended_cac": round(k[0] / f[4], 2),
        "lead_to_customer_pct": round(100 * f[4] / f[0], 2),
        "revenue_to_spend": round(f[5] / k[0], 2),
        "paid_cac": round(paid.spend.sum() / paid.customers.sum(), 2),
        "non_paid_revenue_share_pct": round(100 * ch[ch.is_paid == 0].won_revenue.sum() / ch.won_revenue.sum(), 1),
        "ending_mrr": round(mrr[0], 2), "active_customers_end": mrr[1],
        "top_revenue_channel": ch.sort_values("won_revenue").iloc[-1].channel_name,
        "lowest_paid_cac_channel": paid.sort_values("cac").iloc[0].channel_name,
    }
    (PROCESSED / "kpi_summary.json").write_text(json.dumps(summary, indent=2, default=int), encoding="utf-8")
    log.info(f"kpi_summary.json: {summary['leads']:,} leads, {summary['customers']} customers, "
             f"EUR {summary['won_revenue']:,.0f} won revenue")

    for f in RAW.glob("*.csv"):
        pd.read_csv(f).head(200).to_csv(SAMPLES / f"sample_{f.name}", index=False)
    log.info(f"samples written to data/samples/ (first 200 rows of each raw export)")


if __name__ == "__main__":
    main()
