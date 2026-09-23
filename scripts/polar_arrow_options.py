"""Twelve variations on the arrows-leaving mark.

The direction is settled; what is not is weight, whether the arrows are level
or offset, whether they are drawn as strokes or as solids, how far apart they
sit, and whether anything sits between them. Each of those changes what the
mark reads as at 16 pixels, which is where it is decided.

    python scripts/polar_arrow_options.py
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "polarisation"

BG = "#131519"
L, R = "#6ea8e0", "#d95555"
FAINT = "#3a424d"


def tile(art, ground=BG, rx=18):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            f'<rect width="100" height="100" rx="{rx}" fill="{ground}"/>{art}</svg>')


def stroke_arrow(x_tail, x_head, y, colour, w=8, head=12):
    """A shaft with a chevron head, both round-capped."""
    d = -1 if x_head < x_tail else 1
    return (f'<g stroke="{colour}" stroke-width="{w}" stroke-linecap="round" '
            f'stroke-linejoin="round" fill="none">'
            f'<path d="M{x_tail} {y} H{x_head}"/>'
            f'<path d="M{x_head - d * head} {y - head} L{x_head} {y} '
            f'L{x_head - d * head} {y + head}"/></g>')


def solid_arrow(x_tail, x_head, y, colour, half=11, shaft=7):
    """A filled triangle on a rectangle, which keeps more ink at small sizes."""
    d = -1 if x_head < x_tail else 1
    base = x_head - d * half * 1.6
    return (f'<rect x="{min(x_tail, base)}" y="{y - shaft / 2}" '
            f'width="{abs(base - x_tail)}" height="{shaft}" rx="{shaft / 2}" '
            f'fill="{colour}"/>'
            f'<path d="M{base} {y - half} L{x_head} {y} L{base} {y + half} Z" '
            f'fill="{colour}"/>')


def v1_current():
    return tile(stroke_arrow(46, 18, 50, L) + stroke_arrow(54, 82, 50, R))


def v2_heavier():
    return tile(stroke_arrow(44, 14, 50, L, 12, 15)
                + stroke_arrow(56, 86, 50, R, 12, 15))


def v3_lighter():
    return tile(stroke_arrow(48, 16, 50, L, 5, 9)
                + stroke_arrow(52, 84, 50, R, 5, 9))


def v4_solid():
    return tile(solid_arrow(52, 14, 50, L) + solid_arrow(48, 86, 50, R))


def v5_solid_heavy():
    return tile(solid_arrow(54, 12, 50, L, 15, 11)
                + solid_arrow(46, 88, 50, R, 15, 11))


def v6_stacked():
    """One above the other. Reads as two parties leaving, not one line splitting."""
    return tile(stroke_arrow(58, 16, 34, L, 9, 12)
                + stroke_arrow(42, 84, 66, R, 9, 12))


def v7_stacked_solid():
    return tile(solid_arrow(62, 14, 33, L, 12, 9)
                + solid_arrow(38, 86, 67, R, 12, 9))


def v8_wide_gap():
    """A gap you can see at 16px, which is the thing that says divided."""
    return tile(stroke_arrow(38, 14, 50, L, 9, 12)
                + stroke_arrow(62, 86, 50, R, 9, 12))


def v9_from_a_line():
    """They leave something: a centre line they used to share."""
    return tile(f'<rect x="47" y="18" width="6" height="64" rx="3" fill="{FAINT}"/>'
                + stroke_arrow(42, 16, 50, L, 8, 11)
                + stroke_arrow(58, 84, 50, R, 8, 11))


def v10_tailless():
    """Two chevrons and no shaft. The least ink that still points."""
    return tile(
        f'<path d="M40 26 L18 50 L40 74" fill="none" stroke="{L}" '
        f'stroke-width="13" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="M60 26 L82 50 L60 74" fill="none" stroke="{R}" '
        f'stroke-width="13" stroke-linecap="round" stroke-linejoin="round"/>')


def v11_diagonal():
    """Up and away, down and away. Divergence over time rather than in space."""
    return tile(stroke_arrow(0, 0, 0, L, 0, 0).replace("<g", "<g style='display:none'")
                + f'<g stroke="{L}" stroke-width="9" stroke-linecap="round" '
                f'stroke-linejoin="round" fill="none">'
                f'<path d="M48 52 L20 30"/><path d="M20 44 L20 30 L34 30"/></g>'
                f'<g stroke="{R}" stroke-width="9" stroke-linecap="round" '
                f'stroke-linejoin="round" fill="none">'
                f'<path d="M52 52 L80 74"/><path d="M80 60 L80 74 L66 74"/></g>')


def v12_light_ground():
    """The same mark on paper rather than a dark tile."""
    return tile(stroke_arrow(44, 14, 50, "#2f6fb2", 10, 13)
                + stroke_arrow(56, 86, 50, "#c33c3c", 10, 13),
                ground="#efe9dc")


OPTIONS = [
    ("1. as offered", v1_current()),
    ("2. heavier", v2_heavier()),
    ("3. lighter", v3_lighter()),
    ("4. solid heads", v4_solid()),
    ("5. solid, heavy", v5_solid_heavy()),
    ("6. stacked", v6_stacked()),
    ("7. stacked, solid", v7_stacked_solid()),
    ("8. wide gap", v8_wide_gap()),
    ("9. leaving a centre line", v9_from_a_line()),
    ("10. heads only", v10_tailless()),
    ("11. diagonal, over time", v11_diagonal()),
    ("12. on paper", v12_light_ground()),
]

SIZES = [128, 32, 16]


def sheet() -> str:
    rows = ""
    for name, svg in OPTIONS:
        cells = "".join(
            f'<td><div class="w" style="width:{s}px;height:{s}px">{svg}</div>'
            f'<span>{s}</span></td>' for s in SIZES)
        blown = (f'<td class="zoom"><div class="w" style="width:16px;height:16px">'
                 f'{svg}</div><span>16 at 4x</span></td>')
        word = (f'<td class="word"><div class="lockup">'
                f'<div class="w" style="width:42px;height:42px">{svg}</div>'
                f'<b>Polarisation</b></div></td>')
        rows += f'<tr><th>{name}</th>{cells}{blown}{word}</tr>'
    return f"""<!doctype html><meta charset=utf-8>
