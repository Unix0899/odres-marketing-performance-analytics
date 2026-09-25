"""
Draw the technical proofs directly from the SQLite database:

  proofs/proof_01_database.png   tables, keys and row counts
  proofs/proof_02_sql.png        a real query and its result
  proofs/proof_04_model.png      star-schema diagram

The dashboard images in dashboard/ are real Power BI screenshots (see powerbi/DASHBOARD_SPEC.md);
proofs 03, 05 and 06 are built from them by build_powerbi_proofs.py.
"""
import sqlite3

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from common import DB, ROOT, SQL, get_logger  # noqa: E402

log = get_logger("visuals")
PROOFS = ROOT / "proofs"

NAVY, TEAL, INK, MUTED, LINE = "#0d2a45", "#0f8b8d", "#102033", "#607086", "#dce4ea"
plt.rcParams.update({"font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10})

conn = sqlite3.connect(DB)
q = lambda sql: pd.read_sql_query(sql, conn)  # noqa: E731


def save(fig, path):
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    log.info(f"{path.relative_to(ROOT)}")


def proof_database():
    tables = q("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') ORDER BY type, name")
    fig = plt.figure(figsize=(16, 9), dpi=110, facecolor="white")
    fig.text(0.04, 0.93, "SQLite database · odres_marketing_analytics_demo.sqlite", fontsize=18,
             fontweight="bold", color=NAVY)
    fig.text(0.04, 0.895, "9 tables with primary / foreign keys and CHECK constraints, 7 reporting views · "
                          "synthetic data", fontsize=10.5, color=MUTED)
    col_x = [0.04, 0.365, 0.69]
    i = 0
    for r in tables[tables.type == "table"].itertuples():
        cols = conn.execute(f"PRAGMA table_info({r.name})").fetchall()
        n = conn.execute(f"SELECT COUNT(*) FROM {r.name}").fetchone()[0]
        x, y = col_x[i % 3], 0.84 - (i // 3) * 0.27
        fig.add_artist(FancyBboxPatch((x, y - 0.235), 0.27, 0.235, boxstyle="round,pad=0,rounding_size=0.008",
                                      fc="white", ec=LINE, transform=fig.transFigure))
        fig.add_artist(plt.Rectangle((x, y - 0.035), 0.27, 0.035,
                                     color=NAVY if r.name.startswith("fact") else TEAL, transform=fig.transFigure))
        fig.text(x + 0.01, y - 0.0175, r.name, color="white", fontsize=10.5, fontweight="bold", va="center")
        fig.text(x + 0.26, y - 0.0175, f"{n:,} rows", color="white", fontsize=9, va="center", ha="right")
        for k, c in enumerate(cols[:8]):
            pk = " PK" if c[5] else ""
            fig.text(x + 0.012, y - 0.055 - k * 0.022, f"{c[1]}", fontsize=8.5, color=INK, family="monospace")
            fig.text(x + 0.26, y - 0.055 - k * 0.022, f"{c[2]}{pk}", fontsize=8, color=MUTED, ha="right",
                     family="monospace")
        if len(cols) > 8:
            fig.text(x + 0.012, y - 0.055 - 8 * 0.022, f"+ {len(cols) - 8} more columns", fontsize=8, color=MUTED)
        i += 1
    views = ", ".join(tables[tables.type == "view"].name)
    fig.text(0.04, 0.035, f"Views: {views}", fontsize=9.5, color=INK)
    return fig


def sql_image(sql_text, title, result: pd.DataFrame):
    fig = plt.figure(figsize=(16, 9), dpi=110, facecolor="white")
    fig.text(0.04, 0.93, title, fontsize=18, fontweight="bold", color=NAVY)
    fig.text(0.04, 0.895, "Real query from sql/05_campaign_analysis.sql, executed on the synthetic database",
             fontsize=10.5, color=MUTED)
    lines = sql_text.strip("\n").splitlines()[:21]
    box_h = len(lines) * 0.0225 + 0.045
    fig.add_artist(FancyBboxPatch((0.04, 0.87 - box_h), 0.92, box_h, boxstyle="round,pad=0,rounding_size=0.01",
                                  fc="#0e263d", ec="none", transform=fig.transFigure))
    for k, line in enumerate(lines):
        color = "#7f97ab" if line.strip().startswith("--") else "#dbe7ef"
        fig.text(0.055, 0.845 - k * 0.0225, line if len(line) < 118 else line[:115] + "…", fontsize=9.3,
                 color=color, family="monospace", va="top")
    ax = fig.add_axes([0.04, 0.06, 0.92, 0.72 - box_h])
    ax.axis("off")
    ax.set_title("Result", loc="left", color=INK)
    tab = ax.table(cellText=result.values, colLabels=list(result.columns), loc="upper center", bbox=[0, 0, 1, 0.95])
    tab.auto_set_font_size(False)
    tab.set_fontsize(9.5)
    for (i, j), cell in tab.get_celld().items():
        cell.set_edgecolor(LINE)
        cell.visible_edges = "B"
        if i == 0:
            cell.set_text_props(color=MUTED, fontweight="bold")
    return fig


def proof_sql():
    text = (SQL / "05_campaign_analysis.sql").read_text(encoding="utf-8")
    start = text.index("-- Q18. Campaigns")
    block = text[start:text.index(";", start) + 1]
    res = q(block)
    res = res.assign(spend=res.spend.map(lambda v: f"€{v:,.0f}"), cac=res.cac.map(lambda v: f"€{v:,.0f}"))
    return sql_image(block, "SQL · finding campaigns that spend a lot and convert poorly", res)


def proof_model():
    fig = plt.figure(figsize=(16, 9), dpi=110, facecolor="white")
    fig.text(0.04, 0.93, "Analytical data model (star schema)", fontsize=18, fontweight="bold", color=NAVY)
    fig.text(0.04, 0.895, "4 fact tables at different grains share 5 conformed dimensions · single-direction "
                          "relationships (1 → *) · synthetic data", fontsize=10.5, color=MUTED)
    boxes = {
        "DimChannel": (0.14, 0.72, "7 channels", TEAL),
        "DimDate": (0.42, 0.72, "calendar", TEAL),
        "DimCampaign": (0.70, 0.72, "21 campaigns + Unassigned", TEAL),
        "FactMarketingDaily": (0.04, 0.45, "date × campaign", NAVY),
        "FactLeads": (0.28, 0.45, "one row per lead", NAVY),
        "FactOpportunities": (0.56, 0.45, "one row per deal", NAVY),
        "FactCustomerMonthly": (0.80, 0.45, "customer × month", NAVY),
        "DimRegion": (0.42, 0.18, "8 Belgian regions", TEAL),
        "DimCustomer": (0.80, 0.18, "350 customers", TEAL),
    }
    w, h = 0.16, 0.10
    centers = {}
    for name, (x, y, sub, col) in boxes.items():
        fig.add_artist(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.01", fc="white", ec=col,
                                      lw=2, transform=fig.transFigure))
        fig.add_artist(plt.Rectangle((x, y + h - 0.035), w, 0.035, color=col, transform=fig.transFigure))
        fig.text(x + w / 2, y + h - 0.0175, name, color="white", fontsize=10.5, fontweight="bold", ha="center",
                 va="center")
        fig.text(x + w / 2, y + 0.032, sub, color=MUTED, fontsize=9, ha="center", va="center")
        centers[name] = (x + w / 2, y + h / 2)
    rels = [("DimDate", "FactMarketingDaily"), ("DimDate", "FactLeads"), ("DimDate", "FactOpportunities"),
            ("DimDate", "FactCustomerMonthly"), ("DimChannel", "FactMarketingDaily"), ("DimChannel", "FactLeads"),
            ("DimChannel", "FactOpportunities"), ("DimCampaign", "FactMarketingDaily"), ("DimCampaign", "FactLeads"),
            ("DimCampaign", "FactOpportunities"), ("DimRegion", "FactLeads"), ("DimRegion", "FactOpportunities"),
            ("DimCustomer", "FactCustomerMonthly")]
    for a, b in rels:
        (x1, y1), (x2, y2) = centers[a], centers[b]
        fig.add_artist(plt.Line2D([x1, x2], [y1, y2], color="#9fb0bf", lw=1.1, zorder=0, transform=fig.transFigure))
        fig.text(x1 + (x2 - x1) * 0.18, y1 + (y2 - y1) * 0.18, "1", fontsize=8, color=TEAL, fontweight="bold")
        fig.text(x1 + (x2 - x1) * 0.80, y1 + (y2 - y1) * 0.80, "*", fontsize=11, color=NAVY, fontweight="bold")
    fig.text(0.04, 0.06, "Facts (navy) hold measures: spend, sessions, leads, MQL/SQL flags, deal values, MRR. "
                         "Dimensions (teal) hold what we filter by: date, channel, campaign, region, customer.",
             fontsize=10, color=INK)
    fig.text(0.04, 0.03, "Revenue by month uses FactOpportunities[revenue_date_key] (close date, or creation date "
                         "when the close date is unknown). Details: powerbi/DATA_MODEL.md", fontsize=9, color=MUTED)
    return fig


def main():
    PROOFS.mkdir(exist_ok=True)
    save(proof_database(), PROOFS / "proof_01_database.png")
    save(proof_sql(), PROOFS / "proof_02_sql.png")
    save(proof_model(), PROOFS / "proof_04_model.png")


if __name__ == "__main__":
    main()
