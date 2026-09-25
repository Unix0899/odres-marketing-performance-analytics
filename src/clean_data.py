"""
Clean layer: data/raw (tool exports) -> data/clean (typed, keyed, conformed tables).

Every correction is a documented business rule and is logged in
data/processed/cleaning_log.csv (rule, table, rows affected, action).
"""
import numpy as np
import pandas as pd

from common import CLEAN, COMPANY_SIZES, PROCESSED, RAW, REF, REGION_SYNONYMS, get_logger, norm

log = get_logger("clean")
LOG_ROWS = []


def record(rule, table, rows, action):
    LOG_ROWS.append({"rule": rule, "table": table, "rows_affected": int(rows), "action": action})
    log.info(f"{rule:<5} {table:<22} {int(rows):>5} rows | {action}")


# --------------------------------------------------------------------------- reference data
channels = pd.read_csv(REF / "channels.csv")
campaigns = pd.read_csv(REF / "campaigns.csv")
regions = pd.read_csv(REF / "regions.csv")
CHANNEL_ID = {norm(n): i for n, i in zip(channels.channel_name, channels.channel_id)}
CAMPAIGN_ID = {norm(n): i for n, i in zip(campaigns.campaign_name, campaigns.campaign_id)}
REGION_ID = {norm(n): i for n, i in zip(regions.region_name, regions.region_id)}
REGION_ID.update({k: REGION_ID[norm(v)] for k, v in REGION_SYNONYMS.items()})


def date_key(series: pd.Series) -> pd.Series:
    return series.dt.strftime("%Y%m%d").astype("Int64")


# --------------------------------------------------------------------------- marketing
def clean_marketing() -> pd.DataFrame:
    df = pd.read_csv(RAW / "ads_platform_export.csv", dtype={"date": "string"})
    n0 = len(df)

    dup = df.duplicated()
    record("M1", "marketing_daily", dup.sum(), "exact duplicate rows removed")
    df = df[~dup].copy()

    std = df.channel.map(norm).map(CHANNEL_ID)
    variants = (~df.channel.isin(channels.channel_name)).sum()
    record("M2", "marketing_daily", variants, "channel labels trimmed and matched to reference (case-insensitive)")
    df["channel_id"] = std
    df["campaign_id"] = df.campaign.map(norm).map(CAMPAIGN_ID)

    parsed = pd.to_datetime(df.date, format="%Y-%m-%d", errors="coerce")
    bad = parsed.isna()
    record("M3", "marketing_daily", bad.sum(), "invalid or empty dates dropped (row cannot be attributed to a day)")
    df, parsed = df[~bad].copy(), parsed[~bad]
    df["date_key"] = date_key(parsed)

    neg = df.spend < 0
    record("M4", "marketing_daily", neg.sum(), "negative spend treated as sign error (abs value)")
    df.loc[neg, "spend"] = df.loc[neg, "spend"].abs()

    med = df.groupby("campaign_id").spend.transform(lambda s: s[s > 0].median())
    outlier = (df.spend > 10 * med) & (med > 0)
    record("M5", "marketing_daily", outlier.sum(), "spend > 10x campaign median replaced by campaign median")
    df.loc[outlier, "spend"] = med[outlier].round(2)

    impossible = df.clicks > df.impressions
    record("M6", "marketing_daily", impossible.sum(), "clicks > impressions: clicks reset to analytics sessions")
    df.loc[impossible, "clicks"] = df.loc[impossible, "sessions"]

    key_dup = df.duplicated(["date_key", "campaign_id"])
    record("M7", "marketing_daily", key_dup.sum(), "remaining duplicates on (date, campaign) removed")
    df = df[~key_dup]

    out = df[["date_key", "campaign_id", "channel_id", "impressions", "clicks", "sessions", "spend"]]
    log.info(f"marketing_daily: {n0:,} raw -> {len(out):,} clean")
    return out.sort_values(["date_key", "campaign_id"]).reset_index(drop=True)


