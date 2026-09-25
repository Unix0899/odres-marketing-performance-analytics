"""
Build the Power BI layer from ONE definition (this file):

  powerbi/DAX_MEASURES.md                       documentation of every measure
  powerbi/tmdl_measures_script.tmdl             script to paste in Power BI Desktop > TMDL view
  powerbi/ODRES_Marketing_Analytics/            Power BI Project (PBIP):
      ODRES_Marketing_Analytics.pbip
      ODRES_Marketing_Analytics.SemanticModel/  TMDL model: tables, types, relationships, measures
      ODRES_Marketing_Analytics.Report/         report shell with the 6 pages

The CSV folder is a model parameter (DataFolder) so the project works on any machine.
"""
import json
import shutil
import uuid

import pandas as pd

from common import DISCLOSURE, POWERBI_DATA, ROOT
from powerbi_report import build_report

PBI = ROOT / "powerbi"
NAME = "ODRES_Marketing_Analytics"
PROJECT = PBI / NAME

# --------------------------------------------------------------------------- measures (single source of truth)
# (table, name, dax, format, folder, description)
MEASURES = [
    ("FactMarketingDaily", "Total Spend", "SUM ( FactMarketingDaily[spend] )", "€ #,0", "1 Acquisition",
     "Paid media, email tool, partner and event costs."),
    ("FactMarketingDaily", "Impressions", "SUM ( FactMarketingDaily[impressions] )", "#,0", "1 Acquisition", ""),
    ("FactMarketingDaily", "Clicks", "SUM ( FactMarketingDaily[clicks] )", "#,0", "1 Acquisition", ""),
    ("FactMarketingDaily", "Sessions", "SUM ( FactMarketingDaily[sessions] )", "#,0", "1 Acquisition", ""),
    ("FactMarketingDaily", "CTR", "DIVIDE ( [Clicks], [Impressions] )", "0.00%", "1 Acquisition",
     "Click-through rate."),
    ("FactMarketingDaily", "CPC", "DIVIDE ( [Total Spend], [Clicks] )", "€ #,0.00", "1 Acquisition",
     "Cost per click."),
    ("FactLeads", "Leads", "COUNTROWS ( FactLeads )", "#,0", "2 Funnel", ""),
    ("FactLeads", "MQLs", "CALCULATE ( [Leads], FactLeads[is_mql] = 1 )", "#,0", "2 Funnel",
     "Marketing-qualified leads."),
    ("FactLeads", "SQLs", "CALCULATE ( [Leads], FactLeads[is_sql] = 1 )", "#,0", "2 Funnel",
     "Sales-qualified leads (an SQL is always an MQL)."),
    ("FactLeads", "Avg Lead Score", "AVERAGE ( FactLeads[lead_score] )", "0.0", "2 Funnel",
     "Unknown scores (blank) are ignored."),
    ("FactOpportunities", "Opportunities", "COUNTROWS ( FactOpportunities )", "#,0", "2 Funnel", ""),
    ("FactOpportunities", "Customers", "CALCULATE ( COUNTROWS ( FactOpportunities ), FactOpportunities[is_won] = 1 )",
     "#,0", "2 Funnel", "Won opportunities = new customers."),
    ("FactLeads", "Session to Lead %", "DIVIDE ( [Leads], [Sessions] )", "0.0%", "3 Conversion", ""),
    ("FactLeads", "Lead to MQL %", "DIVIDE ( [MQLs], [Leads] )", "0.0%", "3 Conversion", ""),
    ("FactLeads", "MQL to SQL %", "DIVIDE ( [SQLs], [MQLs] )", "0.0%", "3 Conversion", ""),
    ("FactLeads", "SQL to Customer %", "DIVIDE ( [Customers], [SQLs] )", "0.0%", "3 Conversion", ""),
    ("FactLeads", "Lead to Customer %", "DIVIDE ( [Customers], [Leads] )", "0.00%", "3 Conversion", ""),
    ("FactMarketingDaily", "CPL", "IF ( [Total Spend] > 0, DIVIDE ( [Total Spend], [Leads] ) )", "€ #,0.00",
     "4 Efficiency", "Cost per lead. Blank when there is no spend (not applicable), never 0."),
    ("FactMarketingDaily", "CAC", "IF ( [Total Spend] > 0, DIVIDE ( [Total Spend], [Customers] ) )", "€ #,0",
     "4 Efficiency", "Customer acquisition cost. Blank when there is no spend."),
    ("FactMarketingDaily", "Revenue / Spend", "DIVIDE ( [Won Revenue], [Total Spend] )", "0.0x", "4 Efficiency",
     "First-year revenue per euro spent."),
    ("FactOpportunities", "Won Revenue",
     "CALCULATE ( SUM ( FactOpportunities[won_value] ), FactOpportunities[is_won] = 1 )", "€ #,0", "5 Revenue",
     "First-year contract value of won deals, by revenue_date_key."),
    ("FactOpportunities", "Average Deal Value", "DIVIDE ( [Won Revenue], [Customers] )", "€ #,0", "5 Revenue", ""),
    ("FactOpportunities", "Average Sales Cycle",
     "CALCULATE ( AVERAGE ( FactOpportunities[sales_cycle_days] ), FactOpportunities[is_won] = 1 )", "0.0",
     "5 Revenue", "Days from opportunity creation to close (won deals, known dates only)."),
    ("FactOpportunities", "Win Rate",
     'DIVIDE ( [Customers], CALCULATE ( COUNTROWS ( FactOpportunities ), '
     'FactOpportunities[status] IN { "Won", "Lost" } ) )', "0.0%", "5 Revenue", "Won / closed opportunities."),
    ("FactOpportunities", "Open Pipeline",
     'CALCULATE ( SUM ( FactOpportunities[expected_value] ), FactOpportunities[status] = "Open" )', "€ #,0",
     "5 Revenue", ""),
    ("FactOpportunities", "Lost Value",
     'CALCULATE ( SUM ( FactOpportunities[expected_value] ), FactOpportunities[status] = "Lost" )', "€ #,0",
     "5 Revenue", ""),
    ("FactCustomerMonthly", "MRR",
     "CALCULATE ( SUM ( FactCustomerMonthly[mrr] ), FactCustomerMonthly[is_active] = 1 )", "€ #,0",
     "6 Customers", "Monthly recurring revenue of active customers (sum over the months in context)."),
    ("FactCustomerMonthly", "MRR (end of period)",
     "VAR LastMonth = MAX ( FactCustomerMonthly[month_key] )\nRETURN\n    CALCULATE ( [MRR], "
     "FactCustomerMonthly[month_key] = LastMonth )", "€ #,0", "6 Customers",
     "MRR of the last month in the filter context: use this one on cards."),
    ("FactCustomerMonthly", "Active Customers",
     "CALCULATE ( DISTINCTCOUNT ( FactCustomerMonthly[customer_id] ), FactCustomerMonthly[is_active] = 1 )", "#,0",
     "6 Customers", ""),
    ("FactCustomerMonthly", "Churned Customers", "SUM ( FactCustomerMonthly[is_churned] )", "#,0", "6 Customers", ""),
    ("FactCustomerMonthly", "Churn Rate", "DIVIDE ( [Churned Customers], [Active Customers] + [Churned Customers] )",
     "0.0%", "6 Customers", "Logo churn: churned / (active + churned)."),
    ("FactLeads", "MoM Leads %",
     "VAR CurrentLeads = [Leads]\nVAR PreviousLeads = CALCULATE ( [Leads], DATEADD ( DimDate[date], -1, MONTH ) )\n"
     "RETURN\n    DIVIDE ( CurrentLeads - PreviousLeads, PreviousLeads )", "+0.0%;-0.0%;0.0%", "7 Trend",
     "Month-over-month change. Use with DimDate[year_month] on the axis."),
    ("FactOpportunities", "MoM Revenue %",
     "VAR CurrentRevenue = [Won Revenue]\nVAR PreviousRevenue = CALCULATE ( [Won Revenue], "
     "DATEADD ( DimDate[date], -1, MONTH ) )\nRETURN\n    DIVIDE ( CurrentRevenue - PreviousRevenue, PreviousRevenue )",
     "+0.0%;-0.0%;0.0%", "7 Trend", ""),
    ("DataQualityChecks", "Issues Found (raw)", "SUM ( DataQualityChecks[raw] )", "#,0", "8 Data quality", ""),
    ("DataQualityChecks", "Blocking Errors Left",
     'CALCULATE ( SUM ( DataQualityChecks[clean] ), DataQualityChecks[severity] = "BLOCKING" )', "#,0",
     "8 Data quality", "Must be 0."),
    ("DataQualityChecks", "Documented Warnings",
     'CALCULATE ( SUM ( DataQualityChecks[clean] ), DataQualityChecks[severity] = "WARNING" )', "#,0",
     "8 Data quality", ""),
    ("DataQualityRowCounts", "Rows Loaded", "SUM ( DataQualityRowCounts[clean_rows] )", "#,0", "8 Data quality", ""),
    ("DataQualityRowCounts", "Rows Removed", "SUM ( DataQualityRowCounts[removed] )", "#,0", "8 Data quality", ""),
]

