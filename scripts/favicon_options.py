"""Ten favicon designs for the inequality page, on one contact sheet.

The point of the sheet is the SMALL column, not the big one. A favicon is read
at 16 CSS pixels in a tab strip, and the three-stack mark the page currently
uses has 13 coins, 3 face ellipses and 3 milled rings inside that square, which
is roughly one shape per pixel of height. Everything here is therefore rendered
at 128, 48, 32 and 16, with the 16 blown up four times so the mush is visible
rather than merely suspected.

    python scripts/favicon_options.py

Writes site/inequality/_favicon_options.png. Nothing here is wired into the
page: pick one and it gets built properly by make_coin_icons.py.
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "inequality"

BG = "#131519"
PARCHMENT = "#efe6d4"
# the dark-mode metals, which hold up on a dark tile at any size
METAL = {
    "bronze": ("#b06a28", "#d98f45", "#f0b982"),
    "silver": ("#98a2ac", "#c6ced7", "#e3e9ef"),
    "gold": ("#c69a22", "#ecc457", "#f7e2a4"),
}
DARK = {"bronze": ("#8a4f1c", "#a86a2c", "#5d3410"),
        "silver": ("#6f7681", "#89929c", "#4d535b"),
        "gold": ("#9c7714", "#c09a24", "#6b5109")}


def stack(metal, cx, n, rx, ry, step, base, palette=METAL):
    """A pile of n coins seen slightly from above, drawn bottom up.

    Each body is `step + ry` tall, not `step`. At `step` alone a coin covered
    only the flat half of the ellipse below it and the curved half showed
    through as a ring, which is the bug that shipped in the wordmark and then
    shipped again in the GIF renderer after the wordmark was fixed.
    """
    body, face, edge = palette[metal]
    top = base - (n - 1) * step
    coins = "".join(
        f'<path d="M{cx - rx} {base - i * step} L{cx - rx} {base - i * step + step + ry} '
        f'A{rx} {ry} 0 0 0 {cx + rx} {base - i * step + step + ry} '
        f'L{cx + rx} {base - i * step} Z" fill="{body}" stroke="{edge}" '
        f'stroke-width=".6" stroke-opacity=".45"/>'
        for i in range(n)
    )
    return f"{coins}<ellipse cx={cx} cy={top} rx={rx} ry={ry} fill=\"{face}\"/>"


def coin_face(cx, cy, r, metal="gold", ring=True):
    body, face, edge = METAL[metal]
    out = (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{face}" '
           f'stroke="{body}" stroke-width="{r * 0.13:.1f}"/>')
    if ring:
        out += (f'<circle cx="{cx}" cy="{cy}" r="{r * 0.66:.1f}" fill="none" '
                f'stroke="{edge}" stroke-width="{r * 0.09:.1f}" stroke-opacity=".75"/>')
    return out


def tile(art, ground=BG, rx=18):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            f'<rect width="100" height="100" rx="{rx}" fill="{ground}"/>{art}</svg>')


# --------------------------------------------------------------- the ten

def o1_current():
    art = "".join(stack(m, cx, n, 9.0, 3.4, 5.6, 82.0)
                  for m, cx, n in [("bronze", 22.0, 2), ("silver", 50.0, 3), ("gold", 78.0, 8)])
    return tile(art)


def o2_two_stacks():
    art = "".join(stack(m, cx, n, 15.0, 5.4, 9.0, 84.0)
                  for m, cx, n in [("bronze", 27.0, 2), ("gold", 73.0, 7)])
    return tile(art)


def o3_one_coin():
    return tile(coin_face(50, 50, 33))


def o4_tall_crop():
    # full bleed, no tile corners, the stack running off the top
    art = stack("gold", 50.0, 9, 26.0, 9.0, 13.0, 96.0)
    return tile(art, rx=0)


def o5_flat_bars():
    """No ellipses at all. Three rounded columns, ascending, in the metals.

    The only design here that is still three distinct objects at 16px, because
    a column has no internal detail to lose."""
    bars = ""
    for metal, x, h in [("bronze", 16, 26), ("silver", 42, 46), ("gold", 68, 72)]:
        body, face, _ = METAL[metal]
        bars += (f'<rect x="{x}" y="{88 - h}" width="16" height="{h}" rx="5" '
                 f'fill="{face}" stroke="{body}" stroke-width="2"/>')
    return tile(bars)


def o6_unequal():
    """The page's actual argument as a picture: one coin against nine."""
    art = (stack("bronze", 24.0, 1, 14.0, 5.2, 9.0, 84.0)
           + stack("gold", 72.0, 9, 14.0, 5.2, 8.4, 84.0))
    return tile(art)


