"""
Synthetic data generator — ODRES marketing & commercial performance (portfolio reconstruction).

Professional context based on a real ODRES Group experience.
Public technical reconstruction using synthetic data: NO real ODRES client, prospect,
campaign result, price or revenue is used. Plans and prices below are fictional.

Simulated business: a Belgian subscription ERP (restaurants, shops and other businesses manage their
establishment through several applications); the dataset focuses on its hospitality
businesses (restaurants, bars, snacks, cafés, hotels), Nov 2025 → Jun 2026.

Outputs (deterministic, seed below):
  data/reference/  channels, campaigns, regions (master data)
  data/raw/        exports as they would come out of source tools:
                   ads_platform_export.csv, crm_leads_export.csv,
                   crm_opportunities_export.csv, billing_customers_export.csv,
                   billing_mrr_monthly_export.csv
  data/raw/_injected_anomalies.json   what was deliberately broken, for QA
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20260924
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
REF = ROOT / "data" / "reference"
START, END = pd.Timestamp("2025-11-01"), pd.Timestamp("2026-06-30")

rng = np.random.default_rng(SEED)

# --------------------------------------------------------------------------- reference data
CHANNELS = pd.DataFrame([
    # id, name, group, paid, ctr, cpc, session_to_lead, quality, base_score
    (1, "Google Ads",     "Paid Search", 1, 0.045, 2.10, 0.034, 1.00, 52),
    (2, "LinkedIn Ads",   "Paid Social", 1, 0.007, 6.80, 0.036, 1.35, 63),
    (3, "Meta Ads",       "Paid Social", 1, 0.012, 0.75, 0.046, 0.62, 38),
    (4, "Organic Search", "Organic",     0, 0.032, 0.00, 0.017, 1.10, 56),
    (5, "Direct",         "Direct",      0, 1.000, 0.00, 0.021, 1.15, 58),
    (6, "Email",          "Owned",       0, 0.038, 0.00, 0.052, 1.20, 60),
    (7, "Referral",       "Referral",    0, 1.000, 0.00, 0.066, 1.28, 66),
], columns=["channel_id", "channel_name", "channel_group", "is_paid",
            "p_ctr", "p_cpc", "p_s2l", "p_quality", "p_score"])

CAMPAIGNS = pd.DataFrame([
    # id, name, channel, objective, start, daily_budget_or_sessions, cost_mult, quality_mult
    (1,  "High Intent Search",    1, "Conversion",   "2025-11-01", 85, 1.10, 1.15),
    (2,  "Competitor Search",     1, "Conversion",   "2025-11-01", 45, 1.45, 0.85),
    (3,  "Restaurant Operations", 1, "Conversion",   "2025-11-15", 40, 1.00, 1.05),
    (4,  "Decision Makers",       2, "Lead gen",     "2025-11-01", 55, 1.10, 1.25),
    (5,  "Operations Leaders",    2, "Lead gen",     "2025-12-01", 35, 1.00, 1.10),
    (6,  "SMB Growth",            2, "Lead gen",     "2026-01-15", 30, 0.90, 0.85),
    (7,  "Awareness Video",       3, "Awareness",    "2025-11-01", 55, 0.80, 0.55),
    (8,  "Lead Magnet",           3, "Lead gen",     "2025-11-01", 30, 1.00, 0.85),
    (9,  "Retargeting",           3, "Conversion",   "2026-01-15", 20, 1.20, 1.35),
    (10, "SEO Product Pages",     4, "Organic",      "2025-11-01", 120, 1.0, 1.10),
    (11, "SEO Guides",            4, "Organic",      "2025-11-01", 110, 1.0, 0.85),
    (12, "SEO Comparison",        4, "Organic",      "2026-02-01", 45, 1.0, 1.30),
    (13, "Brand Direct",          5, "Direct",       "2025-11-01", 95, 1.0, 1.10),
    (14, "Returning Visitors",    5, "Direct",       "2025-11-01", 45, 1.0, 1.15),
    (15, "Demo Page Direct",      5, "Direct",       "2025-12-01", 25, 1.0, 1.40),
    (16, "Newsletter",            6, "Nurture",      "2025-11-01", 30, 1.0, 1.05),
    (17, "Lead Nurture",          6, "Nurture",      "2025-12-01", 22, 1.0, 1.30),
    (18, "Reactivation",          6, "Nurture",      "2026-02-01", 14, 1.0, 0.85),
    (19, "Partner Network",       7, "Partnership",  "2025-11-01", 16, 1.0, 1.25),
    (20, "Customer Referral",     7, "Partnership",  "2025-11-01", 12, 1.0, 1.35),
    (21, "Industry Events",       7, "Events",       "2026-02-15", 9,  1.0, 1.20),
], columns=["campaign_id", "campaign_name", "channel_id", "objective", "start_date",
            "p_volume", "p_cost_mult", "p_quality_mult"])

REGIONS = pd.DataFrame([
    (1, "Brussels", "Brussels-Capital", 0.21), (2, "Antwerp", "Flanders", 0.15),
    (3, "East Flanders", "Flanders", 0.12), (4, "Flemish Brabant", "Flanders", 0.10),
    (5, "Hainaut", "Wallonia", 0.12), (6, "Liège", "Wallonia", 0.12),
    (7, "Walloon Brabant", "Wallonia", 0.10), (8, "Namur", "Wallonia", 0.08),
], columns=["region_id", "region_name", "region_group", "p_weight"])

# Fictional plans (NOT ODRES prices): monthly price by plan
PLANS = {"Starter": 49.0, "Pro": 119.0, "Group": 290.0}
BUSINESS_TYPES = (["Restaurant", "Bar", "Snack", "Café", "Hotel"], [0.48, 0.20, 0.15, 0.11, 0.06])


def seasonality(day: pd.Timestamp) -> float:
    """Growth trend + holiday dip + lower B2B activity at weekends."""
    months = (day - START).days / 30.4
    trend = 1 + 0.035 * months
    holiday = 0.55 if (day.month == 12 and day.day >= 22) or (day.month == 1 and day.day <= 3) else 1.0
    weekend = 0.72 if day.dayofweek >= 5 else 1.0
    return trend * holiday * weekend


# --------------------------------------------------------------------------- marketing daily
def build_marketing() -> pd.DataFrame:
    rows = []
    ch = CHANNELS.set_index("channel_id")
    for day in pd.date_range(START, END):
        s = seasonality(day)
        for c in CAMPAIGNS.itertuples():
            if day < pd.Timestamp(c.start_date):
                continue
            p = ch.loc[c.channel_id]
            if p.is_paid:
                spend = max(0.0, c.p_volume * s * rng.normal(1, 0.12))
                cpc = p.p_cpc * c.p_cost_mult * rng.normal(1, 0.06)
                clicks = int(round(spend / cpc))
                impressions = int(round(clicks / (p.p_ctr * rng.normal(1, 0.08))))
                sessions = int(round(clicks * rng.uniform(0.86, 0.94)))
            else:
                sessions = int(rng.poisson(c.p_volume * s))
                clicks = sessions
                impressions = int(round(sessions / p.p_ctr)) if p.p_ctr < 1 else sessions
                spend = 0.0
                if c.channel_id == 6:                      # email tool cost
                    spend = 6.5
                elif c.campaign_name == "Partner Network":  # partner commission
                    spend = 14.0 * s * rng.normal(1, 0.1)
                elif c.campaign_name == "Industry Events" and day.day in (5, 19):
                    spend = rng.uniform(1100, 1600)         # event participation
            rows.append((day.strftime("%Y-%m-%d"), p.channel_name, c.campaign_name,
                         impressions, clicks, sessions, round(spend, 2)))
    return pd.DataFrame(rows, columns=["date", "channel", "campaign", "impressions",
                                       "clicks", "sessions", "spend"])


# --------------------------------------------------------------------------- leads
def build_leads(mkt: pd.DataFrame) -> pd.DataFrame:
    ch = CHANNELS.set_index("channel_name")
    cp = CAMPAIGNS.set_index("campaign_name")
    rows, lead_id = [], 0
    for r in mkt.itertuples():
        pc, pk = ch.loc[r.channel], cp.loc[r.campaign]
        n = rng.poisson(r.sessions * pc.p_s2l)
        for _ in range(n):
            lead_id += 1
            quality = pc.p_quality * pk.p_quality_mult
            size_p = [0.22, 0.43, 0.35] if r.channel == "LinkedIn Ads" else [0.58, 0.33, 0.09]
            size = rng.choice(["1-9", "10-49", "50+"], p=size_p)
            region = rng.choice(REGIONS.region_name, p=REGIONS.p_weight / REGIONS.p_weight.sum())
            btype = rng.choice(BUSINESS_TYPES[0], p=BUSINESS_TYPES[1])
            score = pc.p_score * pk.p_quality_mult ** 0.5 + {"1-9": -4, "10-49": 3, "50+": 9}[size]
            score = int(np.clip(round(rng.normal(score, 13)), 0, 100))
            p_mql = np.clip((score - 18) / 70, 0.03, 0.95)
            is_mql = int(rng.random() < p_mql)
            p_sql = np.clip(0.36 * quality * (0.6 + score / 100), 0.02, 0.9)
            is_sql = int(is_mql and rng.random() < p_sql)
            ts = pd.Timestamp(r.date) + pd.Timedelta(minutes=int(rng.integers(7 * 60, 22 * 60)))
            rows.append((lead_id, ts.strftime("%Y-%m-%d %H:%M"), r.channel, r.campaign,
                         region, size, btype, score, is_mql, is_sql))
    return pd.DataFrame(rows, columns=["lead_id", "created_at", "channel", "campaign", "region",
                                       "company_size", "business_type", "lead_score",
                                       "is_mql", "is_sql"])


# --------------------------------------------------------------------------- opportunities
def build_opportunities(leads: pd.DataFrame) -> pd.DataFrame:
    ch = CHANNELS.set_index("channel_name")
    cp = CAMPAIGNS.set_index("campaign_name")
    rows, opp_id = [], 0
    for l in leads[leads.is_sql == 1].itertuples():
        if rng.random() > 0.84:            # not every SQL becomes an opportunity
            continue
        opp_id += 1
        quality = ch.loc[l.channel].p_quality * cp.loc[l.campaign].p_quality_mult
        created = pd.Timestamp(l.created_at).normalize() + pd.Timedelta(days=int(rng.integers(2, 11)))
        plan = {"1-9": rng.choice(["Starter", "Pro"], p=[0.7, 0.3]),
                "10-49": rng.choice(["Starter", "Pro", "Group"], p=[0.2, 0.65, 0.15]),
                "50+": rng.choice(["Pro", "Group"], p=[0.3, 0.7])}[l.company_size]
        sites = 1 if plan != "Group" else int(rng.integers(2, 6))
        expected = PLANS[plan] * 12 * sites * rng.uniform(0.9, 1.1)
        p_win = np.clip(0.21 * quality * (0.75 + l.lead_score / 160), 0.05, 0.8)
        cycle_mean = {"1-9": 16, "10-49": 26, "50+": 44}[l.company_size] * (1.25 if l.channel == "LinkedIn Ads" else 1)
        cycle = int(max(3, rng.gamma(4, cycle_mean / 4)))
        closed = created + pd.Timedelta(days=cycle)
        if closed > END:
            stage, closed_s, won = "Open", "", 0.0
        else:
            stage = "Won" if rng.random() < p_win else "Lost"
            closed_s = closed.strftime("%Y-%m-%d")
            won = round(expected * rng.uniform(0.85, 1.02), 2) if stage == "Won" else 0.0
        rows.append((opp_id, l.lead_id, created.strftime("%Y-%m-%d"), closed_s, stage,
                     plan, sites, round(expected, 2), won))
    return pd.DataFrame(rows, columns=["opportunity_id", "lead_id", "created_at", "closed_at",
                                       "stage", "plan", "sites", "expected_value", "won_value"])


# --------------------------------------------------------------------------- billing
def build_billing(opps: pd.DataFrame, leads: pd.DataFrame):
    won = opps[opps.stage == "Won"].merge(leads[["lead_id", "channel"]], on="lead_id")
    churn_hazard = {"Meta Ads": 0.045, "Google Ads": 0.024, "LinkedIn Ads": 0.016,
                    "Organic Search": 0.020, "Direct": 0.018, "Email": 0.017, "Referral": 0.010}
    customers, monthly = [], []
    months = pd.period_range(START, END, freq="M")
    for i, o in enumerate(won.itertuples(), start=1):
        start = pd.Timestamp(o.closed_at)
        mrr = round(o.won_value / 12, 2)
        customers.append((i, o.opportunity_id, start.strftime("%Y-%m-%d"), o.plan, mrr))
        churned = False
        for m in months[months >= start.to_period("M")]:
            if churned:
                break
            is_first = m == start.to_period("M")
            churned = (not is_first) and rng.random() < churn_hazard[o.channel]
            mrr_m = round(mrr * (1 + 0.004 * rng.normal()), 2)
            monthly.append((i, str(m), mrr_m, "churned" if churned else "active"))
    return (pd.DataFrame(customers, columns=["customer_id", "opportunity_id", "start_date",
                                             "plan", "starting_mrr"]),
            pd.DataFrame(monthly, columns=["customer_id", "year_month", "mrr", "status"]))


# --------------------------------------------------------------------------- anomalies
def inject_anomalies(mkt, leads, opps, cust):
    log = {}

    # Marketing export ------------------------------------------------------
    idx = rng.choice(mkt.index, 12, replace=False)
    mkt = pd.concat([mkt, mkt.loc[idx]], ignore_index=True)
    log["marketing_duplicate_rows"] = 12
    variants = {"Google Ads": ["google ads", "GOOGLE ADS ", "Google ads"],
                "Meta Ads": ["meta ads", "Meta ads ", "META ADS"],
                "LinkedIn Ads": ["Linkedin Ads", "linkedin ads"]}
    n = 0
    for name, alts in variants.items():
        sel = mkt[mkt.channel == name].sample(frac=0.04, random_state=SEED).index
        mkt.loc[sel, "channel"] = rng.choice(alts, len(sel))
        n += len(sel)
    log["marketing_channel_casing_variants"] = n
    bad_dates = rng.choice(mkt.index, 3, replace=False)
    mkt.loc[bad_dates, "date"] = ["2026-02-30", "2026-13-05", ""]
    log["marketing_invalid_dates"] = 3
    neg = rng.choice(mkt[mkt.spend > 0].index, 2, replace=False)
    mkt.loc[neg, "spend"] = -mkt.loc[neg, "spend"]
    log["marketing_negative_spend"] = 2
    out = rng.choice(mkt[(mkt.spend > 20) & (mkt.channel == "Google Ads")].index, 1)
    mkt.loc[out, "spend"] = mkt.loc[out, "spend"] * 100
    log["marketing_spend_outlier_x100"] = 1
    clk = rng.choice(mkt[mkt.impressions > 50].index, 2, replace=False)
    mkt.loc[clk, "clicks"] = mkt.loc[clk, "impressions"] + 40
    log["marketing_clicks_above_impressions"] = 2

    # CRM leads export ----------------------------------------------------
    dup = leads.sample(45, random_state=SEED)
    leads = pd.concat([leads, dup], ignore_index=True)
    log["lead_duplicate_rows"] = 45
    miss = rng.choice(leads.index, 60, replace=False)
    leads["lead_score"] = leads["lead_score"].astype("float")
    leads.loc[miss, "lead_score"] = np.nan
    log["lead_missing_score"] = 60
    oor = rng.choice(leads.index.difference(miss), 8, replace=False)
    leads.loc[oor, "lead_score"] = rng.choice([130, 145, -5, 999], 8)
    log["lead_score_out_of_range"] = 8
    bad_funnel = rng.choice(leads[(leads.is_mql == 1) & (leads.is_sql == 0)].index, 25, replace=False)
    leads.loc[bad_funnel, ["is_mql", "is_sql"]] = [0, 1]
    log["lead_sql_without_mql"] = 25
    unk = rng.choice(leads[leads.channel == "Meta Ads"].index, 30, replace=False)
    leads.loc[unk, "campaign"] = "Summer Promo TEST"
    log["lead_unknown_campaign"] = 30
    reg = rng.choice(leads.index, 70, replace=False)
    fr_names = {"Brussels": "Bruxelles", "Antwerp": "Anvers", "Liège": "LIEGE",
                "Hainaut": "hainaut", "Namur": "namur ", "East Flanders": "Oost-Vlaanderen"}
    leads.loc[reg, "region"] = leads.loc[reg, "region"].map(lambda r: fr_names.get(r, r.upper()))
    log["lead_region_label_variants"] = 70
    size = rng.choice(leads.index, 40, replace=False)
    leads.loc[size, "company_size"] = leads.loc[size, "company_size"].map(
        {"1-9": "1 - 9", "10-49": "10 - 49", "50+": "50 +"})
    log["lead_company_size_format_variants"] = 40
    no_id = rng.choice(leads.index, 3, replace=False)
    leads["lead_id"] = leads["lead_id"].astype("Int64")
    leads.loc[no_id, "lead_id"] = pd.NA
    log["lead_missing_id"] = 3

    # CRM opportunities export ---------------------------------------------
    case = rng.choice(opps.index, 35, replace=False)
    opps.loc[case, "stage"] = opps.loc[case, "stage"].map({"Won": "won", "Lost": "LOST", "Open": "open"})
    log["opportunity_stage_casing"] = 35
    won_zero = rng.choice(opps[opps.stage == "Won"].index, 6, replace=False)
    opps.loc[won_zero, "won_value"] = 0.0
    log["opportunity_won_without_value"] = 6
    closed = opps[(opps.closed_at != "")].index.difference(won_zero)
    inv = rng.choice(closed, 4, replace=False)
    opps.loc[inv, "closed_at"] = (pd.to_datetime(opps.loc[inv, "created_at"]) - pd.Timedelta(days=5)).dt.strftime("%Y-%m-%d")
    log["opportunity_closed_before_created"] = 4
    orphans = pd.DataFrame({"opportunity_id": range(90001, 90006), "lead_id": range(990001, 990006),
                            "created_at": "2026-03-10", "closed_at": "", "stage": "Open",
                            "plan": "Pro", "sites": 1, "expected_value": 1428.0, "won_value": 0.0})
    opps = pd.concat([opps, orphans], ignore_index=True)
    log["opportunity_orphan_lead"] = 5
    opps = pd.concat([opps, opps.sample(8, random_state=SEED + 1)], ignore_index=True)
    log["opportunity_duplicate_rows"] = 8

    # Billing export --------------------------------------------------------
    cust = pd.concat([cust, cust.sample(3, random_state=SEED)], ignore_index=True)
    log["customer_duplicate_rows"] = 3
    return mkt, leads, opps, cust, log


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    REF.mkdir(parents=True, exist_ok=True)
    CHANNELS.loc[:, ~CHANNELS.columns.str.startswith("p_")].to_csv(REF / "channels.csv", index=False)
    CAMPAIGNS.loc[:, ~CAMPAIGNS.columns.str.startswith("p_")].to_csv(REF / "campaigns.csv", index=False)
    REGIONS.loc[:, ~REGIONS.columns.str.startswith("p_")].to_csv(REF / "regions.csv", index=False)

    mkt = build_marketing()
    leads = build_leads(mkt)
    opps = build_opportunities(leads)
    cust, monthly = build_billing(opps, leads)
    mkt, leads, opps, cust, log = inject_anomalies(mkt, leads, opps, cust)

    # shuffle exports a little, like real tools do
    mkt = mkt.sample(frac=1, random_state=SEED).reset_index(drop=True)
    mkt.to_csv(RAW / "ads_platform_export.csv", index=False)
    leads.to_csv(RAW / "crm_leads_export.csv", index=False)
    opps.to_csv(RAW / "crm_opportunities_export.csv", index=False)
    cust.to_csv(RAW / "billing_customers_export.csv", index=False)
    monthly.to_csv(RAW / "billing_mrr_monthly_export.csv", index=False)
    (RAW / "_injected_anomalies.json").write_text(json.dumps(log, indent=2), encoding="utf-8")

    for name, df in [("ads_platform_export", mkt), ("crm_leads_export", leads),
                     ("crm_opportunities_export", opps), ("billing_customers_export", cust),
                     ("billing_mrr_monthly_export", monthly)]:
        print(f"{name:32s} {len(df):>7,} rows")
    print(f"anomalies injected: {sum(log.values())} across {len(log)} rules")


if __name__ == "__main__":
    main()
