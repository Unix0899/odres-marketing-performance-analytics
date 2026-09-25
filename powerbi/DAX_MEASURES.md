# DAX measures

> Professional context based on a real ODRES Group experience. Public technical reconstruction using synthetic data.

47 measures, generated from `src/build_powerbi_project.py` (single source of truth: the same definitions produce this page, the TMDL model and the paste-in script).

Conventions: `DIVIDE()` everywhere (no division errors); efficiency ratios return **blank** when there is no spend, never 0; measures live in their home fact table, grouped in display folders.

## Acquisition

### Total Spend

Table `FactMarketingDaily` · format `€ #,0` · Paid media, email tool, partner and event costs.

```DAX
Total Spend =
    SUM ( FactMarketingDaily[spend] )
```

### Impressions

Table `FactMarketingDaily` · format `#,0`

```DAX
Impressions =
    SUM ( FactMarketingDaily[impressions_count] )
```

### Clicks

Table `FactMarketingDaily` · format `#,0`

```DAX
Clicks =
    SUM ( FactMarketingDaily[clicks_count] )
```

### Sessions

Table `FactMarketingDaily` · format `#,0`

```DAX
Sessions =
    SUM ( FactMarketingDaily[sessions_count] )
```

### CTR

Table `FactMarketingDaily` · format `0.00%` · Click-through rate.

```DAX
CTR =
    DIVIDE ( [Clicks], [Impressions] )
```

### CPC

Table `FactMarketingDaily` · format `€ #,0.00` · Cost per click.

```DAX
CPC =
    DIVIDE ( [Total Spend], [Clicks] )
```

## Funnel

### Leads

Table `FactLeads` · format `#,0`

```DAX
Leads =
    COUNTROWS ( FactLeads )
```

### MQLs

Table `FactLeads` · format `#,0` · Marketing-qualified leads.

```DAX
MQLs =
    CALCULATE ( [Leads], FactLeads[is_mql] = 1 )
```

### SQLs

Table `FactLeads` · format `#,0` · Sales-qualified leads (an SQL is always an MQL).

```DAX
SQLs =
    CALCULATE ( [Leads], FactLeads[is_sql] = 1 )
```

### Avg Lead Score

Table `FactLeads` · format `0.0` · Unknown scores (blank) are ignored.

```DAX
Avg Lead Score =
    AVERAGE ( FactLeads[lead_score] )
```

### Opportunities

Table `FactOpportunities` · format `#,0`

```DAX
Opportunities =
    COUNTROWS ( FactOpportunities )
```

### Customers

Table `FactOpportunities` · format `#,0` · Won opportunities = new customers.

```DAX
Customers =
    CALCULATE ( COUNTROWS ( FactOpportunities ), FactOpportunities[is_won] = 1 )
```

## Conversion

### Session to Lead %

Table `FactLeads` · format `0.0%`

```DAX
Session to Lead % =
    DIVIDE ( [Leads], [Sessions] )
```

### Lead to MQL %

Table `FactLeads` · format `0.0%`

```DAX
Lead to MQL % =
    DIVIDE ( [MQLs], [Leads] )
```

### MQL to SQL %

Table `FactLeads` · format `0.0%`

```DAX
MQL to SQL % =
    DIVIDE ( [SQLs], [MQLs] )
```

### SQL to Customer %

Table `FactLeads` · format `0.0%`

```DAX
SQL to Customer % =
    DIVIDE ( [Customers], [SQLs] )
```

### Lead to Customer %

Table `FactLeads` · format `0.00%`

```DAX
Lead to Customer % =
    DIVIDE ( [Customers], [Leads] )
```

## Efficiency

### CPL

Table `FactMarketingDaily` · format `€ #,0.00` · Cost per lead. Blank when there is no spend (not applicable), never 0.

```DAX
CPL =
    IF ( [Total Spend] > 0, DIVIDE ( [Total Spend], [Leads] ) )
```

### CAC

Table `FactMarketingDaily` · format `€ #,0` · Customer acquisition cost. Blank when there is no spend.

```DAX
CAC =
    IF ( [Total Spend] > 0, DIVIDE ( [Total Spend], [Customers] ) )
```

### Revenue / Spend

Table `FactMarketingDaily` · format `0.0x` · First-year revenue per euro spent.

```DAX
Revenue / Spend =
    DIVIDE ( [Won Revenue], [Total Spend] )
```

## Revenue

### Won Revenue

Table `FactOpportunities` · format `€ #,0` · First-year contract value of won deals, by revenue_date_key.

```DAX
Won Revenue =
    CALCULATE ( SUM ( FactOpportunities[won_value] ), FactOpportunities[is_won] = 1 )
```

### Average Deal Value

Table `FactOpportunities` · format `€ #,0`

```DAX
Average Deal Value =
    DIVIDE ( [Won Revenue], [Customers] )
```

### Average Sales Cycle

Table `FactOpportunities` · format `0.0` · Days from opportunity creation to close (won deals, known dates only).

```DAX
Average Sales Cycle =
    CALCULATE ( AVERAGE ( FactOpportunities[sales_cycle_days] ), FactOpportunities[is_won] = 1 )
```

### Win Rate

Table `FactOpportunities` · format `0.0%` · Won / closed opportunities.

```DAX
Win Rate =
    DIVIDE ( [Customers], CALCULATE ( COUNTROWS ( FactOpportunities ), FactOpportunities[status] IN { "Won", "Lost" } ) )
```

### Open Pipeline

Table `FactOpportunities` · format `€ #,0`

```DAX
Open Pipeline =
    CALCULATE ( SUM ( FactOpportunities[expected_value] ), FactOpportunities[status] = "Open" )
```

### Lost Value

