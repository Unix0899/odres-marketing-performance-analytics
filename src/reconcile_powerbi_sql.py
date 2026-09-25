"""
Optional check (not part of run_pipeline.py): reconcile the Power BI measures with SQL.

Requires the PBIP open in Power BI Desktop. Connects READ-ONLY through Microsoft's Power BI Modeling MCP
server, evaluates the DAX measures, computes the same numbers from SQLite, and writes
docs/POWERBI_SQL_RECONCILIATION.md with PASS / FAIL for every comparison.

    python reconcile_powerbi_sql.py
"""
import csv
import io
import json
import sqlite3
from datetime import datetime

import pandas as pd

from common import DB, DISCLOSURE, DOCS
from validate_powerbi_model import McpClient, find_server

TOLERANCE = 0.005   # 0.5 % relative, or 0.01 absolute for small numbers

# measure -> SQL returning the same number on the whole period
GLOBAL = {
    "Total Spend": "SELECT SUM(spend) FROM fact_marketing_daily",
    "Impressions": "SELECT SUM(impressions) FROM fact_marketing_daily",
    "Clicks": "SELECT SUM(clicks) FROM fact_marketing_daily",
    "Sessions": "SELECT SUM(sessions) FROM fact_marketing_daily",
    "CTR": "SELECT 1.0*SUM(clicks)/SUM(impressions) FROM fact_marketing_daily",
    "CPC": "SELECT SUM(spend)/SUM(clicks) FROM fact_marketing_daily",
    "Leads": "SELECT COUNT(*) FROM fact_leads",
    "MQLs": "SELECT SUM(is_mql) FROM fact_leads",
    "SQLs": "SELECT SUM(is_sql) FROM fact_leads",
    "Avg Lead Score": "SELECT AVG(lead_score) FROM fact_leads",
    "Opportunities": "SELECT COUNT(*) FROM fact_opportunities",
    "Customers": "SELECT SUM(is_won) FROM fact_opportunities",
    "Session to Lead %": "SELECT (SELECT 1.0*COUNT(*) FROM fact_leads)/(SELECT SUM(sessions) FROM fact_marketing_daily)",
    "Lead to MQL %": "SELECT 1.0*SUM(is_mql)/COUNT(*) FROM fact_leads",
    "MQL to SQL %": "SELECT 1.0*SUM(is_sql)/SUM(is_mql) FROM fact_leads",
    "SQL to Customer %": "SELECT (SELECT 1.0*SUM(is_won) FROM fact_opportunities)/(SELECT SUM(is_sql) FROM fact_leads)",
    "Lead to Customer %": "SELECT (SELECT 1.0*SUM(is_won) FROM fact_opportunities)/(SELECT COUNT(*) FROM fact_leads)",
    "CPL": "SELECT (SELECT SUM(spend) FROM fact_marketing_daily)/(SELECT COUNT(*) FROM fact_leads)",
    "CAC": "SELECT (SELECT SUM(spend) FROM fact_marketing_daily)/(SELECT SUM(is_won) FROM fact_opportunities)",
    "Won Revenue": "SELECT SUM(won_value) FROM fact_opportunities WHERE is_won = 1",
    "Revenue / Spend": "SELECT (SELECT SUM(won_value) FROM fact_opportunities WHERE is_won=1)/(SELECT SUM(spend) FROM fact_marketing_daily)",
    "Average Deal Value": "SELECT AVG(won_value) FROM fact_opportunities WHERE is_won = 1",
    "Average Sales Cycle": "SELECT AVG(sales_cycle_days) FROM fact_opportunities WHERE is_won = 1",
    "Win Rate": "SELECT 1.0*SUM(is_won)/COUNT(*) FROM fact_opportunities WHERE status IN ('Won','Lost')",
    "Open Pipeline": "SELECT SUM(expected_value) FROM fact_opportunities WHERE status = 'Open'",
    "Lost Value": "SELECT SUM(expected_value) FROM fact_opportunities WHERE status = 'Lost'",
    "MRR": "SELECT SUM(mrr) FROM fact_customer_monthly WHERE is_active = 1",
    "MRR (end of period)": "SELECT SUM(mrr) FROM fact_customer_monthly WHERE is_active = 1 "
                           "AND year_month = (SELECT MAX(year_month) FROM fact_customer_monthly)",
    "Active Customers": "SELECT COUNT(DISTINCT customer_id) FROM fact_customer_monthly WHERE is_active = 1",
    "Churned Customers": "SELECT SUM(is_churned) FROM fact_customer_monthly",
    "Churn Rate": "SELECT 1.0*(SELECT SUM(is_churned) FROM fact_customer_monthly)/((SELECT COUNT(DISTINCT customer_id) "
                  "FROM fact_customer_monthly WHERE is_active=1)+(SELECT SUM(is_churned) FROM fact_customer_monthly))",
    "Issues Found (raw)": None, "Blocking Errors Left": None, "Documented Warnings": None,
    "Rows Loaded": None, "Rows Removed": None,
}
DQ_EXPECTED_FROM = "data/processed"

BY_CHANNEL = ["Leads", "Customers", "Won Revenue", "CPL", "CAC", "Win Rate"]
CHANNEL_SQL = {
    "Leads": "leads", "Customers": "customers", "Won Revenue": "won_revenue", "CPL": "cpl", "CAC": "cac",
}


def parse_number(text):
    text = text.strip().strip('"')
    if text == "":
        return None
    return float(text.replace(" ", "").replace(" ", "").replace(",", "."))


