# Power BI ↔ SQL reconciliation

> Professional context based on a real ODRES Group experience. Public technical reconstruction using synthetic data.

Run on 24/09/2026 18:22 with `src/reconcile_powerbi_sql.py`: the PBIP open in Power BI Desktop, queried **read-only** through Microsoft's Power BI Modeling MCP server, compared with the same numbers computed in SQLite.

**Result: 102/102 comparisons PASS** (tolerance 0.5 %).

| Scope | Measure | Power BI (DAX) | SQL | Status |
|---|---|---:|---:|---|
| Whole period | Total Spend | 112,850.88 | 112,850.88 | PASS |
| Whole period | Impressions | 6,476,416.00 | 6,476,416.00 | PASS |
| Whole period | Clicks | 185,433.00 | 185,433.00 | PASS |
| Whole period | Sessions | 179,556.00 | 179,556.00 | PASS |
| Whole period | CTR | 0.0286 | 0.0286 | PASS |
| Whole period | CPC | 0.6086 | 0.6086 | PASS |
| Whole period | Leads | 5,477.00 | 5,477.00 | PASS |
| Whole period | MQLs | 2,677.00 | 2,677.00 | PASS |
| Whole period | SQLs | 1,493.00 | 1,493.00 | PASS |
| Whole period | Avg Lead Score | 52.54 | 52.54 | PASS |
| Whole period | Opportunities | 1,222.00 | 1,222.00 | PASS |
| Whole period | Customers | 350.00 | 350.00 | PASS |
| Whole period | Session to Lead % | 0.0305 | 0.0305 | PASS |
| Whole period | Lead to MQL % | 0.4888 | 0.4888 | PASS |
| Whole period | MQL to SQL % | 0.5577 | 0.5577 | PASS |
| Whole period | SQL to Customer % | 0.2344 | 0.2344 | PASS |
| Whole period | Lead to Customer % | 0.0639 | 0.0639 | PASS |
| Whole period | CPL | 20.60 | 20.60 | PASS |
| Whole period | CAC | 322.43 | 322.43 | PASS |
| Whole period | Won Revenue | 751,030.94 | 751,030.94 | PASS |
| Whole period | Revenue / Spend | 6.6551 | 6.6551 | PASS |
| Whole period | Average Deal Value | 2,145.80 | 2,145.80 | PASS |
| Whole period | Average Sales Cycle | 20.52 | 20.52 | PASS |
| Whole period | Win Rate | 0.3359 | 0.3359 | PASS |
| Whole period | Open Pipeline | 590,843.22 | 590,843.22 | PASS |
| Whole period | Lost Value | 1,896,224.45 | 1,896,224.45 | PASS |
| Whole period | MRR | 191,715.59 | 191,715.59 | PASS |
| Whole period | MRR (end of period) | 58,044.42 | 58,044.42 | PASS |
| Whole period | Active Customers | 350.00 | 350.00 | PASS |
| Whole period | Churned Customers | 19.00 | 19.00 | PASS |
| Whole period | Churn Rate | 0.0515 | 0.0515 | PASS |
| Whole period | Issues Found (raw) | 443.00 | 443.00 | PASS |
| Whole period | Blocking Errors Left | 0.0000 | 0.0000 | PASS |
| Whole period | Documented Warnings | 96.00 | 96.00 | PASS |
| Whole period | Rows Loaded | 12,838.00 | 12,838.00 | PASS |
| Whole period | Rows Removed | 79.00 | 79.00 | PASS |
| Google Ads | Leads | 535.00 | 535.00 | PASS |
| Google Ads | Customers | 26.00 | 26.00 | PASS |
| Google Ads | Won Revenue | 48,580.67 | 48,580.67 | PASS |
| Google Ads | CPL | 77.75 | 77.75 | PASS |
| Google Ads | CAC | 1,599.82 | 1,599.82 | PASS |
| Google Ads | Win Rate | 0.3250 | 0.3250 | PASS |
| LinkedIn Ads | Leads | 140.00 | 140.00 | PASS |
| LinkedIn Ads | Customers | 20.00 | 20.00 | PASS |
| LinkedIn Ads | Won Revenue | 67,951.63 | 67,951.63 | PASS |
| LinkedIn Ads | CPL | 190.40 | 190.40 | PASS |
| LinkedIn Ads | CAC | 1,332.78 | 1,332.78 | PASS |
| LinkedIn Ads | Win Rate | 0.4000 | 0.4000 | PASS |
| Meta Ads | Leads | 1,533.00 | 1,533.00 | PASS |
| Meta Ads | Customers | 7.0000 | 7.0000 | PASS |
| Meta Ads | Won Revenue | 6,241.34 | 6,241.34 | PASS |
| Meta Ads | CPL | 16.14 | 16.14 | PASS |
| Meta Ads | CAC | 3,534.10 | 3,534.10 | PASS |
| Meta Ads | Win Rate | 0.1489 | 0.1489 | PASS |
| Organic Search | Leads | 1,075.00 | 1,075.00 | PASS |
| Organic Search | Customers | 53.00 | 53.00 | PASS |
| Organic Search | Won Revenue | 141,486.97 | 141,486.97 | PASS |
| Organic Search | CPL | blank | blank | PASS |
| Organic Search | CAC | blank | blank | PASS |
| Organic Search | Win Rate | 0.2690 | 0.2690 | PASS |
| Direct | Leads | 823.00 | 823.00 | PASS |
| Direct | Customers | 65.00 | 65.00 | PASS |
| Direct | Won Revenue | 94,125.53 | 94,125.53 | PASS |
| Direct | CPL | blank | blank | PASS |
| Direct | CAC | blank | blank | PASS |
| Direct | Win Rate | 0.3171 | 0.3171 | PASS |
| Email | Leads | 805.00 | 805.00 | PASS |
| Email | Customers | 72.00 | 72.00 | PASS |
| Email | Won Revenue | 155,715.06 | 155,715.06 | PASS |
| Email | CPL | 4.8770 | 4.8800 | PASS |
| Email | CAC | 54.53 | 54.53 | PASS |
| Email | Win Rate | 0.3186 | 0.3186 | PASS |
| Referral | Leads | 566.00 | 566.00 | PASS |
| Referral | Customers | 107.00 | 107.00 | PASS |
| Referral | Won Revenue | 236,929.74 | 236,929.74 | PASS |
| Referral | CPL | 28.15 | 28.15 | PASS |
| Referral | CAC | 148.93 | 148.93 | PASS |
| Referral | Win Rate | 0.4515 | 0.4515 | PASS |
| 2025-11 | Leads | 514.00 | 514.00 | PASS |
| 2025-11 | MoM Leads % | blank | blank | PASS |
| 2025-11 | MoM Revenue % | blank | blank | PASS |
| 2025-12 | Leads | 540.00 | 540.00 | PASS |
| 2025-12 | MoM Leads % | 0.0506 | 0.0506 | PASS |
| 2025-12 | MoM Revenue % | 8.5553 | 8.5553 | PASS |
| 2026-01 | Leads | 616.00 | 616.00 | PASS |
| 2026-01 | MoM Leads % | 0.1407 | 0.1407 | PASS |
| 2026-01 | MoM Revenue % | -0.0016 | -0.0016 | PASS |
| 2026-02 | Leads | 659.00 | 659.00 | PASS |
| 2026-02 | MoM Leads % | 0.0698 | 0.0698 | PASS |
| 2026-02 | MoM Revenue % | 0.1548 | 0.1548 | PASS |
| 2026-03 | Leads | 741.00 | 741.00 | PASS |
| 2026-03 | MoM Leads % | 0.1244 | 0.1244 | PASS |
| 2026-03 | MoM Revenue % | -0.0426 | -0.0426 | PASS |
| 2026-04 | Leads | 756.00 | 756.00 | PASS |
| 2026-04 | MoM Leads % | 0.0202 | 0.0202 | PASS |
| 2026-04 | MoM Revenue % | 0.2537 | 0.2537 | PASS |
| 2026-05 | Leads | 827.00 | 827.00 | PASS |
| 2026-05 | MoM Leads % | 0.0939 | 0.0939 | PASS |
| 2026-05 | MoM Revenue % | 0.2995 | 0.2995 | PASS |
| 2026-06 | Leads | 824.00 | 824.00 | PASS |
| 2026-06 | MoM Leads % | -0.0036 | -0.0036 | PASS |
| 2026-06 | MoM Revenue % | 0.7587 | 0.7587 | PASS |
