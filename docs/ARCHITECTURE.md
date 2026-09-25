# Architecture

> Professional context based on a real ODRES Group experience. Public technical reconstruction using synthetic data.

```text
 SOURCE EXPORTS (synthetic)          CLEAN LAYER              DATABASE (SQLite)                 BI + DECISIONS
 ────────────────────────           ─────────────             ─────────────────                 ──────────────
 ads_platform_export.csv   ─┐                                 01_schema.sql  keys + CHECK rules
 crm_leads_export.csv       │  validate   clean   validate    02_views.sql   6 reporting views   powerbi/data/*.csv
 crm_opportunities_export  ─┼─►  (raw) ─► rules ─►  (clean) ─► 03-07 *.sql    38 analysis queries ─► TMDL model + DAX
 billing_customers_export   │   22 checks  22 rules  0 errors  integrity_tests 14 tests          ─► 6 dashboard pages
 billing_mrr_monthly_export─┘                                                                    ─► insights + recommendations
 + reference/ (channels, campaigns, regions)
```

## Layers

| # | Layer | Folder / script | What it guarantees |
|---|---|---|---|
| 1 | Source | `data/raw/`, `data/reference/` — `generate_synthetic_data.py` | Realistic exports with 20 kinds of controlled anomalies, deterministic seed |
| 2 | Quality (before) | `validate_data.py` | 22 checks measured on the raw exports |
| 3 | Clean | `data/clean/` — `clean_data.py` | 22 documented rules, logged in `data/processed/cleaning_log.csv` |
| 4 | Quality (after) | `validate_data.py` | Blocking checks must be 0, else the pipeline stops; report in `docs/DATA_QUALITY_REPORT.md` |
| 5 | Storage | `database/*.sqlite` — `load_to_sqlite.py` | Primary/foreign keys and business rules enforced by the schema; full SQL dump |
| 6 | Semantic | `sql/02_views.sql` | One definition per KPI, reused by every query, export and chart |
| 7 | Analysis | `sql/03`–`07`, `tests/integrity_tests.sql` — `run_sql_tests.py` | Every statement executed on each run; 14 integrity tests |
| 8 | Reporting | `data/processed/` — `build_reporting_tables.py` | View exports, KPI summary JSON, raw samples |
| 9 | BI | `powerbi/` — `export_powerbi_data.py`, `build_powerbi_project.py` | Star-schema CSVs, TMDL model, DAX documentation |
| 10 | Visuals | `dashboard/`, `proofs/` — `powerbi_report.py`, `make_visuals.py`, `build_powerbi_proofs.py` | 6-page Power BI report (screenshots) and 6 portfolio proofs |

## Design decisions

- **Raw is never edited.** Corrections happen in the clean layer, so every change is traceable.
- **Rules live in the schema.** `CHECK (is_sql <= is_mql)`, `CHECK (spend >= 0)`, `CHECK (status <> 'Won' OR
  won_value > 0)`: bad rows cannot be loaded silently, even by mistake.
- **Not applicable ≠ zero.** CAC and CPL are NULL / blank for channels without spend, in SQL and in DAX.
- **Unknown ≠ zero.** A missing lead score stays NULL and is excluded from averages instead of being imputed.
- **One number, one definition.** KPIs are defined once in SQL views and once in DAX measures (generated from a
  single Python list), then reused.
- **Reproducible.** `python run_pipeline.py` rebuilds everything from nothing in about a minute.
