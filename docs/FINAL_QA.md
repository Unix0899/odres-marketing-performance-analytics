# Final QA

> Professional context based on a real ODRES Group experience. Public technical reconstruction using synthetic data.

QA run on 24/09/2026 after `python run_pipeline.py` (full rebuild from scratch, 28 s).

## Technical checks

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Python scripts run | **PASS** | 10/10 pipeline steps succeed (`run_pipeline.py`) |
| 2 | Dataset reproducible | **PASS** | Fixed seed 20260924; same row counts on every rebuild |
| 3 | SQLite opens | **PASS** | Opened read-only; `PRAGMA integrity_check` = ok; 0 foreign-key violations |
| 4 | Schema enforces business rules | **PASS** | Clean layer loads with every CHECK / FK constraint active |
| 5 | SQL queries run | **PASS** | 38 analysis statements executed, all return rows (`data/processed/sql_run_log.csv`) |
| 6 | Views work | **PASS** | 7 views queried by the analysis files and exports |
| 7 | Integrity tests | **PASS** | 14/14 tests with 0 failures |
| 8 | Data quality | **PASS** | 443 raw issues → 0 blocking issues; 2 documented warnings ([report](DATA_QUALITY_REPORT.md)) |
| 9 | Critical metrics reproducible | **PASS** | KPIs recomputed by SQL views, `kpi_summary.json`, charts and tests from the same database; reconciliation tests on leads, spend and revenue |
| 10 | No broken paths (repository) | **PASS** | 37 relative Markdown links checked, 0 broken |
| 11 | No confidential data | **PASS** | Scan for secrets, API keys, e-mails, phone numbers: 0 hits (code, data, docs, SQL dump) |
| 12 | No fake ODRES claims | **PASS** | Disclosure on README, docs, dashboards, Power BI model, portfolio page; insights say "in the synthetic demonstration dataset" |
| 13 | Power BI exports exist | **PASS** | 12 CSV tables in `powerbi/data/` |
| 14 | DAX measures | **PASS** | 47 measures (38 core + 9 report helpers) documented and written into the TMDL model |
| 15 | Power BI Project (PBIP) generated | **PASS** | TMDL model: 12 tables, 16 relationships, 47 measures, 2 calculated columns; 6-page report with 85 visuals |
| 16 | Model loads in the Power BI engine | **PASS** | Imported with Microsoft's Power BI Modeling MCP server (`src/validate_powerbi_model.py`): 12 tables, 16 relationships and all measures. The check found and fixed one TMDL error |
| 16b | DAX measures = SQL | **PASS** | PBIP opened in Power BI Desktop, queried read-only: **102/102** comparisons match SQL (38 core measures, 7 channels, 8 months) — [reconciliation](POWERBI_SQL_RECONCILIATION.md) |
| 16c | PBIP opens in Power BI Desktop | **PASS** | After fixing a measure/column name clash reported by Desktop |
| 17 | Power BI report | **PASS** | 6 pages generated in the PBIP and validated in Power BI Desktop; `.pbix` optional via *Save as* |
| 18 | Dashboard images | **PASS** | 6 real Power BI screenshots (`dashboard/powerbi_*.png`), report validated by Harry in Power BI Desktop |
| 19 | Proofs | **PASS** | 6 PNG files in `proofs/` |

## Portfolio website

| # | Check | Result | Evidence |
|---|---|---|---|
| 20 | Case study page works | **PASS** | `site/projects/odres/` rendered in a browser, 17 sections |
| 21 | Images load / links work | **PASS** | 37 local links and images checked on the 3 pages: 0 broken |
| 22 | Translations complete | **PASS** | EN / FR / NL: 210 keys on the ODRES page, 0 missing |
| 23 | Home page updated | **PASS** | ODRES card live with thumbnail; skills map links to ODRES sections |
| 24 | Real experience vs public reconstruction separated | **PASS** | "My role" section, two explicit columns |

## Recruiter criteria

| Question | Answer |
|---|---|
| Can I see the raw data? | Yes — `data/raw/`, `data/samples/` |
| Can I understand the schema? | Yes — `proof_04_model.png`, `DATA_DICTIONARY.md`, `01_schema.sql` |
| Can I inspect the SQL? | Yes — `sql/01`–`07`, proof 02 |
| Can I see data-quality work? | Yes — report, proof 03, dashboard page 6 |
| Can I understand the KPIs? | Yes — data dictionary, DAX measures, KPI framework on the page |
| Can I see a dashboard? | Yes — 6 Power BI pages (screenshots + PBIP) |
| Can I understand the business question? | Yes — `BUSINESS_CASE.md` |
| Can I see the recommendations? | Yes — `INSIGHTS.md`, proof 06, portfolio section 11 |
| Can I understand what Harry actually did? | Yes — real experience vs public reconstruction |
| Is confidentiality respected? | Yes — synthetic data, disclosure everywhere, secret scan clean |
| Could Harry explain every part in an interview? | Yes, if he walks through `RECRUITER_GUIDE.md` and the interview questions it lists |
| Does it look like professional analyst work? | Yes — layered pipeline, tests, documented rules, decisions |

## Remaining manual work

1. Optional: *File → Save as* `.pbix` if a single file is needed (the PBIP is the versioned source).
2. Done: repository published at https://github.com/Unix0899/odres-marketing-performance-analytics and linked from the portfolio page.