# --------------------------------------------------------------------------- tables
PANDAS_TO_TMDL = {"int64": ("int64", "Int64.Type"), "float64": ("double", "type number"),
                  "object": ("string", "type text"), "str": ("string", "type text"),
                  "string": ("string", "type text")}
KEY_COLUMNS = {"DimDate": "date", "DimChannel": "channel_id", "DimCampaign": "campaign_id",
               "DimRegion": "region_id", "DimCustomer": "customer_id"}
HIDDEN = {"sort_order", "value_imputed", "month_key", "created_date_key", "close_date_key", "revenue_date_key",
          "date_key", "channel_id", "campaign_id", "region_id", "customer_id", "lead_id", "opportunity_id",
          "acquisition_date_key"}

RELATIONSHIPS = [  # (from table, from column, to table, to column, active)
    ("FactMarketingDaily", "date_key", "DimDate", "date_key", True),
    ("FactLeads", "created_date_key", "DimDate", "date_key", True),
    ("FactOpportunities", "revenue_date_key", "DimDate", "date_key", True),
    ("FactCustomerMonthly", "month_key", "DimDate", "date_key", True),
    ("FactMarketingDaily", "channel_id", "DimChannel", "channel_id", True),
    ("FactLeads", "channel_id", "DimChannel", "channel_id", True),
    ("FactOpportunities", "channel_id", "DimChannel", "channel_id", True),
    ("DimCustomer", "channel_id", "DimChannel", "channel_id", True),
    ("FactMarketingDaily", "campaign_id", "DimCampaign", "campaign_id", True),
    ("FactLeads", "campaign_id", "DimCampaign", "campaign_id", True),
    ("FactOpportunities", "campaign_id", "DimCampaign", "campaign_id", True),
    ("DimCustomer", "campaign_id", "DimCampaign", "campaign_id", True),
    ("FactLeads", "region_id", "DimRegion", "region_id", True),
    ("FactOpportunities", "region_id", "DimRegion", "region_id", True),
    ("DimCustomer", "region_id", "DimRegion", "region_id", True),
    ("FactCustomerMonthly", "customer_id", "DimCustomer", "customer_id", True),
]