# --------------------------------------------------------------------------- leads
def clean_leads() -> pd.DataFrame:
    df = pd.read_csv(RAW / "crm_leads_export.csv", dtype={"lead_id": "Int64"})
    n0 = len(df)

    miss = df.lead_id.isna()
    record("L1", "leads", miss.sum(), "rows without lead_id dropped (cannot be linked)")
    df = df[~miss].copy()

    dup = df.duplicated("lead_id")
    record("L2", "leads", dup.sum(), "duplicate lead_id removed (first occurrence kept)")
    df = df[~dup].copy()

    df["channel_id"] = df.channel.map(norm).map(CHANNEL_ID)
    df["campaign_id"] = df.campaign.map(norm).map(CAMPAIGN_ID).astype("Int64")
    unknown = df.campaign_id.isna()
    record("L3", "leads", unknown.sum(), "unknown campaign -> campaign_id NULL, lead kept under its channel")

    matched = df.region.isin(regions.region_name)
    df["region_id"] = df.region.map(norm).map(REGION_ID).astype("Int64")
    record("L4", "leads", (~matched).sum(), "region labels (FR/NL/casing) mapped to reference region")

    size = df.company_size.str.replace(" ", "", regex=False)
    record("L5", "leads", (size != df.company_size).sum(), "company_size format normalised (e.g. '10 - 49' -> '10-49')")
    df["company_size"] = size

    oor = df.lead_score.notna() & ~df.lead_score.between(0, 100)
    record("L6", "leads", oor.sum(), "lead_score outside 0-100 set to NULL (unknown)")
    df.loc[oor, "lead_score"] = np.nan
    record("L6b", "leads", df.lead_score.isna().sum(), "lead_score NULL kept as unknown (excluded from averages, not imputed)")

    sql_no_mql = (df.is_sql == 1) & (df.is_mql == 0)
    record("L7", "leads", sql_no_mql.sum(), "SQL without MQL: is_mql set to 1 (an SQL has passed the MQL stage)")
    df.loc[sql_no_mql, "is_mql"] = 1

    created = pd.to_datetime(df.created_at, errors="coerce")
    df["created_date_key"] = date_key(created)
    df["lead_score"] = df.lead_score.astype("Int64")
    out = df[["lead_id", "created_date_key", "channel_id", "campaign_id", "region_id", "company_size",
              "business_type", "lead_score", "is_mql", "is_sql"]]
    log.info(f"leads: {n0:,} raw -> {len(out):,} clean")
    return out.sort_values("lead_id").reset_index(drop=True)


