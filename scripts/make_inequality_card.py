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


MARK = """<svg viewBox="0 8 58 48" width="104" height="86"><path d="M6.40 51.00 L6.40 57.80 A6.60 2.60 0 0 0 19.60 57.80 L19.60 51.00 Z" fill="#b06a28" stroke="#f0b982" stroke-width=".4" stroke-opacity=".5"/><path d="M6.40 46.80 L6.40 53.60 A6.60 2.60 0 0 0 19.60 53.60 L19.60 46.80 Z" fill="#b06a28" stroke="#f0b982" stroke-width=".4" stroke-opacity=".5"/><ellipse cx="13.00" cy="46.80" rx="6.60" ry="2.60" fill="#d98f45"/><ellipse cx="13.00" cy="46.80" rx="4.70" ry="1.80" fill="none" stroke="#f0b982" stroke-width=".5" opacity=".8"/><path d="M22.40 51.00 L22.40 57.80 A6.60 2.60 0 0 0 35.60 57.80 L35.60 51.00 Z" fill="#98a2ac" stroke="#e3e9ef" stroke-width=".4" stroke-opacity=".5"/><path d="M22.40 46.80 L22.40 53.60 A6.60 2.60 0 0 0 35.60 53.60 L35.60 46.80 Z" fill="#98a2ac" stroke="#e3e9ef" stroke-width=".4" stroke-opacity=".5"/><path d="M22.40 42.60 L22.40 49.40 A6.60 2.60 0 0 0 35.60 49.40 L35.60 42.60 Z" fill="#98a2ac" stroke="#e3e9ef" stroke-width=".4" stroke-opacity=".5"/><ellipse cx="29.00" cy="42.60" rx="6.60" ry="2.60" fill="#c6ced7"/><ellipse cx="29.00" cy="42.60" rx="4.70" ry="1.80" fill="none" stroke="#e3e9ef" stroke-width=".5" opacity=".8"/><path d="M38.40 51.00 L38.40 57.80 A6.60 2.60 0 0 0 51.60 57.80 L51.60 51.00 Z" fill="#c69a22" stroke="#f7e2a4" stroke-width=".4" stroke-opacity=".5"/><path d="M38.40 46.80 L38.40 53.60 A6.60 2.60 0 0 0 51.60 53.60 L51.60 46.80 Z" fill="#c69a22" stroke="#f7e2a4" stroke-width=".4" stroke-opacity=".5"/><path d="M38.40 42.60 L38.40 49.40 A6.60 2.60 0 0 0 51.60 49.40 L51.60 42.60 Z" fill="#c69a22" stroke="#f7e2a4" stroke-width=".4" stroke-opacity=".5"/><path d="M38.40 38.40 L38.40 45.20 A6.60 2.60 0 0 0 51.60 45.20 L51.60 38.40 Z" fill="#c69a22" stroke="#f7e2a4" stroke-width=".4" stroke-opacity=".5"/><path d="M38.40 34.20 L38.40 41.00 A6.60 2.60 0 0 0 51.60 41.00 L51.60 34.20 Z" fill="#c69a22" stroke="#f7e2a4" stroke-width=".4" stroke-opacity=".5"/><path d="M38.40 30.00 L38.40 36.80 A6.60 2.60 0 0 0 51.60 36.80 L51.60 30.00 Z" fill="#c69a22" stroke="#f7e2a4" stroke-width=".4" stroke-opacity=".5"/><path d="M38.40 25.80 L38.40 32.60 A6.60 2.60 0 0 0 51.60 32.60 L51.60 25.80 Z" fill="#c69a22" stroke="#f7e2a4" stroke-width=".4" stroke-opacity=".5"/><path d="M38.40 21.60 L38.40 28.40 A6.60 2.60 0 0 0 51.60 28.40 L51.60 21.60 Z" fill="#c69a22" stroke="#f7e2a4" stroke-width=".4" stroke-opacity=".5"/><path d="M38.40 17.40 L38.40 24.20 A6.60 2.60 0 0 0 51.60 24.20 L51.60 17.40 Z" fill="#c69a22" stroke="#f7e2a4" stroke-width=".4" stroke-opacity=".5"/><ellipse cx="45.00" cy="17.40" rx="6.60" ry="2.60" fill="#ecc457"/><ellipse cx="45.00" cy="17.40" rx="4.70" ry="1.80" fill="none" stroke="#f7e2a4" stroke-width=".5" opacity=".8"/></svg>"""

HTML = f"""<!doctype html><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400&display=block" rel="stylesheet">
<style>
  * {{ margin:0; box-sizing:border-box; }}
  body {{ width:{W}px; height:{H}px; background:{BG}; overflow:hidden;
         font-family:'Libre Baskerville',Georgia,serif; }}
  .top {{ padding:66px 70px 0; }}
  .head {{ display:flex; align-items:center; gap:24px; }}
  h1 {{ font-size:66px; letter-spacing:-.015em; color:{INK}; font-weight:400; }}
  p {{ margin-top:20px; font-size:31px; color:{INK_SOFT}; }}
  svg.chart {{ position:absolute; left:0; top:0; }}
</style>
<svg class="chart" width="{W}" height="{H}">{draw()}</svg>
<div class="top">
  <div class="head">{MARK}<h1>Inequality</h1></div>
  <p>From a Syrian village in 9200 BC to last year&#8217;s tax returns.</p>
</div>
"""


def main() -> int:
    tmp = ROOT / "site" / "inequality" / "_og.html"
    out = ROOT / "site" / "inequality" / "og-card.png"
    tmp.write_text(HTML, encoding="utf-8")
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
        pg.goto(tmp.as_uri())
        pg.wait_for_timeout(2500)  # the webfont has to arrive
        pg.screenshot(path=str(out))
        br.close()
    tmp.unlink()
    print(f"wrote {out.relative_to(ROOT)}  {out.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