# Report helpers: measures used by specific visuals of the 6-page report
MEASURES += [
    ("FactMarketingDaily", "Paid Spend", "CALCULATE ( [Total Spend], DimChannel[is_paid] = 1 )", "€ #,0",
     "9 Report helpers", "Spend of paid media channels only."),
    ("FactMarketingDaily", "Paid CAC", "CALCULATE ( [CAC], DimChannel[is_paid] = 1 )", "€ #,0", "9 Report helpers",
     "CAC of paid media channels only."),
    ("FactOpportunities", "Non-paid Revenue Share",
     "DIVIDE ( CALCULATE ( [Won Revenue], DimChannel[is_paid] = 0 ), [Won Revenue] )", "0%", "9 Report helpers",
     "Share of won revenue coming from channels without paid media."),
    ("FactLeads", "Share of Leads", "DIVIDE ( [Leads], CALCULATE ( [Leads], ALL ( DimChannel ) ) )", "0.0%",
     "9 Report helpers", "Share of all leads (by channel)."),
    ("FactOpportunities", "Share of Customers",
     "DIVIDE ( [Customers], CALCULATE ( [Customers], ALL ( DimChannel ) ) )", "0.0%", "9 Report helpers",
     "Share of all customers (by channel)."),
    ("FactCustomerMonthly", "ARR Run-rate", "[MRR (end of period)] * 12", "€ #,0", "9 Report helpers",
     "Annual run-rate = end-of-period MRR x 12."),
    ("FactMarketingDaily", "Campaigns to Scale",
     'CALCULATE ( COUNTROWS ( DimCampaign ), DimCampaign[Recommendation] = "SCALE" ) + 0', "0", "9 Report helpers", ""),
    ("FactMarketingDaily", "Campaigns to Reduce",
     'CALCULATE ( COUNTROWS ( DimCampaign ), DimCampaign[Recommendation] = "REDUCE" ) + 0', "0", "9 Report helpers", ""),
    ("DataQualityChecks", "Issues After Cleaning", "SUM ( DataQualityChecks[clean] )", "#,0", "8 Data quality", ""),
]

