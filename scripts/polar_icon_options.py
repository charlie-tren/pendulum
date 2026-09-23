"""Twelve marks for the polarisation page, on one contact sheet.

Decided at 16 pixels, so that is the column that matters: the sheet shows each
at 128, 32 and 16, then the 16 again blown up four times with no smoothing,
which is roughly what a tab strip gives the eye. The last column puts it beside
the word at title size, because this mark has to work in both places.

The incumbent, two humps, is included unchanged as number 12 so the round has a
baseline to beat rather than twelve unknowns.

    python scripts/polar_icon_options.py
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "polarisation"

BG = "#131519"
L, R = "#6ea8e0", "#d95555"        # the page's own blue and red, dark-mode values
GREY, PAPER, GOLD = "#8b949e", "#e8e2d4", "#d9a521"


def tile(art, ground=BG, rx=18):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            f'<rect width="100" height="100" rx="{rx}" fill="{ground}"/>{art}</svg>')


def o1_split_disc():
    """A disc cut in two and pulled apart. The plainest possible statement."""
    return tile(f'<path d="M46 16 A34 34 0 0 0 46 84 Z" fill="{L}"/>'
                f'<path d="M54 16 A34 34 0 0 1 54 84 Z" fill="{R}"/>')


def o2_arrows_apart():
    """Two arrows leaving each other. The conventional sign for diverging."""
    return tile(
        f'<g stroke="{L}" stroke-width="8" stroke-linecap="round" fill="none">'
        f'<path d="M46 50 H18"/><path d="M30 38 L18 50 L30 62"/></g>'
        f'<g stroke="{R}" stroke-width="8" stroke-linecap="round" fill="none">'
        f'<path d="M54 50 H82"/><path d="M70 38 L82 50 L70 62"/></g>')


def o3_crack():
    """One block with a fissure through it. The gap is the whole mark."""
    return tile(f'<path d="M18 20 H44 L38 40 L48 56 L40 80 H18 Z" fill="{L}"/>'
                f'<path d="M82 20 H56 L50 40 L60 56 L52 80 H82 Z" fill="{R}"/>')


def o4_magnet():
    """A horseshoe magnet. A concrete object whose two poles are the idea."""
    return tile(
        f'<path d="M26 74 V46 A24 24 0 0 1 74 46 V74" fill="none" '
        f'stroke="{GREY}" stroke-width="15"/>'
        f'<rect x="18.5" y="66" width="15" height="18" fill="{L}"/>'
        f'<rect x="66.5" y="66" width="15" height="18" fill="{R}"/>')


def o5_tug_of_war():
    """A rope with the knot pulled off centre. Division as a contest."""
    return tile(
        f'<line x1="14" y1="50" x2="86" y2="50" stroke="{GREY}" '
        f'stroke-width="6" stroke-linecap="round"/>'
        f'<rect x="12" y="34" width="16" height="32" rx="4" fill="{L}"/>'
        f'<rect x="72" y="34" width="16" height="32" rx="4" fill="{R}"/>'
        f'<circle cx="62" cy="50" r="9" fill="{GOLD}"/>')


def o6_wall():
    """Two fields and the wall between them."""
    return tile(f'<rect x="14" y="22" width="30" height="56" rx="3" fill="{L}"/>'
                f'<rect x="56" y="22" width="30" height="56" rx="3" fill="{R}"/>'
                f'<rect x="47" y="12" width="6" height="76" rx="3" fill="{PAPER}"/>')


def o7_speech_bubbles():
    """Two bubbles facing away from one another."""
    return tile(
        f'<path d="M12 24 H46 A4 4 0 0 1 50 28 V52 A4 4 0 0 1 46 56 H26 L14 68 '
        f'V56 H12 A4 4 0 0 1 8 52 V28 A4 4 0 0 1 12 24 Z" fill="{L}"/>'
        f'<path d="M88 40 H54 A4 4 0 0 0 50 44 V68 A4 4 0 0 0 54 72 H74 L86 84 '
        f'V72 H88 A4 4 0 0 0 92 68 V44 A4 4 0 0 0 88 40 Z" fill="{R}"/>')


def o8_ballot_split():
    """A ballot paper torn down the middle. The most literal political object."""
    return tile(
        f'<path d="M20 18 H48 L44 34 L50 50 L44 66 L48 82 H20 Z" fill="{PAPER}"/>'
        f'<path d="M80 18 H52 L56 34 L50 50 L56 66 L52 82 H80 Z" fill="{PAPER}" '
        f'fill-opacity=".72"/>'
        f'<rect x="26" y="30" width="14" height="5" fill="{L}"/>'
        f'<rect x="60" y="30" width="14" height="5" fill="{R}"/>')


def o9_chasm():
    """Two cliff edges and the drop between them, seen from the side."""
    return tile(
        f'<path d="M10 44 H42 V90 H10 Z" fill="{L}"/>'
        f'<path d="M58 34 H90 V90 H58 Z" fill="{R}"/>'
        f'<rect x="10" y="38" width="32" height="7" fill="{L}" fill-opacity=".55"/>'
        f'<rect x="58" y="28" width="32" height="7" fill="{R}" fill-opacity=".55"/>')


def o10_chevrons():
    """Two arrowheads turned away from each other, nothing else."""
    return tile(
        f'<path d="M44 20 L20 50 L44 80" fill="none" stroke="{L}" '
        f'stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="M56 20 L80 50 L56 80" fill="none" stroke="{R}" '
        f'stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>')


def o11_two_dots():
    """Two crowds that have stopped overlapping. Light ground, for temperature."""
    art = ""
    for cx, cy, col in ((30, 38, L), (24, 56, L), (38, 54, L), (32, 70, L),
                        (70, 38, R), (76, 56, R), (62, 54, R), (68, 70, R)):
        art += f'<circle cx="{cx}" cy="{cy}" r="10" fill="{col}"/>'
    return tile(art, ground=PAPER, rx=18)


def o12_current_humps():
    """The incumbent, unchanged, so the round has a baseline."""
    return tile(f'<path d="M12 78 C24 78 25 26 37 26 C49 26 50 78 50 78 Z" fill="{L}"/>'
                f'<path d="M50 78 C50 78 51 26 63 26 C75 26 76 78 88 78 Z" fill="{R}"/>')


OPTIONS = [
    ("1. disc cut in two", o1_split_disc()),
    ("2. arrows leaving", o2_arrows_apart()),
    ("3. a crack through it", o3_crack()),
    ("4. magnet, two poles", o4_magnet()),
    ("5. tug of war", o5_tug_of_war()),
    ("6. the wall between", o6_wall()),
    ("7. bubbles facing away", o7_speech_bubbles()),
    ("8. ballot torn in half", o8_ballot_split()),
    ("9. two cliff edges", o9_chasm()),
    ("10. chevrons apart", o10_chevrons()),
    ("11. two crowds, light", o11_two_dots()),
    ("12. CURRENT, two humps", o12_current_humps()),
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
        # and beside the word, which is the other place it has to work
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
<h1>Polarisation mark, twelve options</h1>
<p>The 16px column decides it. The wide column is that same 16px render blown up
four times with no smoothing, which is roughly what a tab strip gives your eye.
The last column is the other place it has to work, beside the word.</p>
<table>{rows}</table>"""


def main() -> int:
    html = OUT / "_icon_options.html"
    html.write_text(sheet(), encoding="utf-8")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1180, "height": 900}, device_scale_factor=2)
        pg.goto(html.as_uri())
        pg.wait_for_timeout(2200)   # the webfont has to arrive
        pg.screenshot(path=str(OUT / "_icon_options.png"), full_page=True)
        b.close()
    print("wrote", OUT / "_icon_options.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
