"""Render the link-preview card that WhatsApp, Slack and the rest unfurl.

Drawn from the live data rather than screenshotted, so it cannot drift into
showing a chart the site no longer has. 2400x1260, matching the card the
homepage already uses, which is 2x the 1200x630 that the scrapers want.

Dark, because the unfurl sits inside a chat window that is usually dark and a
white rectangle in a WhatsApp thread reads as a page from somewhere else. The
tokens are the site's own dark palette, and the bands use each bucket's
colour_dark where it has one, so the card matches what a reader lands on.
"""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data" / "out" / "orientation.json").read_text(encoding="utf-8"))

W, H = 1200, 630
# The site now excludes countries without a reading by default, so the card
# shows the same three bands a reader lands on rather than a grey wedge that
# is not on the page.
BANDS = ["left", "centre", "right"]
PAL = DATA["palette"]["buckets"]
# site/style.css, the prefers-color-scheme: dark block
BG, INK, INK_SOFT, INK_FAINT = "#131519", "#e9ecf0", "#a7aeb8", "#98a0aa"

def shade(key: str) -> str:
    """What the site paints this bucket in dark mode."""
    return PAL[key].get("colour_dark") or PAL[key]["colour"]

series = [r for r in DATA["groups"]["world"]["by_population"] if r["year"] <= 2025]
years = [r["year"] for r in series]
y0, y1 = min(years), max(years)

# the chart sits as a band across the lower half
CX, CY, CW, CH = 0, 300, W, 330
sx = lambda y: CX + (y - y0) / (y1 - y0) * CW
sy = lambda v: CY + (1 - v) * CH

# rescaled over the coded share, matching dropMissing() in site/app.js
coded = [sum(r[k] or 0 for k in BANDS) for r in series]

bands, base = [], [0.0] * len(series)
for key in BANDS:
    top = [base[i] + (series[i][key] or 0) / coded[i] for i in range(len(series))]
    pts = ([f"{sx(series[i]['year']):.1f},{sy(top[i]):.1f}" for i in range(len(series))] +
           [f"{sx(series[i]['year']):.1f},{sy(base[i]):.1f}" for i in range(len(series) - 1, -1, -1)])
    bands.append(f'<polygon points="{" ".join(pts)}" fill="{shade(key)}"/>')
    base = top

# the raised ball travels left of x=0, so the viewBox is widened rather than
# letting it clip against the edge of the mark
MARK = f"""<svg viewBox="-9 8 67 48" width="99" height="71" color="{INK_SOFT}">
  <line x1="9" y1="12" x2="55" y2="12" stroke="currentColor" stroke-width="3.4" stroke-linecap="round"/>
  <g transform="rotate(32 20 12)">
    <line x1="20" y1="12" x2="20" y2="41" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" opacity=".55"/>
    <circle cx="20" cy="47" r="6" fill="#2f6fb2"/>
  </g>
  <line x1="32" y1="12" x2="32" y2="41" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" opacity=".55"/>
  <circle cx="32" cy="47" r="6" fill="#9042d4"/>
  <line x1="44" y1="12" x2="44" y2="41" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" opacity=".55"/>
  <circle cx="44" cy="47" r="6" fill="#c33c3c"/>
</svg>"""

KEY = "".join(
    f'<span><i style="background:{shade(k)}"></i>{PAL[k]["label"]}</span>'
    for k in ("left", "centre", "right"))

HTML = f"""<!doctype html><meta charset="utf-8">
<style>
  * {{ margin: 0; box-sizing: border-box; }}
  body {{ width: {W}px; height: {H}px; background: {BG}; overflow: hidden;
         font-family: "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif; }}
  .top {{ padding: 62px 70px 0; }}
  .head {{ display: flex; align-items: center; gap: 26px; }}
  h1 {{ font-size: 78px; letter-spacing: -.015em; color: {INK}; font-weight: 400; }}
  p {{ margin-top: 20px; font-size: 33px; color: {INK_SOFT}; }}
  .key {{ display: flex; gap: 30px; margin-top: 26px;
         font: 22px/1 -apple-system,"Segoe UI",sans-serif; color: {INK_SOFT}; }}
  .key span {{ display: inline-flex; align-items: center; gap: 9px; }}
  .key i {{ width: 17px; height: 17px; border-radius: 4px; display: inline-block; }}
  svg.chart {{ position: absolute; left: 0; top: 0; }}
  .yrs {{ position: absolute; left: 70px; right: 70px; bottom: 16px; display: flex;
         justify-content: space-between;
         font: 22px/1 -apple-system,"Segoe UI",sans-serif;
         color: rgba(255,255,255,.72); }}
</style>
<svg class="chart" width="{W}" height="{H}">{"".join(bands)}</svg>
<div class="top">
  <div class="head">{MARK}<h1>Pendulum</h1></div>
  <p>Who governs the world&#8217;s eight billion people.</p>
  <div class="key">{KEY}</div>
</div>
<div class="yrs"><span>{y0}</span><span>{y1}</span></div>
"""


def main() -> int:
    tmp = ROOT / "site" / "_og.html"
    tmp.write_text(HTML, encoding="utf-8")
    out = ROOT / "site" / "og-card.png"
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        page.goto(tmp.as_uri())
        page.wait_for_timeout(400)
        page.screenshot(path=str(out))
        browser.close()
    tmp.unlink()
    print(f"wrote {out.relative_to(ROOT)}  {out.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