<link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400&display=block" rel="stylesheet">
<style>
 body {{ margin:0; padding:22px 26px; background:#f7f5f0; color:#22242a;
         font:14px/1.4 "Segoe UI",system-ui,sans-serif; }}
 h1 {{ font-size:16px; margin:0 0 4px; }}
 p {{ margin:0 0 18px; color:#5d6169; font-size:12.5px; max-width:660px; }}
 table {{ border-collapse:collapse; }}
 th {{ text-align:left; font-weight:600; font-size:13px; padding:9px 20px 9px 0;
       white-space:nowrap; }}
 td {{ padding:9px 16px 9px 0; vertical-align:middle; text-align:center; }}
 td span {{ display:block; margin-top:5px; font-size:10px; color:#8b8f97; }}
 .w {{ display:inline-block; }}
 .w svg {{ width:100%; height:100%; display:block; }}
 .zoom .w {{ transform:scale(4); transform-origin:center; image-rendering:pixelated; }}
 .zoom {{ padding-left:42px; padding-right:42px; }}
 .word {{ padding-left:14px; }}
 .lockup {{ display:flex; align-items:center; gap:9px; }}
 .lockup b {{ font:400 30px "Libre Baskerville",Georgia,serif; }}
 tr {{ border-bottom:1px solid #e2ded4; }}
</style>
<h1>Arrows leaving, twelve variations</h1>
<p>Weight, level against stacked, stroked against solid, how wide the gap is,
and whether anything sits between them. The 16px column decides it; the wide
column is that render blown up four times with no smoothing.</p>
<table>{rows}</table>"""


def main() -> int:
    html = OUT / "_arrow_options.html"
    html.write_text(sheet(), encoding="utf-8")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1180, "height": 900}, device_scale_factor=2)
        pg.goto(html.as_uri())
        pg.wait_for_timeout(2200)
        pg.screenshot(path=str(OUT / "_arrow_options.png"), full_page=True)
        b.close()
    print("wrote", OUT / "_arrow_options.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
