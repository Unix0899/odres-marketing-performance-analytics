"""
Data-quality validation, run on the RAW exports and on the CLEAN layer with the same rules.

Writes:
  data/processed/data_quality_results.csv   one row per check and layer
  docs/DATA_QUALITY_REPORT.md               before / after report
Exit code 1 if any blocking check still fails on the clean layer.
"""
import json
import sys
from datetime import datetime

import pandas as pd

from common import (CLEAN, COMPANY_SIZES, DISCLOSURE, DOCS, PROCESSED, RAW, REF, REGION_SYNONYMS, STAGES,
                    get_logger, norm)

log = get_logger("validate")

# check id, table, description, severity (BLOCKING = must be 0 after cleaning, WARNING = documented)
CHECKS = [
    ("DQ01", "marketing_daily", "Exact duplicate rows", "BLOCKING"),
    ("DQ02", "marketing_daily", "Channel label not in reference (exact match)", "BLOCKING"),
    ("DQ03", "marketing_daily", "Invalid or empty date", "BLOCKING"),
    ("DQ04", "marketing_daily", "Negative spend (spend >= 0)", "BLOCKING"),
    ("DQ05", "marketing_daily", "Spend outlier (> 10x campaign median)", "BLOCKING"),
    ("DQ06", "marketing_daily", "Clicks greater than impressions", "BLOCKING"),
    ("DQ07", "leads", "Missing lead_id (critical ID)", "BLOCKING"),
    ("DQ08", "leads", "Duplicate lead_id", "BLOCKING"),
    ("DQ09", "leads", "Unknown campaign", "WARNING"),
    ("DQ10", "leads", "Region label not in reference", "BLOCKING"),
    ("DQ11", "leads", "Company size not in 1-9 / 10-49 / 50+", "BLOCKING"),
    ("DQ12", "leads", "Lead score outside 0-100", "BLOCKING"),
    ("DQ13", "leads", "Lead score missing", "WARNING"),
    ("DQ14", "leads", "SQL = 1 while MQL = 0", "BLOCKING"),
    ("DQ15", "opportunities", "Duplicate opportunity rows", "BLOCKING"),
    ("DQ16", "opportunities", "Orphan opportunity (lead unknown)", "BLOCKING"),
    ("DQ17", "opportunities", "Stage not in Won / Lost / Open", "BLOCKING"),
    ("DQ18", "opportunities", "Won opportunity without value (> 0)", "BLOCKING"),
    ("DQ19", "opportunities", "Negative won value", "BLOCKING"),
    ("DQ20", "opportunities", "Close date before creation date", "BLOCKING"),
    ("DQ21", "customers", "Duplicate customer_id", "BLOCKING"),
    ("DQ22", "customers", "Customer without a Won opportunity", "BLOCKING"),
]


def count_raw() -> dict:
    ref_ch = set(pd.read_csv(REF / "channels.csv").channel_name)
    ref_cp = {norm(x) for x in pd.read_csv(REF / "campaigns.csv").campaign_name}
    ref_rg = set(pd.read_csv(REF / "regions.csv").region_name)
    m = pd.read_csv(RAW / "ads_platform_export.csv", dtype={"date": "string"})
    l = pd.read_csv(RAW / "crm_leads_export.csv", dtype={"lead_id": "Int64"})
    o = pd.read_csv(RAW / "crm_opportunities_export.csv", dtype={"closed_at": "string"})
    c = pd.read_csv(RAW / "billing_customers_export.csv")
    med = m.groupby(m.campaign).spend.transform(lambda s: s[s > 0].median())
    created, closed = pd.to_datetime(o.created_at, errors="coerce"), pd.to_datetime(o.closed_at, errors="coerce")
    won_ids = set(o.loc[o.stage.str.title() == "Won", "opportunity_id"])
    return {
        "DQ01": m.duplicated().sum(), "DQ02": (~m.channel.isin(ref_ch)).sum(),
        "DQ03": pd.to_datetime(m.date, format="%Y-%m-%d", errors="coerce").isna().sum(),
        "DQ04": (m.spend < 0).sum(), "DQ05": ((m.spend > 10 * med) & (med > 0)).sum(),
        "DQ06": (m.clicks > m.impressions).sum(),
        "DQ07": l.lead_id.isna().sum(), "DQ08": l.lead_id.dropna().duplicated().sum(),
        "DQ09": (~l.campaign.map(norm).isin(ref_cp)).sum(), "DQ10": (~l.region.isin(ref_rg)).sum(),
        "DQ11": (~l.company_size.isin(COMPANY_SIZES)).sum(),
        "DQ12": (l.lead_score.notna() & ~l.lead_score.between(0, 100)).sum(),
        "DQ13": l.lead_score.isna().sum(), "DQ14": ((l.is_sql == 1) & (l.is_mql == 0)).sum(),
        "DQ15": o.duplicated().sum(), "DQ16": (~o.lead_id.isin(l.lead_id)).sum(),
        "DQ17": (~o.stage.isin(STAGES)).sum(),
        "DQ18": ((o.stage.str.title() == "Won") & (o.won_value.fillna(0) <= 0)).sum(),
        "DQ19": (o.won_value < 0).sum(), "DQ20": (closed < created).sum(),
        "DQ21": c.customer_id.duplicated().sum(), "DQ22": (~c.opportunity_id.isin(won_ids)).sum(),
    }


