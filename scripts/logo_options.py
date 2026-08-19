"""Render the logo candidates to a PNG contact sheet.

Each mark is shown large, at 32px and at 16px, because a mark that only works
at 96px is not a favicon.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
LEFT, CENTRE, RIGHT = "#2f6fb2", "#7d5ba6", "#c33c3c"
INK, SOFT = "#1a1c1f", "#8b9199"

GRAD = (f'<linearGradient id="g" x1="0" x2="1">'
        f'<stop offset="0" stop-color="{LEFT}"/>'
        f'<stop offset=".5" stop-color="{CENTRE}"/>'
        f'<stop offset="1" stop-color="{RIGHT}"/></linearGradient>')

MARKS = {
    "1. Swing arc": f'''<defs>{GRAD}</defs>
      <path d="M10 34 Q32 52 54 34" fill="none" stroke="url(#g)" stroke-width="5"
            stroke-linecap="round"/>
      <line x1="32" y1="12" x2="52" y2="32" stroke="{INK}" stroke-width="3.2"
            stroke-linecap="round"/>
      <circle cx="32" cy="12" r="3.4" fill="{INK}"/>
      <circle cx="53" cy="33" r="7.5" fill="{RIGHT}"/>''',

    "2. Split bob": f'''
      <line x1="32" y1="11" x2="32" y2="30" stroke="{INK}" stroke-width="3.2"
            stroke-linecap="round"/>
      <circle cx="32" cy="11" r="3.4" fill="{INK}"/>
      <path d="M32 30 A14 14 0 0 0 32 58 Z" fill="{LEFT}"/>
      <path d="M32 30 A14 14 0 0 1 32 58 Z" fill="{RIGHT}"/>''',

    "3. Three positions": f'''
      <line x1="32" y1="12" x2="12" y2="42" stroke="{LEFT}" stroke-width="3"
            stroke-linecap="round" opacity=".45"/>
      <circle cx="12" cy="42" r="5" fill="{LEFT}" opacity=".45"/>
      <line x1="32" y1="12" x2="52" y2="42" stroke="{RIGHT}" stroke-width="3"
            stroke-linecap="round" opacity=".45"/>
      <circle cx="52" cy="42" r="5" fill="{RIGHT}" opacity=".45"/>
      <line x1="32" y1="12" x2="32" y2="46" stroke="{INK}" stroke-width="3.4"
            stroke-linecap="round"/>
      <circle cx="32" cy="50" r="7.5" fill="{CENTRE}"/>
      <circle cx="32" cy="12" r="3.4" fill="{INK}"/>''',

    "4. Motion trail": f'''<defs>{GRAD}</defs>
      <circle cx="14" cy="38" r="5" fill="{LEFT}" opacity=".30"/>
      <circle cx="23" cy="45" r="5.6" fill="{LEFT}" opacity=".50"/>
      <circle cx="32" cy="48" r="6.2" fill="{CENTRE}" opacity=".72"/>
      <circle cx="41" cy="45" r="6.8" fill="{RIGHT}" opacity=".86"/>
      <circle cx="50" cy="38" r="7.6" fill="{RIGHT}"/>
      <line x1="32" y1="12" x2="50" y2="38" stroke="{INK}" stroke-width="3"
            stroke-linecap="round"/>
      <circle cx="32" cy="12" r="3.4" fill="{INK}"/>''',

    "5. Newton's cradle": f'''
      <line x1="10" y1="13" x2="54" y2="13" stroke="{INK}" stroke-width="3"
            stroke-linecap="round"/>
      <line x1="18" y1="13" x2="10" y2="34" stroke="{SOFT}" stroke-width="2.4"/>
      <circle cx="9" cy="39" r="6.4" fill="{LEFT}"/>
      <line x1="30" y1="13" x2="30" y2="40" stroke="{SOFT}" stroke-width="2.4"/>
      <circle cx="30" cy="46" r="6.4" fill="{CENTRE}"/>
      <line x1="42" y1="13" x2="44" y2="40" stroke="{SOFT}" stroke-width="2.4"/>
      <circle cx="44" cy="46" r="6.4" fill="{RIGHT}"/>''',

    "6. Arc only": f'''<defs>{GRAD}</defs>
      <path d="M8 24 Q32 58 56 24" fill="none" stroke="url(#g)" stroke-width="9"
            stroke-linecap="round"/>''',

    "7. Bob on a stacked arc": f'''
      <path d="M10 30 Q21 44 32 47" fill="none" stroke="{LEFT}" stroke-width="5"
            stroke-linecap="round"/>
      <path d="M32 47 Q43 44 54 30" fill="none" stroke="{RIGHT}" stroke-width="5"
            stroke-linecap="round"/>
      <line x1="32" y1="12" x2="45" y2="38" stroke="{INK}" stroke-width="3.2"
            stroke-linecap="round"/>
      <circle cx="32" cy="12" r="3.4" fill="{INK}"/>
      <circle cx="46" cy="40" r="8" fill="{CENTRE}"/>''',

    "8. Tilted globe bob": f'''<defs>{GRAD}</defs>
      <path d="M12 32 Q32 50 52 32" fill="none" stroke="{SOFT}" stroke-width="2"
            stroke-dasharray="3 4" stroke-linecap="round"/>
      <line x1="32" y1="12" x2="48" y2="34" stroke="{INK}" stroke-width="3.2"
            stroke-linecap="round"/>
      <circle cx="32" cy="12" r="3.4" fill="{INK}"/>
      <circle cx="49" cy="36" r="10" fill="url(#g)"/>
      <path d="M39 36 h20 M49 26 a13 13 0 0 1 0 20 a13 13 0 0 1 0-20"
            fill="none" stroke="#fff" stroke-width="1.3" opacity=".8"/>''',
}


def svg(body: str, size: int) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" '
            f'width="{size}" height="{size}">{body}</svg>')


def main() -> int:
    cells = []
    for name, body in MARKS.items():
        cells.append(
            f'<div class="cell"><div class="row">{svg(body, 96)}'
            f'<div class="small">{svg(body, 32)}{svg(body, 16)}</div></div>'
            f'<p>{name}</p></div>')

    html = f"""<!doctype html><meta charset="utf-8">
<style>
 body {{ margin:0; background:#fbfbfa; font:14px/1.4 Segoe UI, Helvetica, Arial, sans-serif;
        color:#1a1c1f; padding:26px 26px 10px; }}
 h1 {{ font-size:17px; margin:0 0 4px; }}
 .lead {{ color:#5a6068; margin:0 0 22px; font-size:13.5px; }}
 .grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:22px 18px; }}
 .cell {{ background:#fff; border:1px solid #e2e5e9; border-radius:12px; padding:14px; }}
 .row {{ display:flex; align-items:center; gap:14px; }}
 .small {{ display:flex; align-items:center; gap:10px; }}
 p {{ margin:12px 0 0; font-size:13px; color:#5a6068; }}
</style>
<h1>Pendulum logo options</h1>
<p class="lead">Each shown at 96px, 32px and 16px. The 16px version is the favicon test.</p>
<div class="grid">{''.join(cells)}</div>"""

    out_html = ROOT / "site" / "logo_options.html"
    out_html.write_text(html, encoding="utf-8")
    out_png = ROOT / "site" / "logo_options.png"

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1180, "height": 700},
                                device_scale_factor=2)
        page.goto(out_html.as_uri())
        page.wait_for_timeout(300)
        page.screenshot(path=str(out_png), full_page=True)
        browser.close()
    print(f"wrote {out_png.relative_to(ROOT)}  {out_png.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
