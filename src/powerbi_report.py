"""
Report layout for the Power BI project: the 6 pages of powerbi/DASHBOARD_SPEC.md written as a
PBIR-legacy report.json (sections -> visualContainers), the format Power BI Desktop opens from a PBIP.

Canvas 1280 x 720. Style: light grey page, white bordered cards, navy / teal.
Every page: title, synced slicers (month, channel, campaign), footer "synthetic data".
"""
import itertools
import json

NAVY, TEAL, TEAL2, GREY, AMBER, RED, INK, MUTED, BORDER, PAGE_BG = (
    "#0D2A45", "#0F8B8D", "#65B8B5", "#C9D3DC", "#C7851A", "#B5473A", "#102033", "#607086", "#DCE4EA", "#F6F8FA")

_ids = itertools.count(1)


# --------------------------------------------------------------------------- literals
def lit(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


def text(s: str) -> dict:
    return lit("'" + s.replace("'", "''") + "'")


def color(hex_code: str) -> dict:
    return {"solid": {"color": text(hex_code)}}


TRUE, FALSE = lit("true"), lit("false")


# --------------------------------------------------------------------------- fields
class Report:
    def __init__(self, measure_home: dict):
        self.measure_home = measure_home          # measure name -> table
        self.sections = []

    # a field is ("m", measure) or ("c", table, column)
    def _entity(self, f):
        return self.measure_home[f[1]] if f[0] == "m" else f[1]

    def _prop(self, f):
        return f[1] if f[0] == "m" else f[2]

    def ref(self, f):
        return f"{self._entity(f)}.{self._prop(f)}"

    def _expr(self, f, alias):
        kind = "Measure" if f[0] == "m" else "Column"
        return {kind: {"Expression": {"SourceRef": {"Source": alias}}, "Property": self._prop(f)}}

    def query(self, fields, order_by=None, descending=True):
        aliases, frm = {}, []
        for f in fields + ([order_by] if order_by else []):
            e = self._entity(f)
            if e not in aliases:
                aliases[e] = f"t{len(aliases)}"
                frm.append({"Name": aliases[e], "Entity": e, "Type": 0})
        select, seen = [], set()
        for f in fields:
            r = self.ref(f)
            if r in seen:
                continue
            seen.add(r)
            select.append({**self._expr(f, aliases[self._entity(f)]), "Name": r, "NativeReferenceName": self._prop(f)})
        q = {"Version": 2, "From": frm, "Select": select}
        if order_by:
            q["OrderBy"] = [{"Direction": 2 if descending else 1,
                             "Expression": self._expr(order_by, aliases[self._entity(order_by)])}]
        return q

    # ----------------------------------------------------------------------- visual container
    def container(self, page, x, y, w, h, single_visual):
        z = len(page["visualContainers"]) * 1000
        name = f"{next(_ids):020x}"
        config = {"name": name,
                  "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": z}}],
                  "singleVisual": single_visual}
        page["visualContainers"].append({"x": x, "y": y, "z": z, "width": w, "height": h,
                                         "config": json.dumps(config), "filters": "[]"})

    def visual(self, page, vtype, x, y, w, h, roles: dict, title=None, objects=None, order_by=None,
               descending=True, card_style=True, slicer_sync=None):
        fields = [f for fs in roles.values() for f in fs]
        projections = {role: [{"queryRef": self.ref(f), **({"active": True} if vtype == "slicer" else {})}
                              for f in fs] for role, fs in roles.items()}
        vc = {}
        if title:
            vc["title"] = [{"properties": {"show": TRUE, "text": text(title), "fontColor": color(INK),
                                           "fontSize": lit("11D"), "bold": TRUE}}]
        else:
            vc["title"] = [{"properties": {"show": FALSE}}]
        if card_style:
            vc["background"] = [{"properties": {"show": TRUE, "color": color("#FFFFFF"), "transparency": lit("0D")}}]
            vc["border"] = [{"properties": {"show": TRUE, "color": color(BORDER), "radius": lit("8D")}}]
            vc["padding"] = [{"properties": {"top": lit("10D"), "bottom": lit("10D"), "left": lit("12D"),
                                             "right": lit("12D")}}]
        sv = {"visualType": vtype, "projections": projections,
              "prototypeQuery": self.query(fields, order_by, descending),
              "drillFilterOtherVisuals": True, "hasDefaultSort": order_by is None,
              "objects": objects or {}, "vcObjects": vc}
        if slicer_sync:
            sv["syncGroup"] = {"groupName": slicer_sync, "fieldChanges": True, "filterChanges": True}
        self.container(page, x, y, w, h, sv)

    def textbox(self, page, x, y, w, h, paragraphs):
        """paragraphs: list of (text, size_pt, bold, color)."""
        paras = [{"textRuns": [{"value": t, "textStyle": {"fontSize": f"{size}pt", "color": col,
                                                          **({"fontWeight": "bold"} if bold else {})}}]}
                 for t, size, bold, col in paragraphs]
        self.container(page, x, y, w, h, {
            "visualType": "textbox", "drillFilterOtherVisuals": True,
            "objects": {"general": [{"properties": {"paragraphs": paras}}]},
            "vcObjects": {"background": [{"properties": {"show": FALSE}}]}})

    # ----------------------------------------------------------------------- page
    def page(self, title, question):
        p = {"config": json.dumps({"objects": {"background": [{"properties": {"color": color(PAGE_BG),
                                                                              "transparency": lit("0D")}}]}}),
             "displayName": title, "displayOption": 1, "filters": "[]", "height": 720.0,
             "name": f"ReportSection{len(self.sections) + 1}", "ordinal": len(self.sections),
             "visualContainers": [], "width": 1280.0}
        self.sections.append(p)
        self.textbox(p, 12, 4, 660, 66, [(title, 16, True, NAVY), (question, 10, False, MUTED)])
        for i, (label, field) in enumerate([("Month", ("c", "DimDate", "year_month")),
                                            ("Channel", ("c", "DimChannel", "channel_name")),
                                            ("Campaign", ("c", "DimCampaign", "campaign_name"))]):
            self.visual(p, "slicer", 692 + i * 196, 4, 184, 66, {"Values": [field]}, title=label,
                        objects={"data": [{"properties": {"mode": text("Dropdown")}}],
                                 "header": [{"properties": {"show": FALSE}}]},
                        slicer_sync=label.lower())
        self.textbox(p, 16, 694, 1000, 22,
                     [("Synthetic demonstration dataset — public reconstruction, not ODRES figures. "
                       "Professional context based on a real ODRES Group experience.", 8, False, MUTED)])
        return p

    def cards(self, page, measures, y=74, h=84):
        n = len(measures)
        gap = 12
        w = (1248 - gap * (n - 1)) / n
        for i, m in enumerate(measures):
            self.visual(page, "card", round(16 + i * (w + gap)), y, round(w), h, {"Values": [("m", m)]},
                        objects={"labels": [{"properties": {"color": color(NAVY), "fontSize": lit("22D")}}],
                                 "categoryLabels": [{"properties": {"color": color(MUTED), "fontSize": lit("9D")}}]})

    def build(self) -> dict:
        return {"config": json.dumps({"version": "5.59", "themeCollection": {}, "activeSectionIndex": 0,
                                      "linguisticSchemaSyncVersion": 0, "objects": {}}),
                "layoutOptimization": 0, "resourcePackages": [], "sections": self.sections}