def count_clean() -> dict:
    m = pd.read_csv(CLEAN / "fact_marketing_daily.csv")
    l = pd.read_csv(CLEAN / "fact_leads.csv", dtype={"lead_score": "Int64", "campaign_id": "Int64"})
    o = pd.read_csv(CLEAN / "fact_opportunities.csv")
    c = pd.read_csv(CLEAN / "dim_customer.csv")
    d = pd.read_csv(CLEAN / "dim_date.csv")
    ch = pd.read_csv(CLEAN / "dim_channel.csv")
    rg = pd.read_csv(CLEAN / "dim_region.csv")
    med = m.groupby("campaign_id").spend.transform(lambda s: s[s > 0].median())
    return {
        "DQ01": m.duplicated().sum(), "DQ02": (~m.channel_id.isin(ch.channel_id)).sum(),
        "DQ03": (~m.date_key.isin(d.date_key)).sum(), "DQ04": (m.spend < 0).sum(),
        "DQ05": ((m.spend > 10 * med) & (med > 0)).sum(), "DQ06": (m.clicks > m.impressions).sum(),
        "DQ07": l.lead_id.isna().sum(), "DQ08": l.lead_id.duplicated().sum(),
        "DQ09": l.campaign_id.isna().sum(), "DQ10": (~l.region_id.isin(rg.region_id)).sum(),
        "DQ11": (~l.company_size.isin(COMPANY_SIZES)).sum(),
        "DQ12": (l.lead_score.notna() & ~l.lead_score.fillna(0).between(0, 100)).sum(),
        "DQ13": l.lead_score.isna().sum(), "DQ14": ((l.is_sql == 1) & (l.is_mql == 0)).sum(),
        "DQ15": o.duplicated().sum(), "DQ16": (~o.lead_id.isin(l.lead_id)).sum(),
        "DQ17": (~o.status.isin(STAGES)).sum(), "DQ18": ((o.status == "Won") & (o.won_value <= 0)).sum(),
        "DQ19": (o.won_value < 0).sum(), "DQ20": (o.close_date_key < o.created_date_key).sum(),
        "DQ21": c.customer_id.duplicated().sum(),
        "DQ22": (~c.opportunity_id.isin(o.loc[o.is_won == 1, "opportunity_id"])).sum(),
    }


def row_counts() -> pd.DataFrame:
    pairs = [("Marketing daily", "ads_platform_export.csv", "fact_marketing_daily.csv"),
             ("Leads", "crm_leads_export.csv", "fact_leads.csv"),
             ("Opportunities", "crm_opportunities_export.csv", "fact_opportunities.csv"),
             ("Customers", "billing_customers_export.csv", "dim_customer.csv"),
             ("Customer-months", "billing_mrr_monthly_export.csv", "fact_customer_monthly.csv")]
    rows = []
    for name, r, c in pairs:
        nr, nc = len(pd.read_csv(RAW / r)), len(pd.read_csv(CLEAN / c))
        rows.append({"table": name, "raw_rows": nr, "clean_rows": nc, "removed": nr - nc})
    return pd.DataFrame(rows)


