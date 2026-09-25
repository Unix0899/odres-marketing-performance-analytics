# Key insights

> Professional context based on a real ODRES Group experience. Public technical reconstruction using synthetic data.
>
> **These are findings of the synthetic demonstration dataset, not ODRES results.** The generator was designed
> with realistic B2B SaaS trade-offs so that the analysis has decisions to make. What this page demonstrates is the
> *reasoning*: from a number, to its business meaning, to a recommendation that can be tested.

Period analysed: 1 Nov 2025 – 30 Jun 2026 · 5,477 leads · 1,222 opportunities · 350 new customers ·
€112,851 spend · €751,031 first-year won revenue.

---

## 1. Lead volume is a misleading KPI

**Observation.** In the synthetic demonstration dataset, Meta Ads is the largest source of leads but one of the
smallest sources of customers.

**Evidence.** Meta Ads brings 1,533 leads (28.0% of all leads) but 7 customers (2.0%). Its lead-to-SQL rate is 4.4%
against 27.3% company-wide, 71.9% of its leads score below 40, and its CAC is €3,534 for an average first-year deal
of €892. (`sql/06_funnel_analysis.sql` Q19b, `sql/04_kpi_queries.sql` Q04 and Q14)

**Business impact.** A report that celebrates lead volume would push budget towards the channel that converts
worst. Sales time is also consumed by leads that almost never close.

**Recommendation.** Stop using "leads" as the headline acquisition KPI. Report leads next to SQL rate, CAC and won
revenue on the same page (Executive Overview), and set channel targets on SQLs, not on leads.

---

## 2. Four paid campaigns absorb a third of the budget and return almost nothing

**Observation.** In the synthetic demonstration dataset, a small group of paid campaigns spends heavily without
producing customers.

**Evidence.** The 4 campaigns flagged **REDUCE** (Awareness Video, Competitor Search, Lead Magnet, SMB Growth) spent
€37,626 (33% of total spend) for €6,704 of first-year revenue. Awareness Video alone: €13,645, 931 leads,
24 SQLs (2.6%), 3 customers, CAC €4,548. Competitor Search: €11,057, CAC €3,686.
(`sql/05_campaign_analysis.sql` Q18 and Q18b, rule in `vw_campaign_performance`)

**Business impact.** Roughly €38k could be reallocated without touching the campaigns that actually produce
customers.

**Recommendation.** Pause Awareness Video and Competitor Search first (largest spend, weakest conversion), keep
Lead Magnet only as a nurture entry point, and move the budget to the campaigns flagged **SCALE**. Measure with a
3-month test and a hold-out region before a permanent change.

---

## 3. A higher CAC can still be the better investment

**Observation.** In the synthetic demonstration dataset, LinkedIn Ads is expensive per lead but brings the most
valuable customers.

**Evidence.** LinkedIn Ads: CPL €190, CAC €1,333, but the highest average deal (€3,398), a 40% win rate and a 57%
lead-to-SQL rate. Its 2 campaigns are both flagged **SCALE** (€21,210 spent → €67,952 revenue).
Google Ads has a similar CAC (€1,600) with smaller deals (€1,868). (`sql/07_revenue_analysis.sql` Q12,
`sql/04_kpi_queries.sql` Q04)

**Business impact.** Comparing channels on CPL alone would cut the channel that reaches larger, multi-site
hospitality groups.

**Recommendation.** Judge paid channels on CAC relative to deal value (`deal_value_to_cac` in Q04), not on CPL.
Increase LinkedIn budget gradually on "Operations Leaders" while watching whether CAC stays below first-year deal
value as volume grows.

---

## 4. Non-paid channels produce most of the revenue

**Observation.** In the synthetic demonstration dataset, referral, email and organic search outperform paid media
on every efficiency metric.

**Evidence.** Non-paid channels: 18% of spend (€19,861: email tool, partner fees, events), 84% of won revenue
(€628,257), 9.1% lead-to-customer, CAC €67. Paid channels: €92,990, 16% of revenue, 2.4% lead-to-customer,
CAC €1,755. Referral alone: 10% of leads, 31% of customers, 61% SQL rate. (`sql/04_kpi_queries.sql` Q20,
`sql/06_funnel_analysis.sql` Q19)

**Business impact.** Growth is currently carried by channels that are hard to scale quickly (referrals, partners).
Paid media is not yet an efficient growth engine.

**Recommendation.** Formalise a customer-referral programme and expand the partner network (lowest CAC, highest
quality). Keep investing in SEO comparison pages and lead nurture emails, which convert well at almost no marginal
cost.

---

## 5. The lead score works and should route sales effort

**Observation.** In the synthetic demonstration dataset, the CRM lead score is strongly predictive of conversion.

**Evidence.** Lead → customer: 0.8% for scores 0–39, 4.2% for 40–59, 9.8% for 60–79, 20.9% for 80–100.
The 449 leads scoring 80+ convert 27 times better than the 1,443 leads below 40.
(`sql/06_funnel_analysis.sql` Q14b)

**Business impact.** Treating every lead the same wastes sales time on leads that almost never convert.

**Recommendation.** Route scores 60+ to sales within 24 hours; send scores below 40 to automated nurture only.
Review the scoring model quarterly with the same query.

---

## 6. Larger customers are few, slow and worth a lot

**Observation.** In the synthetic demonstration dataset, company size drives deal value much more than region does.

**Evidence.** Companies with 50+ staff: 10% of leads, 36 customers, average deal €8,999, 43% of revenue, won sales
cycle 37 days. Companies with 1–9 staff: 57% of leads, average deal €781, cycle 15 days. Regions, by contrast,
convert within a narrow band (5.6%–8.0%); the differences in regional revenue come from a few large multi-site
deals, not from a structural gap. (`sql/07_revenue_analysis.sql` Q13, Q21, Q22)

**Business impact.** One sales process for every segment either rushes large accounts or over-serves small ones.
No region needs to be deprioritised.

**Recommendation.** Split the pipeline: a fast, low-touch process for 1–9 staff and an account-based approach
(demo, multi-site pricing, longer follow-up) for 50+. Keep national coverage.

---

## Limits of these insights

- Synthetic data: the patterns were designed to be realistic, not measured at ODRES.
- Attribution is first-touch (the lead's source in the CRM). Multi-touch journeys are not modelled.
- Revenue is first-year contract value; lifetime value would favour channels with lower churn.
- Some groups are small (7 Meta customers, 20 LinkedIn customers): recommendations are framed as tests.
