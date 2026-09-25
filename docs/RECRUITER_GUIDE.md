# Recruiter guide — where to look (10 minutes)

> Professional context based on a real ODRES Group experience. Public technical reconstruction using synthetic data.

| Question you may have | Where to look | Time |
|---|---|---|
| What was the business problem? | [BUSINESS_CASE.md](BUSINESS_CASE.md) | 1 min |
| What did Harry conclude? | [INSIGHTS.md](INSIGHTS.md) and `proofs/proof_06_business_insight.png` | 2 min |
| Can I see a dashboard? | `dashboard/powerbi_01_executive_overview.png` (and pages 02–06) | 1 min |
| Can I see the raw data? | `data/raw/` (full exports) or `data/samples/` (200 rows each) | 1 min |
| Can I see data-quality work? | [DATA_QUALITY_REPORT.md](DATA_QUALITY_REPORT.md), `proofs/proof_03_data_quality.png` | 1 min |
| Can I understand the schema? | `proofs/proof_04_model.png`, [DATA_DICTIONARY.md](DATA_DICTIONARY.md), `sql/01_schema.sql` | 2 min |
| Can I inspect the SQL? | `sql/05_campaign_analysis.sql` (Q18), `sql/02_views.sql` | 2 min |
| Power BI / DAX? | `powerbi/DAX_MEASURES.md`, `powerbi/DATA_MODEL.md`, `powerbi/ODRES_Marketing_Analytics/` | 1 min |
| Do Power BI and SQL agree? | [POWERBI_SQL_RECONCILIATION.md](POWERBI_SQL_RECONCILIATION.md): 102/102 PASS | 30 s |
| Is confidentiality respected? | [DATA_DISCLOSURE.md](DATA_DISCLOSURE.md) | 30 s |

## Skill → evidence

| Skill | Evidence |
|---|---|
| SQL | 6 reusable views and 38 analysis queries (CTE, subqueries, window functions `LAG` / `RANK` / `DENSE_RANK`, rolling averages, `HAVING`, `NULLIF`, `COALESCE`), all executed automatically |
| Data modelling | Star schema with 4 fact tables, keys and business-rule constraints in `01_schema.sql` |
| Python / pandas | Generator, 22 cleaning rules, 22 validation checks, exports, charts: `src/` |
| Data quality | 443 issues found in the raw exports, 0 blocking issues after cleaning, documented warnings |
| Power BI / DAX | 47 measures, TMDL semantic model, 6-page Power BI report, 102/102 measures reconciled with SQL |
| Business analysis | 6 insights with evidence, impact and a testable recommendation each |

## Questions to ask Harry in an interview

- Why is CAC blank, not zero, for organic channels?
- Why is a missing lead score not imputed?
- Why does LinkedIn get a SCALE recommendation despite the highest CPL?
- How would you validate the "reduce Meta Awareness Video" recommendation before acting on it?
- What would change with multi-touch attribution?