# Calculated columns: (table, name, dax, dataType)
CALC_COLUMNS = [
    ("DimCampaign", "Recommendation",
     "VAR ChannelId = DimCampaign[channel_id]\n"
     "VAR IsPaid = LOOKUPVALUE ( DimChannel[is_paid], DimChannel[channel_id], ChannelId )\n"
     "VAR Spend = CALCULATE ( [Total Spend] )\n"
     "VAR Ratio = DIVIDE ( CALCULATE ( [Won Revenue] ), Spend )\n"
     "VAR SqlRate = DIVIDE ( CALCULATE ( [SQLs] ), CALCULATE ( [Leads] ) )\n"
     "VAR ChannelSqlRate =\n"
     "    AVERAGEX (\n"
     "        FILTER ( ALL ( DimCampaign ), DimCampaign[channel_id] = ChannelId ),\n"
     "        DIVIDE ( CALCULATE ( [SQLs] ), CALCULATE ( [Leads] ) )\n"
     "    )\n"
     "RETURN\n"
     "    SWITCH (\n"
     "        TRUE (),\n"
     '        ISBLANK ( ChannelId ), "UNASSIGNED",\n'
     '        IsPaid = 0, "NON-PAID",\n'
     '        Ratio >= 1.5 && SqlRate >= ChannelSqlRate, "SCALE",\n'
     '        Ratio >= 1.0, "MAINTAIN",\n'
     '        Ratio >= 0.5, "OPTIMISE",\n'
     '        "REDUCE"\n'
     "    )", "string"),
    ("FactLeads", "Score Band",
     "SWITCH (\n    TRUE (),\n"
     '    ISBLANK ( FactLeads[lead_score] ), "Unknown",\n'
     '    FactLeads[lead_score] >= 80, "80-100",\n'
     '    FactLeads[lead_score] >= 60, "60-79",\n'
     '    FactLeads[lead_score] >= 40, "40-59",\n'
     '    "0-39"\n)', "string"),
]

# Power BI names are case-insensitive: a measure "Impressions" cannot live next to a column "impressions".
# These columns get a model name of their own (the CSV header stays the same, via sourceColumn).
COLUMN_RENAMES = {
    ("FactMarketingDaily", "impressions"): "impressions_count",
    ("FactMarketingDaily", "clicks"): "clicks_count",
    ("FactMarketingDaily", "sessions"): "sessions_count",
    ("FactCustomerMonthly", "mrr"): "mrr_amount",
}
for (_t, _old), _new in COLUMN_RENAMES.items():
    MEASURES = [(t, m, dax.replace(f"{_t}[{_old}]", f"{_t}[{_new}]"), fmt, f, d) for t, m, dax, fmt, f, d in MEASURES]

PAGES = ["Executive Overview", "Acquisition Funnel", "Channel & Campaign Performance", "Pipeline & Revenue",
         "Customer Value", "Data Quality"]


def tag() -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "odres-" + tag.counter.__next__().__str__()))


tag.counter = iter(range(1, 100000))