def dax(client, query):
    reply = client.request("tools/call", {"name": "dax_query_operations",
                                          "arguments": {"request": {"operation": "Execute", "query": query}}})
    parts = reply["result"]["content"]
    status = json.loads(parts[0]["text"])
    if not status.get("success"):
        raise RuntimeError(status.get("message"))
    table = next(p["resource"]["text"] for p in parts if p.get("type") == "resource")
    return list(csv.reader(io.StringIO(table)))


def close_enough(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= max(0.01, TOLERANCE * abs(b))


def main():
    client = McpClient(find_server())
    client.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                  "clientInfo": {"name": "odres-reconcile", "version": "1.0"}})
    client.request("notifications/initialized", notify=True)
    instances = client.tool("connection_operations", {"operation": "ListLocalInstances"})["data"]
    target = [i for i in instances if "ODRES" in i["parentWindowTitle"]]
    if not target:
        raise SystemExit("Open powerbi/ODRES_Marketing_Analytics/ODRES_Marketing_Analytics.pbip in Power BI Desktop first")
    client.tool("connection_operations", {"operation": "Connect", "connectionString": target[0]["connectionString"]})

    db = sqlite3.connect(DB)
    one = lambda sql: db.execute(sql).fetchone()[0]  # noqa: E731
    dq = pd.read_csv(DB.parents[1] / "data" / "processed" / "data_quality_results.csv")
    rc = pd.read_csv(DB.parents[1] / "data" / "processed" / "row_counts.csv")
    expected = {m: one(sql) for m, sql in GLOBAL.items() if sql}
    expected.update({"Issues Found (raw)": dq.raw.sum(),
                     "Blocking Errors Left": dq[dq.severity == "BLOCKING"].clean.sum(),
                     "Documented Warnings": dq[dq.severity == "WARNING"].clean.sum(),
                     "Rows Loaded": rc.clean_rows.sum(), "Rows Removed": rc.removed.sum()})

    rows = []
    measures = list(GLOBAL)
    query = "EVALUATE ROW(" + ", ".join(f'"{m}", [{m}]' for m in measures) + ")"
    values = dax(client, query)[1]
    for m, v in zip(measures, values):
        got, exp = parse_number(v), expected[m]
        rows.append(("Whole period", m, got, exp, close_enough(got, exp)))

    ch = pd.read_sql_query("SELECT * FROM vw_channel_performance", db)
    q = ("EVALUATE SUMMARIZECOLUMNS(DimChannel[channel_name], "
         + ", ".join(f'"{m}", [{m}]' for m in BY_CHANNEL) + ")")
    table = dax(client, q)
    for r in table[1:]:
        name = r[0]
        sql_row = ch[ch.channel_name == name].iloc[0]
        closed = one(f"SELECT COUNT(*) FROM fact_opportunities o JOIN dim_channel c USING(channel_id) "
                     f"WHERE c.channel_name = '{name}' AND status IN ('Won','Lost')")
        exp_map = {m: sql_row[c] for m, c in CHANNEL_SQL.items()}
        exp_map["Win Rate"] = sql_row.customers / closed if closed else None
        for m, v in zip(BY_CHANNEL, r[1:]):
            exp = exp_map[m]
            exp = None if exp is None or pd.isna(exp) else float(exp)
            got = parse_number(v)
            rows.append((name, m, got, exp, close_enough(got, exp)))

    mm = pd.read_sql_query("SELECT year_month, leads, won_revenue, mom_leads, mom_revenue FROM vw_monthly_management", db)
    table = dax(client, 'EVALUATE SUMMARIZECOLUMNS(DimDate[year_month], "Leads", [Leads], "MoM Leads %", [MoM Leads %],'
                        ' "MoM Revenue %", [MoM Revenue %])')
    got_by_month = {r[0]: r for r in table[1:]}
    for s in mm.itertuples():
        r = got_by_month.get(s.year_month)
        if r is None:
            continue
        for label, got, exp in [("Leads", r[1], s.leads), ("MoM Leads %", r[2], s.mom_leads),
                                ("MoM Revenue %", r[3], s.mom_revenue)]:
            exp = None if pd.isna(exp) else float(exp)
            got = parse_number(got)
            rows.append((s.year_month, label, got, exp, close_enough(got, exp)))
    client.proc.kill()

    passed = sum(r[4] for r in rows)
    fmt = lambda v: "blank" if v is None else (f"{v:,.4f}" if abs(v) < 10 else f"{v:,.2f}")  # noqa: E731
    lines = ["# Power BI ↔ SQL reconciliation", "", f"> {DISCLOSURE}", "",
             f"Run on {datetime.now():%d/%m/%Y %H:%M} with `src/reconcile_powerbi_sql.py`: the PBIP open in Power BI "
             "Desktop, queried **read-only** through Microsoft's Power BI Modeling MCP server, compared with the same "
             "numbers computed in SQLite.", "",
             f"**Result: {passed}/{len(rows)} comparisons PASS** (tolerance 0.5 %).", "",
             "| Scope | Measure | Power BI (DAX) | SQL | Status |", "|---|---|---:|---:|---|"]
    lines += [f"| {s} | {m} | {fmt(g)} | {fmt(e)} | {'PASS' if ok else 'FAIL'} |" for s, m, g, e, ok in rows]
    (DOCS / "POWERBI_SQL_RECONCILIATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{passed}/{len(rows)} PASS")
    for s, m, g, e, ok in rows:
        if not ok:
            print(f"FAIL  {s:<16} {m:<22} DAX={g}  SQL={e}")


if __name__ == "__main__":
    main()