def write_report(res: pd.DataFrame, counts: pd.DataFrame):
    injected = json.loads((RAW / "_injected_anomalies.json").read_text(encoding="utf-8"))
    cleaning = pd.read_csv(PROCESSED / "cleaning_log.csv")
    blocking_left = res[(res.severity == "BLOCKING") & (res.clean > 0)]
    lines = [
        "# Data quality report", "", f"> {DISCLOSURE}", "",
        f"Generated by `src/validate_data.py` on {datetime.now():%d/%m/%Y %H:%M}. Same rules on both layers.", "",
        "## Summary", "",
        f"- **{int(res.raw.sum()):,}** issues detected in the raw exports across {int((res.raw > 0).sum())} checks.",
        f"- **{int(res[res.severity == 'BLOCKING'].clean.sum())}** blocking issues left after cleaning "
        f"({'PASS' if blocking_left.empty else 'FAIL'}).",
        f"- Warnings kept on purpose and documented: "
        + ", ".join(f"{r.description.lower()} ({int(r.clean)})" for r in res[(res.severity == 'WARNING') & (res.clean > 0)].itertuples()),
        "", "## Rows before / after cleaning", "", "| Table | Raw rows | Clean rows | Removed |", "|---|---:|---:|---:|"]
    lines += [f"| {r.table} | {r.raw_rows:,} | {r.clean_rows:,} | {r.removed:,} |" for r in counts.itertuples()]
    lines += ["", "## Checks", "", "| ID | Table | Check | Severity | Raw | Clean | Status |", "|---|---|---|---|---:|---:|---|"]
    for r in res.itertuples():
        status = "PASS" if r.clean == 0 else ("WARN" if r.severity == "WARNING" else "FAIL")
        lines.append(f"| {r.check_id} | {r.table} | {r.description} | {r.severity} | {int(r.raw)} | {int(r.clean)} | {status} |")
    lines += ["", "## Cleaning rules applied (`data/processed/cleaning_log.csv`)", "",
              "| Rule | Table | Rows | Action |", "|---|---|---:|---|"]
    lines += [f"| {r.rule} | {r.table} | {r.rows_affected} | {r.action} |" for r in cleaning.itertuples()]
    lines += ["", "## Anomalies deliberately injected by the generator", "",
              "The raw exports contain controlled anomalies (`data/raw/_injected_anomalies.json`) so that the pipeline "
              "has something real to detect. Small differences with the counts above are expected: an anomaly can sit "
              "on a row that another rule already removed (for example a duplicate row, or a lead without ID whose "
              "opportunity then becomes an orphan).", "", "| Anomaly | Injected |", "|---|---:|"]
    lines += [f"| {k.replace('_', ' ')} | {v} |" for k, v in injected.items()]
    lines += ["", "## Why the warnings are kept", "",
              "- **Missing lead score**: the score is unknown, not zero. Imputing it would bias lead-quality averages, "
              "so these leads stay in volume KPIs and are excluded from score averages. The count goes *up* after "
              "cleaning because out-of-range scores (DQ12) are set to NULL rather than guessed.",
              "- **Unknown campaign**: the lead is real and its channel is known; only the campaign tag is wrong. "
              "It is kept (campaign = NULL, shown as *Unassigned*) so channel totals stay complete.", ""]
    (DOCS / "DATA_QUALITY_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    raw, clean = count_raw(), count_clean()
    res = pd.DataFrame(CHECKS, columns=["check_id", "table", "description", "severity"])
    res["raw"] = res.check_id.map(raw).astype(int)
    res["clean"] = res.check_id.map(clean).astype(int)
    res.to_csv(PROCESSED / "data_quality_results.csv", index=False)
    counts = row_counts()
    counts.to_csv(PROCESSED / "row_counts.csv", index=False)
    write_report(res, counts)
    for r in res.itertuples():
        status = "PASS" if r.clean == 0 else ("WARN" if r.severity == "WARNING" else "FAIL")
        log.info(f"[{status}] {r.check_id} {r.description:<48} raw={r.raw:<4} clean={r.clean}")
    failed = res[(res.severity == "BLOCKING") & (res.clean > 0)]
    if not failed.empty:
        log.error(f"{len(failed)} blocking check(s) failed on the clean layer")
        sys.exit(1)
    log.info("clean layer: all blocking checks PASS")


if __name__ == "__main__":
    main()