def tmdl_table(name: str, df: pd.DataFrame) -> str:
    lines = [f"table {name}", f"\tlineageTag: {tag()}", ""]
    for t, m, dax, fmt, folder, desc in MEASURES:
        if t != name:
            continue
        if desc:
            lines.append(f"\t/// {desc}")
        if "\n" in dax:
            lines.append(f"\tmeasure '{m}' =")
            lines += ["\t\t\t" + d for d in dax.split("\n")]
        else:
            lines.append(f"\tmeasure '{m}' = {dax}")
        lines += [f'\t\tformatString: "{fmt}"', f"\t\tdisplayFolder: {folder}", f"\t\tlineageTag: {tag()}", ""]
    types = []
    for col, dtype in df.dtypes.items():
        whole = str(dtype) == "float64" and (df[col].dropna() % 1 == 0).all()
        if name == "DimDate" and col == "date":
            tm, mt = "dateTime", "type date"
        elif whole:                                  # integer column with blanks: pandas reads it as float
            tm, mt = "int64", "Int64.Type"
        else:
            tm, mt = PANDAS_TO_TMDL.get(str(dtype), ("string", "type text"))
        types.append((col, mt))
        model_col = COLUMN_RENAMES.get((name, col), col)
        lines.append(f"\tcolumn {model_col}")
        lines.append(f"\t\tdataType: {tm}")
        if tm == "dateTime":
            lines.append("\t\tformatString: dd/mm/yyyy")
        if name in KEY_COLUMNS and KEY_COLUMNS[name] == col:
            lines.append("\t\tisKey")
        if col in HIDDEN or (name, col) in COLUMN_RENAMES:
            lines.append("\t\tisHidden")
        lines.append(f"\t\tsummarizeBy: {'none' if tm != 'double' else 'sum'}")
        if name == "DimChannel" and col == "channel_name":
            lines.append("\t\tsortByColumn: sort_order")
        if name == "DimDate" and col == "month_name":
            lines.append("\t\tsortByColumn: month")
        lines += [f"\t\tsourceColumn: {col}", f"\t\tlineageTag: {tag()}", ""]
    for t, cname, dax, dtype in CALC_COLUMNS:
        if t != name:
            continue
        lines.append(f"\tcolumn '{cname}' =")
        lines += ["\t\t\t" + d for d in dax.split("\n")]
        lines += [f"\t\tdataType: {dtype}", "\t\tsummarizeBy: none", f"\t\tlineageTag: {tag()}", ""]
    type_list = ", ".join(f'{{"{c}", {t}}}' for c, t in types)
    lines += [f"\tpartition {name} = m", "\t\tmode: import", "\t\tsource =",
              "\t\t\t\tlet",
              f'\t\t\t\t    Source = Csv.Document(File.Contents(DataFolder & "{name}.csv"), '
              '[Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
              "\t\t\t\t    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),",
              "\t\t\t\t    EmptyToNull = Table.ReplaceValue(Promoted, \"\", null, Replacer.ReplaceValue, "
              "Table.ColumnNames(Promoted)),",
              f'\t\t\t\t    Typed = Table.TransformColumnTypes(EmptyToNull, {{{type_list}}}, "en-US")',
              "\t\t\t\tin",
              "\t\t\t\t    Typed", ""]
    if name == "DimDate":
        lines.insert(2, "\tdataCategory: Time")
    return "\n".join(lines)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_project(tables: dict):
    if PROJECT.exists():
        shutil.rmtree(PROJECT)                 # generated artefact, rebuilt every run
    sm = PROJECT / f"{NAME}.SemanticModel"
    rp = PROJECT / f"{NAME}.Report"
    write(PROJECT / f"{NAME}.pbip", json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
        "settings": {"enableAutoRecovery": True}}, indent=2))
    write(sm / "definition.pbism", json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.2", "settings": {"qnaEnabled": False}}, indent=2))
    write(sm / "definition" / "database.tmdl", "database\n\tcompatibilityLevel: 1567\n")
    folder = str(POWERBI_DATA) + "\\"                 # M strings do not escape backslashes
    write(sm / "definition" / "expressions.tmdl",
          "/// Folder that contains the CSV exports (powerbi/data). Change it after cloning the repository.\n"
          f'expression DataFolder = "{folder}" meta [IsParameterQuery = true, Type = "Text", '
          'IsParameterQueryRequired = true]\n'
          f"\tlineageTag: {tag()}\n")
    model = [f"/// {DISCLOSURE}", "model Model", "\tculture: en-US",
             "\tdefaultPowerBIDataSourceVersion: powerBI_V3", "\tdiscourageImplicitMeasures",
             "\tsourceQueryCulture: en-US", "", "\tannotation Disclosure = Synthetic data - not ODRES figures", ""]
    model += [f"ref table {t}" for t in tables]
    write(sm / "definition" / "model.tmdl", "\n".join(model) + "\n")
    for name, df in tables.items():
        write(sm / "definition" / "tables" / f"{name}.tmdl", tmdl_table(name, df))
    rel = []
    for ft, fc, tt, tc, active in RELATIONSHIPS:
        rel += [f"relationship {tag()}", f"\tfromColumn: {ft}.{fc}", f"\ttoColumn: {tt}.{tc}"]
        if not active:
            rel.append("\tisActive: false")
        rel.append("")
    write(sm / "definition" / "relationships.tmdl", "\n".join(rel))

    # Report (PBIR-legacy report.json): the 6 pages of DASHBOARD_SPEC.md with their visuals
    write(rp / "definition.pbir", json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}}, indent=2))
    report = build_report({m: t for t, m, *_ in MEASURES})
    assert [s["displayName"] for s in report["sections"]] == PAGES
    write(rp / "report.json", json.dumps(report, indent=2, ensure_ascii=False))


