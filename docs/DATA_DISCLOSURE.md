# Confidentiality and synthetic data disclosure

> **Professional context based on a real ODRES Group experience. Public technical reconstruction using synthetic data.**

## What is real

- Harry Mulembwe worked at ODRES Group (Digital Marketing & Data Assistant, Nov 2025 – Jun 2026) on digital
  acquisition performance, KPI monitoring, management reporting and marketing / business recommendations.
- The *type* of questions, KPIs and reporting logic reflects that experience.

## What is synthetic

**Every row in this repository is generated** by `src/generate_synthetic_data.py` (fixed seed 20260924):
campaign results, leads, companies, opportunities, customers, plans, prices, revenue, MRR and churn.

This repository does **not** contain and is not derived from:

- ODRES clients, prospects or their identifiers;
- ODRES revenue, pricing, contracts or commercial performance;
- exports from ODRES internal tools, CRM, ad accounts or databases;
- any secret, API key or token.

Campaign names are generic marketing labels. Plans (Starter / Pro / Group) and prices are fictional.

## How to read the numbers

Findings are written as "In the synthetic demonstration dataset…". They show the analytical method, not ODRES's
results. The generator deliberately includes realistic trade-offs (high-volume / low-quality channels, expensive
but valuable channels) so that the analysis has real decisions to make.
