"""Render the link-preview card for the inequality page.

Drawn from data/out/wealth.json rather than screenshotted, so it cannot drift
into showing a chart the page no longer has. Dark, like the other card and like
the chat window it will be unfurled in. 2400x1260, twice what the scrapers ask
for.

The strip along the bottom is the real Gini data in the page's own three
panels, so the card carries the actual shape of the finding: it climbs through
the archaeology, climbs again through the tax registers, and falls in the
twentieth century.

    python scripts/make_wealth_card.py
"""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data" / "out" / "wealth.json").read_text(encoding="utf-8"))

W, H = 1200, 630
BG, INK, INK_SOFT, INK_FAINT, RULE = "#131519", "#e9ecf0", "#a7aeb8", "#98a0aa", "#2b2f36"
DEEP, EARLY, MID, PICK = "#d4795c", "#e8b45f", "#9aa8b4", "#6ea8e0"
BRONZE, SILVER, GOLD = "#cd7f32", "#c3cad2", "#e3b93f"

# the chart strip
CX, CY, CW, CH = 70, 330, W - 140, 236
GUT = 26


def panels():
    """The same three the page draws, on the Gini."""
    deep = [(p["year"], p["gini"]) for p in DATA["points"]
            if p["layer"] == "deep" and p.get("gini") is not None]
    early = [(p["year"], p["gini"]) for p in DATA["points"]
             if p["layer"] == "preindustrial" and not p.get("rollup") and p.get("gini") is not None]
    country = []
    for c in DATA["countries"].values():
        country += [(y, v) for y, v in c["industrial"]["gini"]]
    return [
        {"label": "Excavated settlements", "dots": deep, "colour": DEEP, "lines": []},
        {"label": "Tax registers", "dots": early, "colour": EARLY,
         "lines": [s["gini"] for s in DATA["regions"] if s.get("gini")]},
        {"label": "Whole countries", "dots": [], "colour": MID,
         "lines": [_median(country)]},
    ]


def _median(pairs):
    by = {}
    for y, v in pairs:
        by.setdefault(y, []).append(v)
    out = []
    for y in sorted(by):
        vs = sorted(by[y])
        out.append([y, vs[len(vs) // 2]])
    return out


def draw() -> str:
    each = (CW - GUT * 2) / 3
    parts = []
    for i, pan in enumerate(panels()):
        x0 = CX + i * (each + GUT)
        years = [y for y, _ in pan["dots"]] + [y for ln in pan["lines"] for y, _ in ln]
        lo, hi = min(years), max(years)
        span = (hi - lo) or 1
        sx = lambda y: x0 + (y - lo) / span * each          # noqa: E731
        sy = lambda v: CY + (1 - v) * CH                    # noqa: E731

        for t in (0.25, 0.5, 0.75, 1.0):
            parts.append(f'<line x1="{x0:.0f}" y1="{sy(t):.1f}" x2="{x0 + each:.0f}" '
                         f'y2="{sy(t):.1f}" stroke="{RULE}" stroke-width="1"/>')
        for ln in pan["lines"]:
            pts = " ".join(f"{sx(y):.1f},{sy(v):.1f}" for y, v in ln)
            parts.append(f'<polyline points="{pts}" fill="none" stroke="{pan["colour"]}" '
                         f'stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"/>')
        for y, v in pan["dots"]:
            parts.append(f'<circle cx="{sx(y):.1f}" cy="{sy(v):.1f}" r="3.4" '
                         f'fill="{pan["colour"]}" fill-opacity=".62"/>')
        parts.append(f'<text x="{x0:.0f}" y="{CY - 10:.0f}" font-size="15" '
                     f'font-weight="600" fill="{INK_SOFT}">{pan["label"]}</text>')
        parts.append(f'<text x="{x0 + each / 2:.0f}" y="{CY + CH + 24:.0f}" '
                     f'text-anchor="middle" font-size="14" fill="{INK_FAINT}">'
                     f'{_span(lo, hi)}</text>')
        if i < 2:
            gx = x0 + each + GUT / 2
            parts.append(f'<line x1="{gx:.0f}" y1="{CY:.0f}" x2="{gx:.0f}" '
                         f'y2="{CY + CH:.0f}" stroke="{RULE}" stroke-width="1" '
                         f'stroke-dasharray="2 4"/>')
    return "".join(parts)


def _span(lo: int, hi: int) -> str:
    fmt = lambda y: f"{abs(y)} BC" if y < 0 else str(y)     # noqa: E731
    return f"{fmt(lo)} to {fmt(hi)}"


MARK = f"""<svg viewBox="0 8 58 48" width="96" height="80">
  <g fill="{BRONZE}"><ellipse cx="13" cy="50" rx="6.4" ry="2.5"/><ellipse cx="13" cy="45" rx="6.4" ry="2.5"/></g>
  <g fill="{SILVER}"><ellipse cx="29" cy="50" rx="6.4" ry="2.5"/><ellipse cx="29" cy="45" rx="6.4" ry="2.5"/>
     <ellipse cx="29" cy="40" rx="6.4" ry="2.5"/></g>
  <g fill="{GOLD}"><ellipse cx="45" cy="50" rx="6.4" ry="2.5"/><ellipse cx="45" cy="45" rx="6.4" ry="2.5"/>
     <ellipse cx="45" cy="40" rx="6.4" ry="2.5"/><ellipse cx="45" cy="35" rx="6.4" ry="2.5"/>
     <ellipse cx="45" cy="30" rx="6.4" ry="2.5"/><ellipse cx="45" cy="25" rx="6.4" ry="2.5"/>
     <ellipse cx="45" cy="20" rx="6.4" ry="2.5"/><ellipse cx="45" cy="15" rx="6.4" ry="2.5"/>
     <ellipse cx="45" cy="10" rx="6.4" ry="2.5"/></g>
</svg>"""

HTML = f"""<!doctype html><meta charset="utf-8">
<style>
  * {{ margin:0; box-sizing:border-box; }}
  body {{ width:{W}px; height:{H}px; background:{BG}; overflow:hidden;
         font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif; }}
  .top {{ padding:66px 70px 0; }}
  .head {{ display:flex; align-items:center; gap:24px; }}
  h1 {{ font-size:78px; letter-spacing:-.015em; color:{INK}; font-weight:400; }}
  p {{ margin-top:20px; font-size:31px; color:{INK_SOFT}; }}
  svg.chart {{ position:absolute; left:0; top:0; }}
</style>
<svg class="chart" width="{W}" height="{H}">{draw()}</svg>
<div class="top">
  <div class="head">{MARK}<h1>Inequality</h1></div>
  <p>Who owned what, from excavated settlements in 9200 BC to national accounts today.</p>
</div>
"""


def main() -> int:
    tmp = ROOT / "site" / "wealth" / "_og.html"
    out = ROOT / "site" / "wealth" / "og-card.png"
    tmp.write_text(HTML, encoding="utf-8")
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        pg.goto(tmp.as_uri())
        pg.wait_for_timeout(400)
        pg.screenshot(path=str(out))
        br.close()
    tmp.unlink()
    print(f"wrote {out.relative_to(ROOT)}  {out.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