def write_docs():
    lines = ["# DAX measures", "", f"> {DISCLOSURE}", "",
             f"{len(MEASURES)} measures, generated from `src/build_powerbi_project.py` (single source of truth: the "
             "same definitions produce this page, the TMDL model and the paste-in script).", "",
             "Conventions: `DIVIDE()` everywhere (no division errors); efficiency ratios return **blank** "
             "when there is no spend, never 0; measures live in their home fact table, grouped in display folders.", ""]
    folder = None
    for t, m, dax, fmt, f, desc in MEASURES:
        if f != folder:
            lines += [f"## {f[2:]}", ""]
            folder = f
        lines += [f"### {m}", "", f"Table `{t}` · format `{fmt}`" + (f" · {desc}" if desc else ""), "",
                  "```DAX", f"{m} =", *("    " + d for d in dax.split("\n")), "```", ""]
    write(PBI / "DAX_MEASURES.md", "\n".join(lines))
    script = ["createOrReplace", ""]
    for t, m, dax, fmt, f, desc in MEASURES:
        script += [f"\tref table {t}", ""]
        if "\n" in dax:
            script += [f"\t\tmeasure '{m}' ="] + ["\t\t\t\t" + d for d in dax.split("\n")]
        else:
            script.append(f"\t\tmeasure '{m}' = {dax}")
        script += [f'\t\t\tformatString: "{fmt}"', f"\t\t\tdisplayFolder: {f}", ""]
    write(PBI / "tmdl_measures_script.tmdl", "\n".join(script))


def check_names(tables: dict):
    """Power BI rejects a measure whose name matches a column of its table (case-insensitive),
    and measure names must be unique in the whole model."""
    problems = []
    seen = {}
    for t, m, *_ in MEASURES:
        cols = {COLUMN_RENAMES.get((t, c), c).lower() for c in tables[t].columns}
        cols |= {cname.lower() for ct, cname, *_ in CALC_COLUMNS if ct == t}
        if m.lower() in cols:
            problems.append(f"measure '{m}' clashes with a column of {t}")
        if m.lower() in seen:
            problems.append(f"measure '{m}' defined twice ({seen[m.lower()]}, {t})")
        seen[m.lower()] = t
    if problems:
        raise SystemExit("Name conflicts:\n  " + "\n  ".join(problems))


def main():
    tables = {p.stem: pd.read_csv(p) for p in sorted(POWERBI_DATA.glob("*.csv"))}
    order = ["DimDate", "DimChannel", "DimCampaign", "DimRegion", "DimCustomer", "FactMarketingDaily", "FactLeads",
             "FactOpportunities", "FactCustomerMonthly", "DataQualityChecks", "DataQualityRowCounts", "CleaningLog"]
    tables = {k: tables[k] for k in order}
    check_names(tables)
    build_project(tables)
    write_docs()
    print(f"PBIP written: {PROJECT.relative_to(ROOT)} ({len(tables)} tables, {len(MEASURES)} measures, "
          f"{len(RELATIONSHIPS)} relationships)")


if __name__ == "__main__":
    main()