# --------------------------------------------------------------------------- common chart settings
def bar_objects(fill=TEAL, labels=True, series_colors=None):
    obj = {"categoryAxis": [{"properties": {"showAxisTitle": FALSE}}],
           "valueAxis": [{"properties": {"showAxisTitle": FALSE, "show": FALSE if labels else TRUE}}],
           "labels": [{"properties": {"show": TRUE if labels else FALSE, "color": color(INK)}}]}
    if series_colors:
        obj["dataPoint"] = [{"properties": {"fill": color(c)}, "selector": {"metadata": ref}}
                            for ref, c in series_colors.items()]
    else:
        obj["dataPoint"] = [{"properties": {"fill": color(fill)}}]
    return obj


def build_report(measure_home: dict) -> dict:
    r = Report(measure_home)
    M = lambda name: ("m", name)  # noqa: E731
    month = ("c", "DimDate", "year_month")
    channel = ("c", "DimChannel", "channel_name")
    campaign = ("c", "DimCampaign", "campaign_name")
    ref = r.ref

    # ------------------------------------------------------------------ 1 Executive overview
    p = r.page("Executive Overview", "Are we buying customers efficiently, and where does revenue come from?")
    r.cards(p, ["Total Spend", "Leads", "Customers", "Won Revenue", "CAC", "Lead to Customer %"])
    r.visual(p, "lineClusteredColumnComboChart", 16, 170, 616, 256,
             {"Category": [month], "Y": [M("Won Revenue")], "Y2": [M("Leads")]},
             title="Won revenue (columns) and leads (line) by month", order_by=month, descending=False,
             objects={**bar_objects(labels=False), "lineStyles": [{"properties": {"strokeWidth": lit("3D")}}],
                      "dataPoint": [{"properties": {"fill": color(TEAL)}, "selector": {"metadata": ref(M("Won Revenue"))}},
                                    {"properties": {"fill": color(NAVY)}, "selector": {"metadata": ref(M("Leads"))}}]})
    r.visual(p, "clusteredBarChart", 644, 170, 620, 256, {"Category": [channel], "Y": [M("Won Revenue")]},
             title="Won revenue by channel", order_by=M("Won Revenue"), objects=bar_objects())
    r.visual(p, "funnel", 16, 438, 616, 250,
             {"Y": [M("Leads"), M("MQLs"), M("SQLs"), M("Opportunities"), M("Customers")]},
             title="Funnel: lead to customer", objects={"dataPoint": [{"properties": {"fill": color(NAVY)}}],
                                                        "labels": [{"properties": {"show": TRUE, "labelDisplayUnits": lit("1D")}}]})
    r.visual(p, "clusteredBarChart", 644, 438, 620, 250,
             {"Category": [channel], "Y": [M("Share of Leads"), M("Share of Customers")]},
             title="Share of leads vs share of customers", order_by=M("Share of Customers"),
             objects=bar_objects(series_colors={ref(M("Share of Leads")): GREY, ref(M("Share of Customers")): TEAL}))

    # ------------------------------------------------------------------ 2 Acquisition funnel
    p = r.page("Acquisition Funnel", "Where do we lose prospects, and which channels bring qualified leads?")
    r.cards(p, ["Sessions", "Leads", "MQLs", "SQLs", "Opportunities", "Customers"])
    r.visual(p, "funnel", 16, 170, 400, 518,
             {"Y": [M("Leads"), M("MQLs"), M("SQLs"), M("Opportunities"), M("Customers")]},
             title="Funnel with conversion", objects={"dataPoint": [{"properties": {"fill": color(TEAL)}}],
                                                      "labels": [{"properties": {"show": TRUE, "labelDisplayUnits": lit("1D")}}],
                                                      "percentBarLabel": [{"properties": {"show": TRUE}}]})
    r.visual(p, "pivotTable", 428, 170, 836, 254,
             {"Rows": [channel], "Values": [M("Session to Lead %"), M("Lead to MQL %"), M("MQL to SQL %"),
                                            M("SQL to Customer %"), M("Lead to Customer %")]},
             title="Stage conversion by channel", order_by=M("Lead to Customer %"))
    r.visual(p, "clusteredColumnChart", 428, 436, 412, 252,
             {"Category": [("c", "FactLeads", "Score Band")], "Y": [M("Lead to Customer %")]},
             title="Lead → customer % by lead score", order_by=("c", "FactLeads", "Score Band"), descending=False,
             objects=bar_objects())
    r.visual(p, "clusteredBarChart", 852, 436, 412, 252, {"Category": [channel], "Y": [M("Avg Lead Score")]},
             title="Average lead score by channel", order_by=M("Avg Lead Score"), objects=bar_objects(fill=NAVY))

    # ------------------------------------------------------------------ 3 Channel & campaign performance
    p = r.page("Channel & Campaign Performance", "Which campaigns should we scale, maintain, optimise or reduce?")
    r.cards(p, ["Paid Spend", "Paid CAC", "Non-paid Revenue Share", "Campaigns to Scale", "Campaigns to Reduce"])
    r.visual(p, "scatterChart", 16, 170, 716, 518,
             {"Category": [campaign], "Series": [("c", "DimCampaign", "Recommendation")],
              "X": [M("CAC")], "Y": [M("Won Revenue")], "Size": [M("Leads")]},
             title="Campaigns: CAC vs won revenue (bubble = leads)",
             objects={"categoryAxis": [{"properties": {"axisScale": text("log"), "showAxisTitle": TRUE}}],
                      "valueAxis": [{"properties": {"showAxisTitle": TRUE}}],
                      "categoryLabels": [{"properties": {"show": TRUE}}]})
    r.visual(p, "tableEx", 744, 170, 520, 518,
             {"Values": [channel, M("Total Spend"), M("Leads"), M("CPL"), M("CAC"), M("Won Revenue"),
                         M("Revenue / Spend")]},
             title="Channel ranking", order_by=M("Won Revenue"))

    # ------------------------------------------------------------------ 4 Pipeline & revenue
    p = r.page("Pipeline & Revenue", "How much do we win, how fast, and what is still open?")
    r.cards(p, ["Won Revenue", "Win Rate", "Average Deal Value", "Average Sales Cycle", "Open Pipeline"])
    r.visual(p, "clusteredColumnChart", 16, 170, 616, 256, {"Category": [month], "Y": [M("Won Revenue")]},
             title="Won revenue by close month", order_by=month, descending=False, objects=bar_objects())
    r.visual(p, "barChart", 644, 170, 620, 256,
             {"Category": [channel], "Series": [("c", "FactOpportunities", "status")], "Y": [M("Opportunities")]},
             title="Opportunities by channel and status", order_by=M("Opportunities"),
             objects={"categoryAxis": [{"properties": {"showAxisTitle": FALSE}}],
                      "valueAxis": [{"properties": {"showAxisTitle": FALSE}}]})
    size = ("c", "FactOpportunities", "company_size")
    r.visual(p, "clusteredColumnChart", 16, 438, 400, 250, {"Category": [size], "Y": [M("Average Sales Cycle")]},
             title="Sales cycle (days) by company size", order_by=size, descending=False, objects=bar_objects())
    r.visual(p, "clusteredColumnChart", 428, 438, 400, 250, {"Category": [size], "Y": [M("Average Deal Value")]},
             title="Average deal value by company size", order_by=size, descending=False,
             objects=bar_objects(fill=NAVY))
    r.visual(p, "clusteredBarChart", 840, 438, 424, 250, {"Category": [campaign], "Y": [M("Open Pipeline")]},
             title="Open pipeline by campaign", order_by=M("Open Pipeline"), objects=bar_objects(fill=NAVY))

    # ------------------------------------------------------------------ 5 Customer value
    p = r.page("Customer Value", "Who do we acquire, and how much recurring revenue do they bring?")
    r.cards(p, ["Customers", "MRR (end of period)", "ARR Run-rate", "Churned Customers", "Churn Rate"])
    r.visual(p, "lineClusteredColumnComboChart", 16, 170, 616, 256,
             {"Category": [month], "Y": [M("Churned Customers")], "Y2": [M("MRR")]},
             title="MRR (line) and churned customers (columns)", order_by=month, descending=False,
             objects={"categoryAxis": [{"properties": {"showAxisTitle": FALSE}}],
                      "valueAxis": [{"properties": {"showAxisTitle": FALSE}}],
                      "dataPoint": [{"properties": {"fill": color(RED)}, "selector": {"metadata": ref(M("Churned Customers"))}},
                                    {"properties": {"fill": color(TEAL)}, "selector": {"metadata": ref(M("MRR"))}}]})
    r.visual(p, "clusteredBarChart", 644, 170, 620, 256, {"Category": [channel], "Y": [M("Customers")]},
             title="New customers by acquisition channel", order_by=M("Customers"), objects=bar_objects())
    r.visual(p, "clusteredBarChart", 16, 438, 400, 250,
             {"Category": [("c", "DimRegion", "region_name")], "Y": [M("Customers")]},
             title="New customers by region", order_by=M("Customers"), objects=bar_objects())
    r.visual(p, "clusteredColumnChart", 428, 438, 400, 250,
             {"Category": [("c", "DimCustomer", "company_size")], "Y": [M("MRR (end of period)")]},
             title="MRR by company size", order_by=("c", "DimCustomer", "company_size"), descending=False,
             objects=bar_objects(fill=NAVY))
    r.visual(p, "clusteredBarChart", 840, 438, 424, 250,
             {"Category": [("c", "DimCustomer", "business_type")], "Y": [M("MRR (end of period)")]},
             title="MRR by business type", order_by=M("MRR (end of period)"), objects=bar_objects(fill=NAVY))

    # ------------------------------------------------------------------ 6 Data quality
    p = r.page("Data Quality", "Can management trust these numbers?")
    r.cards(p, ["Rows Loaded", "Rows Removed", "Issues Found (raw)", "Blocking Errors Left", "Documented Warnings"])
    r.visual(p, "clusteredBarChart", 16, 170, 716, 518,
             {"Category": [("c", "DataQualityChecks", "description")],
              "Y": [M("Issues Found (raw)"), M("Issues After Cleaning")]},
             title="Issues per check: raw export vs clean layer", order_by=M("Issues Found (raw)"),
             objects=bar_objects(series_colors={ref(M("Issues Found (raw)")): GREY,
                                                ref(M("Issues After Cleaning")): TEAL}))
    r.visual(p, "tableEx", 744, 170, 520, 200,
             {"Values": [("c", "DataQualityRowCounts", "table"), ("c", "DataQualityRowCounts", "raw_rows"),
                         ("c", "DataQualityRowCounts", "clean_rows"), ("c", "DataQualityRowCounts", "removed")]},
             title="Rows before / after cleaning")
    r.visual(p, "tableEx", 744, 382, 520, 306,
             {"Values": [("c", "CleaningLog", "rule"), ("c", "CleaningLog", "table"),
                         ("c", "CleaningLog", "rows_affected"), ("c", "CleaningLog", "action")]},
             title="Cleaning rules applied")
    return r.build()
