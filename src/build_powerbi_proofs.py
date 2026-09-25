"""
Build the Power BI proofs from the report screenshots in dashboard/powerbi_*.png
(captured from Power BI Desktop with the PBIP open; synthetic data).

  proofs/proof_03_data_quality.png     <- Data Quality page
  proofs/proof_05_powerbi.png          <- Executive Overview page
  proofs/proof_06_business_insight.png <- Channel & Campaign page + insight / recommendation band
"""
import json
import shutil

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from common import PROCESSED, ROOT, get_logger

log = get_logger("proofs")
DASH, PROOFS = ROOT / "dashboard", ROOT / "proofs"
NAVY, TEAL2, WHITE, SOFT = (13, 42, 69), (101, 184, 181), (255, 255, 255), (198, 213, 223)


def font(size, bold=False):
    for name in (["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def insight_proof():
    shot = Image.open(DASH / "powerbi_03_channel_campaign_performance.png").convert("RGB")
    campaigns = pd.read_csv(PROCESSED / "campaign_performance.csv")
    reduce_ = campaigns[campaigns.recommendation == "REDUCE"]
    spend, revenue = reduce_.spend.sum(), reduce_.won_revenue.sum()
    kpi = json.loads((PROCESSED / "kpi_summary.json").read_text(encoding="utf-8"))
    channels = pd.read_csv(PROCESSED / "channel_performance.csv").set_index("channel_name")
    meta = channels.loc["Meta Ads"]
    band_h = 190
    out = Image.new("RGB", (shot.width, shot.height + band_h), NAVY)
    out.paste(shot, (0, 0))
    d = ImageDraw.Draw(out)
    y = shot.height + 22
    d.text((28, y), "INSIGHT → RECOMMENDATION  ·  synthetic demonstration dataset", fill=TEAL2, font=font(16, True))
    d.text((28, y + 34), f"Meta Ads brings {100 * meta.leads / channels.leads.sum():.0f}% of leads but "
                         f"{100 * meta.customers / channels.customers.sum():.0f}% of customers "
                         f"(CAC €{meta.cac:,.0f}).", fill=WHITE, font=font(24, True))
    d.text((28, y + 78), f"The {len(reduce_)} campaigns flagged REDUCE spent €{spend:,.0f} "
                         f"({100 * spend / kpi['total_spend']:.0f}% of spend) for €{revenue:,.0f} of first-year revenue.",
           fill=SOFT, font=font(18))
    d.text((28, y + 108), "Decision to test: move that budget to campaigns flagged SCALE and to referral / nurture "
                          "programmes, with a 3-month hold-out.", fill=SOFT, font=font(18))
    return out


def main():
    PROOFS.mkdir(exist_ok=True)
    shutil.copyfile(DASH / "powerbi_06_data_quality.png", PROOFS / "proof_03_data_quality.png")
    shutil.copyfile(DASH / "powerbi_01_executive_overview.png", PROOFS / "proof_05_powerbi.png")
    insight_proof().save(PROOFS / "proof_06_business_insight.png")
    log.info("proofs 03, 05, 06 built from the Power BI screenshots")


if __name__ == "__main__":
    main()
