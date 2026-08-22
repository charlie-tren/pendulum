"""Render candidate marks for the wealth page, as a contact sheet to choose from.

The main page's Newton's cradle says "swings back and forth", which is the
political story and not this one. Wealth does not oscillate in the record: it
climbs, with two interruptions. So these are mostly shapes about accumulation
and imbalance rather than motion.

Each is drawn at the same size the real mark renders at, in the site's dark
palette, so the choice is made on the thing rather than on a description.

    python scripts/wealth_mark_options.py
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "_mark_options.png"

INK = "#a7aeb8"          # --ink-soft, dark
BLUE, PURPLE, RED = "#2f6fb2", "#9042d4", "#c33c3c"
GOLD, TERRA = "#e8b45f", "#d4795c"

# Every mark shares the cradle's viewBox so they sit at identical scale
VB = "0 8 58 48"

MARKS = {
    "Unequal bars": f"""
      <rect x="8"  y="42" width="8" height="12" rx="1.5" fill="{INK}" opacity=".45"/>
      <rect x="20" y="36" width="8" height="18" rx="1.5" fill="{INK}" opacity=".6"/>
      <rect x="32" y="29" width="8" height="25" rx="1.5" fill="{PURPLE}"/>
      <rect x="44" y="12" width="8" height="42" rx="1.5" fill="{RED}"/>""",

    "Tipped scales": f"""
      <line x1="29" y1="16" x2="29" y2="50" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>
      <line x1="21" y1="50" x2="37" y2="50" stroke="{INK}" stroke-width="2.6" stroke-linecap="round"/>
      <g transform="rotate(-15 29 16)">
        <line x1="9" y1="16" x2="49" y2="16" stroke="{INK}" stroke-width="2.6" stroke-linecap="round"/>
        <circle cx="11" cy="22" r="4" fill="{BLUE}"/>
        <circle cx="47" cy="26" r="9" fill="{RED}"/>
      </g>""",

    "Lorenz curve": f"""
      <line x1="10" y1="52" x2="52" y2="12" stroke="{INK}" stroke-width="1.8"
            stroke-dasharray="3 3" opacity=".55"/>
      <path d="M10 52 Q40 52 52 12" fill="none" stroke="{RED}" stroke-width="3" stroke-linecap="round"/>
      <line x1="10" y1="12" x2="10" y2="52" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>
      <line x1="10" y1="52" x2="52" y2="52" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>""",

    "Strata": f"""
      <rect x="9" y="14" width="42" height="5"  rx="1.5" fill="{RED}"/>
      <rect x="9" y="22" width="42" height="8"  rx="1.5" fill="{PURPLE}" opacity=".85"/>
      <rect x="9" y="33" width="42" height="7"  rx="1.5" fill="{INK}" opacity=".5"/>
      <rect x="9" y="43" width="42" height="11" rx="1.5" fill="{BLUE}" opacity=".8"/>""",

    "Staircase": f"""
      <path d="M9 52 h11 v-9 h11 v-12 h11 v-19 h9"
            fill="none" stroke="{INK}" stroke-width="2.6"
            stroke-linejoin="round" stroke-linecap="round"/>
      <circle cx="51" cy="12" r="5" fill="{RED}"/>""",

    "Stacked coins": f"""
      <g fill="{BLUE}"><ellipse cx="14" cy="50" rx="6" ry="2.4"/></g>
      <g fill="{PURPLE}">
        <ellipse cx="29" cy="50" rx="6" ry="2.4"/><ellipse cx="29" cy="45" rx="6" ry="2.4"/>
      </g>
      <g fill="{RED}">
        <ellipse cx="45" cy="50" rx="6" ry="2.4"/><ellipse cx="45" cy="45" rx="6" ry="2.4"/>
        <ellipse cx="45" cy="40" rx="6" ry="2.4"/><ellipse cx="45" cy="35" rx="6" ry="2.4"/>
        <ellipse cx="45" cy="30" rx="6" ry="2.4"/><ellipse cx="45" cy="25" rx="6" ry="2.4"/>
        <ellipse cx="45" cy="20" rx="6" ry="2.4"/><ellipse cx="45" cy="15" rx="6" ry="2.4"/>
      </g>""",

    "One and the many": f"""
      <rect x="30" y="14" width="22" height="22" rx="2" fill="{RED}"/>
      <g fill="{INK}" opacity=".55">
        <rect x="8"  y="41" width="6" height="6" rx="1"/><rect x="17" y="41" width="6" height="6" rx="1"/>
        <rect x="26" y="41" width="6" height="6" rx="1"/><rect x="35" y="41" width="6" height="6" rx="1"/>
        <rect x="44" y="41" width="6" height="6" rx="1"/>
        <rect x="8"  y="50" width="6" height="6" rx="1"/><rect x="17" y="50" width="6" height="6" rx="1"/>
        <rect x="26" y="50" width="6" height="6" rx="1"/><rect x="35" y="50" width="6" height="6" rx="1"/>
        <rect x="44" y="50" width="6" height="6" rx="1"/>
      </g>""",

    "Pyramid": f"""
      <path d="M30 11 L36 24 H24 Z" fill="{RED}"/>
      <path d="M23 26 H37 L42 39 H18 Z" fill="{PURPLE}" opacity=".85"/>
      <path d="M17 41 H43 L49 54 H11 Z" fill="{BLUE}" opacity=".8"/>""",

    "The gap": f"""
      <rect x="8"  y="34" width="16" height="20" rx="2" fill="{BLUE}" opacity=".85"/>
      <rect x="36" y="13" width="16" height="41" rx="2" fill="{RED}"/>
      <line x1="26" y1="24" x2="34" y2="24" stroke="{INK}" stroke-width="2"
            stroke-linecap="round" stroke-dasharray="2 4"/>""",

    "Rising dots": f"""
      <circle cx="11" cy="49" r="3.4" fill="{TERRA}"/>
      <circle cx="21" cy="45" r="3.4" fill="{TERRA}"/>
      <circle cx="30" cy="37" r="3.4" fill="{GOLD}"/>
      <circle cx="40" cy="29" r="3.4" fill="{GOLD}"/>
      <circle cx="50" cy="16" r="3.4" fill="{RED}"/>""",
}

HTML = """<!doctype html><meta charset="utf-8">
<style>
  * {{ margin:0; box-sizing:border-box; }}
  body {{ background:#131519; color:#e9ecf0; padding:34px 30px 26px;
         font:15px/1.5 -apple-system,"Segoe UI",Roboto,sans-serif; width:1180px; }}
  h1 {{ font:400 26px/1.2 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
       margin-bottom:6px; }}
  p.note {{ color:#98a0aa; font-size:14px; margin-bottom:26px; }}
  .grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:22px 20px; }}
  .cell {{ border:1px solid #2b2f36; border-radius:12px; background:#1a1d22; padding:16px 16px 13px; }}
  .row {{ display:flex; align-items:center; gap:20px; }}
  svg {{ height:44px; width:auto; overflow:visible; color:#a7aeb8; flex:none; }}
  .word {{ font:400 33px/1 "Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
          letter-spacing:-.015em; }}
  .name {{ margin-top:12px; font-size:12.5px; color:#98a0aa;
          text-transform:uppercase; letter-spacing:.07em; }}
</style>
<h1>A mark for the wealth page</h1>
<p class="note">Shown beside the word at the size it actually renders. The cradle stays on the main page.</p>
<div class="grid">{cells}</div>
"""

CELL = """<div class="cell"><div class="row">
  <svg viewBox="{vb}">{body}</svg><span class="word">{word}</span>
</div><div class="name">{name}</div></div>"""


def main() -> int:
    word = "Wealth"
    cells = "".join(CELL.format(vb=VB, body=b, name=n, word=word) for n, b in MARKS.items())
    tmp = ROOT / "site" / "_marks.html"
    tmp.write_text(HTML.format(cells=cells), encoding="utf-8")
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": 1180, "height": 900}, device_scale_factor=2)
        pg.goto(tmp.as_uri())
        pg.wait_for_timeout(350)
        pg.screenshot(path=str(OUT), full_page=True)
        br.close()
    tmp.unlink()
    print(f"wrote {OUT.relative_to(ROOT)}  {OUT.stat().st_size:,} bytes  ({len(MARKS)} options)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