# --------------------------------------------------------------------------- opportunities
def clean_opportunities(leads: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_csv(RAW / "crm_opportunities_export.csv", dtype={"closed_at": "string"})
    n0 = len(df)

    dup = df.duplicated()
    record("O1", "opportunities", dup.sum(), "exact duplicate rows removed")
    df = df[~dup].copy()

    orphan = ~df.lead_id.isin(leads.lead_id)
    record("O2", "opportunities", orphan.sum(), "orphan opportunities (lead not in CRM) removed")
    df = df[~orphan].copy()

    status = df.stage.str.strip().str.title()
    record("O3", "opportunities", (status != df.stage).sum(), "stage casing standardised to Won / Lost / Open")
    df["status"] = status

    won_zero = (df.status == "Won") & (df.won_value.fillna(0) <= 0)
    record("O4", "opportunities", won_zero.sum(), "Won without value: won_value = expected_value, flagged")
    df["value_imputed"] = won_zero.astype(int)
    df.loc[won_zero, "won_value"] = df.loc[won_zero, "expected_value"]

    created = pd.to_datetime(df.created_at, errors="coerce")
    closed = pd.to_datetime(df.closed_at, errors="coerce")
    inverted = closed < created
    record("O5", "opportunities", inverted.sum(), "close date before creation: close date set NULL (cycle unknown)")
    closed[inverted] = pd.NaT

    df["created_date_key"] = date_key(created)
    df["close_date_key"] = date_key(closed)
    df["sales_cycle_days"] = (closed - created).dt.days.astype("Int64")
    df["is_won"] = (df.status == "Won").astype(int)

    df = df.merge(leads[["lead_id", "channel_id", "campaign_id", "region_id", "company_size"]], on="lead_id")
    out = df[["opportunity_id", "lead_id", "created_date_key", "close_date_key", "channel_id", "campaign_id",
              "region_id", "company_size", "plan", "sites", "status", "is_won", "expected_value", "won_value",
              "sales_cycle_days", "value_imputed"]]
    log.info(f"opportunities: {n0:,} raw -> {len(out):,} clean")
    return out.sort_values("opportunity_id").reset_index(drop=True)


# --------------------------------------------------------------------------- customers
def clean_customers(opps: pd.DataFrame, leads: pd.DataFrame):
    df = pd.read_csv(RAW / "billing_customers_export.csv")
    n0 = len(df)
    dup = df.duplicated("customer_id")
    record("C1", "customers", dup.sum(), "duplicate customer_id removed")
    df = df[~dup].copy()

    no_won = ~df.opportunity_id.isin(opps.loc[opps.is_won == 1, "opportunity_id"])
    record("C2", "customers", no_won.sum(), "customers without a Won opportunity removed")
    df = df[~no_won]

    df = df.merge(opps[["opportunity_id", "lead_id", "channel_id", "campaign_id", "region_id", "company_size"]],
                  on="opportunity_id").merge(leads[["lead_id", "business_type"]], on="lead_id")
    df["acquisition_date_key"] = date_key(pd.to_datetime(df.start_date))
    cust = df[["customer_id", "opportunity_id", "lead_id", "acquisition_date_key", "channel_id", "campaign_id",
               "region_id", "company_size", "business_type", "plan", "starting_mrr"]]

    m = pd.read_csv(RAW / "billing_mrr_monthly_export.csv")
    m = m[m.customer_id.isin(cust.customer_id)].drop_duplicates(["customer_id", "year_month"])
    m["month_key"] = (m.year_month.str.replace("-", "") + "01").astype(int)
    m["is_active"] = (m.status == "active").astype(int)
    m["is_churned"] = (m.status == "churned").astype(int)
    monthly = m[["customer_id", "year_month", "month_key", "mrr", "is_active", "is_churned"]]
    log.info(f"customers: {n0:,} raw -> {len(cust):,} clean | customer-months: {len(monthly):,}")
    return cust.sort_values("customer_id").reset_index(drop=True), monthly.reset_index(drop=True)


def build_dim_date() -> pd.DataFrame:
    d = pd.DataFrame({"date": pd.date_range("2025-10-01", "2026-07-31")})
    return pd.DataFrame({
        "date_key": date_key(d.date), "date": d.date.dt.strftime("%Y-%m-%d"), "year": d.date.dt.year,
        "quarter": "Q" + d.date.dt.quarter.astype(str), "month": d.date.dt.month,
        "month_name": d.date.dt.strftime("%b"), "year_month": d.date.dt.strftime("%Y-%m"),
        "week": d.date.dt.isocalendar().week.astype(int), "day_of_week": d.date.dt.day_name(),
        "is_weekend": (d.date.dt.dayofweek >= 5).astype(int)})


def main():
    CLEAN.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    mkt = clean_marketing()
    leads = clean_leads()
    opps = clean_opportunities(leads)
    cust, monthly = clean_customers(opps, leads)
    tables = {"dim_date": build_dim_date(), "dim_channel": channels, "dim_campaign": campaigns,
              "dim_region": regions, "dim_customer": cust, "fact_marketing_daily": mkt, "fact_leads": leads,
              "fact_opportunities": opps, "fact_customer_monthly": monthly}
    for name, df in tables.items():
        df.to_csv(CLEAN / f"{name}.csv", index=False)
    pd.DataFrame(LOG_ROWS).to_csv(PROCESSED / "cleaning_log.csv", index=False)
    log.info(f"clean layer written: {len(tables)} tables -> {CLEAN.relative_to(CLEAN.parents[1])}")


if __name__ == "__main__":
    main()