Table `FactOpportunities` · format `€ #,0`

```DAX
Lost Value =
    CALCULATE ( SUM ( FactOpportunities[expected_value] ), FactOpportunities[status] = "Lost" )
```

## Customers

### MRR

Table `FactCustomerMonthly` · format `€ #,0` · Monthly recurring revenue of active customers (sum over the months in context).

```DAX
MRR =
    CALCULATE ( SUM ( FactCustomerMonthly[mrr_amount] ), FactCustomerMonthly[is_active] = 1 )
```

### MRR (end of period)

Table `FactCustomerMonthly` · format `€ #,0` · MRR of the last month in the filter context: use this one on cards.

```DAX
MRR (end of period) =
    VAR LastMonth = MAX ( FactCustomerMonthly[month_key] )
    RETURN
        CALCULATE ( [MRR], FactCustomerMonthly[month_key] = LastMonth )
```

### Active Customers

Table `FactCustomerMonthly` · format `#,0`

```DAX
Active Customers =
    CALCULATE ( DISTINCTCOUNT ( FactCustomerMonthly[customer_id] ), FactCustomerMonthly[is_active] = 1 )
```

### Churned Customers

Table `FactCustomerMonthly` · format `#,0`

```DAX
Churned Customers =
    SUM ( FactCustomerMonthly[is_churned] )
```

### Churn Rate

Table `FactCustomerMonthly` · format `0.0%` · Logo churn: churned / (active + churned).

```DAX
Churn Rate =
    DIVIDE ( [Churned Customers], [Active Customers] + [Churned Customers] )
```

## Trend

### MoM Leads %

Table `FactLeads` · format `+0.0%;-0.0%;0.0%` · Month-over-month change. Use with DimDate[year_month] on the axis.

```DAX
MoM Leads % =
    VAR CurrentLeads = [Leads]
    VAR PreviousLeads = CALCULATE ( [Leads], DATEADD ( DimDate[date], -1, MONTH ) )
    RETURN
        DIVIDE ( CurrentLeads - PreviousLeads, PreviousLeads )
```

### MoM Revenue %

Table `FactOpportunities` · format `+0.0%;-0.0%;0.0%`

```DAX
MoM Revenue % =
    VAR CurrentRevenue = [Won Revenue]
    VAR PreviousRevenue = CALCULATE ( [Won Revenue], DATEADD ( DimDate[date], -1, MONTH ) )
    RETURN
        DIVIDE ( CurrentRevenue - PreviousRevenue, PreviousRevenue )
```

## Data quality

### Issues Found (raw)

Table `DataQualityChecks` · format `#,0`

```DAX
Issues Found (raw) =
    SUM ( DataQualityChecks[raw] )
```

### Blocking Errors Left

Table `DataQualityChecks` · format `#,0` · Must be 0.

```DAX
Blocking Errors Left =
    CALCULATE ( SUM ( DataQualityChecks[clean] ), DataQualityChecks[severity] = "BLOCKING" )
```

### Documented Warnings

Table `DataQualityChecks` · format `#,0`

```DAX
Documented Warnings =
    CALCULATE ( SUM ( DataQualityChecks[clean] ), DataQualityChecks[severity] = "WARNING" )
```

### Rows Loaded

Table `DataQualityRowCounts` · format `#,0`

```DAX
Rows Loaded =
    SUM ( DataQualityRowCounts[clean_rows] )
```

### Rows Removed

Table `DataQualityRowCounts` · format `#,0`

```DAX
Rows Removed =
    SUM ( DataQualityRowCounts[removed] )
```

## Report helpers

### Paid Spend

Table `FactMarketingDaily` · format `€ #,0` · Spend of paid media channels only.

```DAX
Paid Spend =
    CALCULATE ( [Total Spend], DimChannel[is_paid] = 1 )
```

### Paid CAC

Table `FactMarketingDaily` · format `€ #,0` · CAC of paid media channels only.

```DAX
Paid CAC =
    CALCULATE ( [CAC], DimChannel[is_paid] = 1 )
```

### Non-paid Revenue Share

Table `FactOpportunities` · format `0%` · Share of won revenue coming from channels without paid media.

```DAX
Non-paid Revenue Share =
    DIVIDE ( CALCULATE ( [Won Revenue], DimChannel[is_paid] = 0 ), [Won Revenue] )
```

### Share of Leads

Table `FactLeads` · format `0.0%` · Share of all leads (by channel).

```DAX
Share of Leads =
    DIVIDE ( [Leads], CALCULATE ( [Leads], ALL ( DimChannel ) ) )
```

### Share of Customers

Table `FactOpportunities` · format `0.0%` · Share of all customers (by channel).

```DAX
Share of Customers =
    DIVIDE ( [Customers], CALCULATE ( [Customers], ALL ( DimChannel ) ) )
```

### ARR Run-rate

Table `FactCustomerMonthly` · format `€ #,0` · Annual run-rate = end-of-period MRR x 12.

```DAX
ARR Run-rate =
    [MRR (end of period)] * 12
```

### Campaigns to Scale

Table `FactMarketingDaily` · format `0`

```DAX
Campaigns to Scale =
    CALCULATE ( COUNTROWS ( DimCampaign ), DimCampaign[Recommendation] = "SCALE" ) + 0
```

### Campaigns to Reduce

Table `FactMarketingDaily` · format `0`

```DAX
Campaigns to Reduce =
    CALCULATE ( COUNTROWS ( DimCampaign ), DimCampaign[Recommendation] = "REDUCE" ) + 0
```

## Data quality

### Issues After Cleaning

Table `DataQualityChecks` · format `#,0`

```DAX
Issues After Cleaning =
    SUM ( DataQualityChecks[clean] )
```
