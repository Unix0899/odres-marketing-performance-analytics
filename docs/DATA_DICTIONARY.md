# Data dictionary

> Professional context based on a real ODRES Group experience. Public technical reconstruction using synthetic data.
> All values are fictional. Currency: EUR. Period: 1 Nov 2025 – 30 Jun 2026.

## Dimensions

### dim_date
| Column | Type | Description |
|---|---|---|
| date_key | INTEGER PK | YYYYMMDD, join key used by every fact |
| date | TEXT | ISO date (Power BI date-table key) |
| year, quarter, month, month_name, year_month, week | | Calendar attributes; `year_month` = YYYY-MM for monthly reporting |
| day_of_week, is_weekend | | Day name, 1 if Saturday/Sunday |

### dim_channel
| Column | Type | Description |
|---|---|---|
| channel_id | INTEGER PK | |
| channel_name | TEXT | Google Ads, LinkedIn Ads, Meta Ads, Organic Search, Direct, Email, Referral |
| channel_group | TEXT | Paid Search, Paid Social, Organic, Direct, Owned, Referral |
| is_paid | 0/1 | 1 = paid media (CAC is meaningful) |

### dim_campaign
| Column | Type | Description |
|---|---|---|
| campaign_id | INTEGER PK | 0 = "Unassigned" in the Power BI export only |
| campaign_name | TEXT | 21 campaigns, 3 per channel |
| channel_id | INTEGER FK | Owning channel |
| objective | TEXT | Conversion, Lead gen, Awareness, Organic, Direct, Nurture, Partnership, Events |
| start_date | TEXT | First day of activity |

### dim_region
| Column | Type | Description |
|---|---|---|
| region_id | INTEGER PK | |
| region_name | TEXT | 8 Belgian provinces / Brussels |
| region_group | TEXT | Brussels-Capital, Flanders, Wallonia |

### dim_customer
| Column | Type | Description |
|---|---|---|
| customer_id | INTEGER PK | |
| opportunity_id | INTEGER FK UNIQUE | The won deal that created the customer |
| lead_id | INTEGER FK | Original lead |
| acquisition_date_key | INTEGER FK | Close date of the won deal |
| channel_id, campaign_id, region_id | FK | Inherited from the lead (first-touch attribution) |
| company_size | TEXT | 1-9, 10-49, 50+ employees |
| business_type | TEXT | Restaurant, Bar, Snack, Café, Hotel |
| plan | TEXT | Starter, Pro, Group (fictional plans and prices) |
| starting_mrr | REAL | Monthly recurring revenue at start = first-year value / 12 |

## Facts

### fact_marketing_daily — grain: date × campaign
| Column | Type | Description |
|---|---|---|
| date_key, campaign_id | PK | |
| channel_id | FK | |
| impressions, clicks, sessions | INTEGER | Ad impressions (or organic impressions / emails sent), clicks, website sessions |
| spend | REAL | Paid media cost; email tool cost; partner commissions; event participation |

### fact_leads — grain: lead
| Column | Type | Description |
|---|---|---|
| lead_id | INTEGER PK | |
| created_date_key | FK | Lead creation date |
| channel_id | FK | Source channel |
| campaign_id | FK, nullable | NULL = unknown campaign tag in the CRM (kept, shown as Unassigned) |
| region_id | FK | |
| company_size, business_type | TEXT | Firmographics |
| lead_score | INTEGER 0–100, nullable | CRM score; NULL = unknown |
| is_mql, is_sql | 0/1 | Marketing- / sales-qualified. Rule: `is_sql <= is_mql` |

### fact_opportunities — grain: opportunity
| Column | Type | Description |
|---|---|---|
| opportunity_id | INTEGER PK | |
| lead_id | FK | |
| created_date_key, close_date_key | FK | Close date NULL = open, or unknown after cleaning (rule O5) |
| channel_id, campaign_id, region_id, company_size | | Inherited from the lead |
| plan, sites | | Plan proposed, number of sites (Group plan: 2–5) |
| status, is_won | | Won / Lost / Open |
| expected_value | REAL | First-year contract value proposed |
| won_value | REAL | First-year contract value signed (0 unless Won) |
| sales_cycle_days | INTEGER | Close date − creation date |
| value_imputed | 0/1 | 1 = won value taken from expected value (rule O4) |

### fact_customer_monthly — grain: customer × month
| Column | Type | Description |
|---|---|---|
| customer_id, year_month | PK | |
| month_key | FK | First day of the month (YYYYMM01) |
| mrr | REAL | Monthly recurring revenue billed |
| is_active, is_churned | 0/1 | Churned = the month the customer stopped |

## KPI definitions

| KPI | Definition |
|---|---|
| CTR | clicks / impressions |
| CPC | spend / clicks |
| CPL | spend / leads (blank if no spend) |
| CAC | spend / new customers (blank if no spend) |
| Lead → MQL → SQL → Customer % | stage volume / previous stage volume |
| Win rate | won / (won + lost) |
| Revenue / Spend | first-year won revenue / spend |
| Average deal value | won revenue / won deals |
| Sales cycle | days from opportunity creation to close (won deals, known dates) |
| MRR | sum of monthly recurring revenue of active customers |
| Churn rate | churned customers / (active + churned) in the month |
| MoM % | (month − previous month) / previous month |