def o7_coin_slice():
    """A gold coin with a tenth cut out of it and set aside."""
    import math
    r, cx, cy = 33, 48, 52
    a0, a1 = -math.pi / 2, -math.pi / 2 + 2 * math.pi * 0.62
    x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    body, face, edge = METAL["gold"]
    big = 1 if 0.62 > 0.5 else 0
    art = (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{DARK["gold"][0]}" />'
           f'<path d="M{cx} {cy} L{x0:.1f} {y0:.1f} A{r} {r} 0 {big} 1 {x1:.1f} {y1:.1f} Z" '
           f'fill="{face}" stroke="{body}" stroke-width="3"/>')
    return tile(art)


def o8_light_tile():
    art = "".join(stack(m, cx, n, 11.0, 4.2, 6.8, 84.0, DARK)
                  for m, cx, n in [("bronze", 22.0, 2), ("silver", 50.0, 3), ("gold", 78.0, 7)])
    return tile(art, ground=PARCHMENT)


def o9_fat_pair():
    art = "".join(stack(m, cx, n, 19.0, 7.0, 12.0, 86.0)
                  for m, cx, n in [("silver", 28.0, 2), ("gold", 72.0, 5)])
    return tile(art)


def o10_gold_only():
    art = stack("gold", 50.0, 5, 24.0, 8.6, 14.0, 88.0)
    return tile(art)


OPTIONS = [
    ("1. current, three stacks", o1_current()),
    ("2. two stacks, fatter coins", o2_two_stacks()),
    ("3. one coin, face on", o3_one_coin()),
    ("4. one stack, full bleed", o4_tall_crop()),
    ("5. flat columns, no coins", o5_flat_bars()),
    ("6. one against nine", o6_unequal()),
    ("7. coin with a slice out", o7_coin_slice()),
    ("8. dark coins, light tile", o8_light_tile()),
    ("9. fat pair, five and two", o9_fat_pair()),
    ("10. one gold stack, centred", o10_gold_only()),
]

SIZES = [128, 48, 32, 16]


def sheet() -> str:
    rows = ""
    for name, svg in OPTIONS:
        cells = "".join(
            f'<td><div class="w" style="width:{s}px;height:{s}px">{svg}</div>'
            f'<span>{s}</span></td>' for s in SIZES
        )
        # the 16px one again at 4x, nearest-neighbour, so the mush is visible
        blown = (f'<td class="zoom"><div class="w" style="width:16px;height:16px">{svg}</div>'
                 f'<span>16 at 4x</span></td>')
        rows += f'<tr><th>{name}</th>{cells}{blown}</tr>'
    return f"""<!doctype html><meta charset=utf-8>
<style>
 body {{ margin:0; padding:22px 26px; background:#f7f5f0; color:#22242a;
         font:14px/1.4 "Segoe UI",system-ui,sans-serif; }}
 h1 {{ font-size:16px; margin:0 0 4px; }}
 p {{ margin:0 0 18px; color:#5d6169; font-size:12.5px; max-width:620px; }}
 table {{ border-collapse:collapse; }}
 th {{ text-align:left; font-weight:600; font-size:13px; padding:9px 22px 9px 0;
       white-space:nowrap; }}
 td {{ padding:9px 20px 9px 0; vertical-align:middle; text-align:center; }}
 td span {{ display:block; margin-top:5px; font-size:10px; color:#8b8f97; }}
 .w {{ display:inline-block; }}
 .w svg {{ width:100%; height:100%; display:block; }}
 .zoom .w {{ transform:scale(4); transform-origin:center;
             image-rendering:pixelated; }}
 .zoom {{ padding-left:44px; padding-right:44px; }}
 tr {{ border-bottom:1px solid #e2ded4; }}
</style>
<h1>Inequality favicon, ten options</h1>
<p>The 16px column is the one that decides it. The right-hand column is that
same 16px render blown up four times with no smoothing, which is roughly what
your eye is given in a tab strip.</p>
<table>{rows}</table>"""


def main() -> int:
    html = OUT / "_favicon_options.html"
    html.write_text(sheet(), encoding="utf-8")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1180, "height": 900},
                        device_scale_factor=2)
        pg.goto(html.as_uri())
        pg.wait_for_timeout(250)
        pg.screenshot(path=str(OUT / "_favicon_options.png"), full_page=True)
        b.close()
    print("wrote", OUT / "_favicon_options.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
