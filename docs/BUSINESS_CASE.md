# Business case

> Professional context based on a real ODRES Group experience. Public technical reconstruction using synthetic data.

## Context

ODRES Group develops an ERP (odres.io) that lets restaurants, shops and other businesses manage their establishment
through several connected applications. The synthetic reconstruction focuses on its hospitality customers
(restaurants, bars, snacks, cafés, hotels).
Growth depends on acquiring these businesses as subscribers through several channels: paid search and social ads,
organic search, direct traffic, email nurturing, partners and referrals.

Marketing and sales information lives in separate tools: ad platforms (spend, clicks), web analytics (sessions),
the CRM (leads, qualification, opportunities) and billing (customers, MRR).

## Problem

Each tool answers its own question. Nobody sees the whole chain from a euro spent to a customer who stays.
Typical symptoms:

- channels are compared on lead volume or cost per lead, not on customers and revenue;
- sales complain about lead quality, marketing about sales follow-up, with no shared numbers;
- monthly reporting is assembled by hand and definitions change from month to month;
- data issues (duplicates, inconsistent labels, missing values) silently distort totals.

## Business question

> **How can management connect acquisition spend, lead quality, sales pipeline and recurring revenue in one reliable
> reporting model, to decide where to invest, what to fix and which channels deserve priority?**

## Stakeholders and what they need

| Stakeholder | Decision | What the model gives them |
|---|---|---|
| Management | Budget allocation, growth targets | Executive overview, CAC vs deal value, revenue by channel |
| Marketing | Which campaigns to scale or stop | Campaign ranking with SCALE / MAINTAIN / OPTIMISE / REDUCE |
| Sales | Which leads to call first, pipeline follow-up | Lead-score conversion, win rate, sales cycle, open pipeline |
| Finance | Payback and recurring revenue | CAC, revenue / spend, MRR, churn |
| Data / BI | Trust in the numbers | Data-quality page, documented rules, tests |

## Scope

In scope: acquisition, funnel, pipeline, first-year revenue, MRR and logo churn, data quality.
Out of scope: multi-touch attribution, lifetime value forecasting, product usage, customer support data.

## Success criteria

1. One definition per KPI, used everywhere (SQL views + DAX measures).
2. Every channel and campaign can be read on cost, quality and revenue at the same time.
3. A clear budget recommendation per paid campaign.
4. Data-quality issues are visible and corrected before reporting.
5. The workflow is reproducible end to end with one command.
