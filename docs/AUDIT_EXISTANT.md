# Audit of the existing project (before changes)

> Professional context based on a real ODRES Group experience. Public technical reconstruction using synthetic data.

Audit date: 24/09/2026. Source: `ODRES_Marketing_Performance_Analytics_SYNTHETIC.zip` (43 files) and
`Harry_Mulembwe_Portfolio_with_ODRES.zip` (`projects/odres/`).

## 1. Existing files

| Area | Files | Content |
|---|---|---|
| Root | `README.md`, `requirements.txt`, `.gitignore`, `MANIFEST.csv` | README with disclosure, 3 dependencies, SHA-256 manifest |
| Raw data | `data/raw/*.csv` (9 files) | 5,082 marketing-day rows, 18,905 leads, 2,043 opportunities, 823 customers, 3,023 customer-months, 4 dimensions |
| Processed | `data/processed/*.csv` (3 files) | channel, campaign and monthly summaries |
| Database | `database/odres_marketing_analytics_demo.sqlite` | 9 tables, 4 views |
| SQL | `schema_and_views.sql`, `analysis_queries.sql` (25 queries), `odres_full_database_dump.sql` (2.3 MB) | indexes, views, analysis pack |
| Python | `src/*.py` (4 files) | loader, quality checks, export, generator |
| Power BI | `powerbi/*.csv` (9), `DAX_MEASURES.md`, `MODEL_AND_REPORT_PAGES.md` | star-schema CSVs, 14 measures, relationship list |
| Dashboard | `dashboard/index.html`, 3 PNG charts, `kpi_summary.json` | HTML preview, matplotlib charts |
| Docs / tests | `docs/ARCHITECTURE.md`, `docs/DATA_DISCLOSURE.md`, `tests/integrity_tests.sql` | short notes, 3 integrity tests |
| Portfolio | `projects/odres/index.html`, `styles.css`, `technical/`, `assets/` | first case-study page, English only |

## 2. What is already solid

- Clear synthetic-data disclosure in the README and on the portfolio page.
- Good business question and a sensible entity list (channel, campaign, region, lead, opportunity, customer, MRR).
- `analysis_queries.sql` already uses CTEs, `LAG`, `CASE WHEN`, `NULLIF`, `COALESCE`, `HAVING`.
- Realistic Belgian regions and B2B campaign names that fit ODRES (hospitality software).
- The intended Power BI page list (6 pages, including Data Quality) matches the target.

## 3. Problems found

### Blocking

1. **The generator is empty.** `src/generate_synthetic_data.py` contains only a seed and comments: the dataset cannot be reproduced.
2. **Unrealistic economics.** €86,733 of spend for €2.4M of won revenue (28× return), CPL of €0.41–€0.81 on Email and Referral, 11.5% session-to-lead rate. A recruiter with marketing experience would not trust these numbers.
3. **No real data-quality story.** Raw and "processed" layers are identical; there are no anomalies to find and no cleaning step. The Data Quality page would have nothing to show.
4. **Misleading zeros.** Organic and Direct channels show CAC = 0.00 instead of "not applicable" (no paid spend).

### Important

5. `dim_channel` stores the generator's parameters (`session_to_lead`, `mql_to_sql`, `avg_deal_value`) as if they were business attributes: it reveals how the data was faked.
6. No primary or foreign keys in SQLite (tables created by `pandas.to_sql`); IDs stored as floats (`20251101.0`).
7. `powerbi/*.csv` are byte-identical copies of `data/raw/*.csv` (redundant, 1.1 MB duplicated).
8. Only 4 views; `vw_funnel`, `vw_campaign_performance`, `vw_revenue_pipeline`, `vw_customer_value` missing.
9. Only 14 DAX measures; no CTR, CPC, stage conversions, MoM %, sales cycle.
10. Charts are generic matplotlib plots; no dashboard pages, no model diagram, no proofs folder.
11. Portfolio page: English only, not connected to the site's language switcher, no "real experience vs public reconstruction" split, links to `.sql`/`.md` files that browsers download instead of display.

### Minor

12. `dashboard/kpi_summary.json` and `dashboard/index.html` hard-code numbers that drift from the database.
13. `requirements.txt` has no versions; `.gitignore` does not ignore generated logs.
14. `MANIFEST.csv` will be out of date after any change.

## 4. Redundant or unnecessary files

| File | Decision |
|---|---|
| `powerbi/*.csv` (9) | Replaced by `powerbi/data/` generated from the clean layer |
| `sql/schema_and_views.sql`, `sql/analysis_queries.sql` | Split into numbered, commented files `01`–`07`; good queries kept and improved |
| `src/data_quality_checks.py`, `src/export_reporting_tables.py` | Replaced by `validate_data.py`, `build_reporting_tables.py`, `export_powerbi_data.py` |
| `dashboard/index.html`, `kpi_summary.json`, 3 PNGs | Replaced by 6 dashboard prototype pages generated from the database |
| `powerbi/MODEL_AND_REPORT_PAGES.md` | Split into `DATA_MODEL.md` and `DASHBOARD_SPEC.md` |

## 5. Missing elements

- Working generator with controlled anomalies; clean layer; before/after quality report.
- Explicit schema (`01_schema.sql`) with keys and constraints.
- Views: `vw_channel_performance`, `vw_campaign_performance`, `vw_monthly_management`, `vw_funnel`, `vw_revenue_pipeline`, `vw_customer_value`.
- Complete DAX layer and a Power BI project file.
- Proof images, data-model diagram, insights, recruiter guide, data dictionary, final QA.

## 6. Improvement plan

1. Rewrite the generator (deterministic seed, realistic B2B SaaS economics, CRM-style raw exports with documented anomalies).
2. Pipeline: `validate (raw) → clean → validate (clean) → load SQLite with schema → views → reporting tables → Power BI exports → visuals`, orchestrated by `run_pipeline.py`.
3. SQL rebuilt in 7 numbered files + integrity tests; every file executed automatically.
4. Power BI: star-schema CSVs, `DATA_MODEL.md`, `DAX_MEASURES.md` (26+ measures), `DASHBOARD_SPEC.md`, and a Power BI Project (PBIP) with the semantic model if Power BI Desktop accepts it.
5. Visuals: 6 dashboard prototype pages (clearly named *prototype*), model diagram, 6 proofs.
6. Docs: README, architecture, dictionary, disclosure, business case, insights, recruiter guide, final QA.
7. Portfolio: rebuild `projects/odres/` in the current trilingual site (EN/FR/NL) following the claim → evidence rule.
