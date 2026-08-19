"""Render title typeface candidates to a PNG contact sheet.

The homepage sets a serif voice (Iowan Old Style / Palatino / Georgia at
weight 400, italic for emphasis) and already loads Spectral and Hanken Grotesk
from Google. Pendulum currently uses a bold system sans, which belongs to a
different site. These are the alternatives, shown with the mark and the
standfirst so the pairing is judged rather than the letterforms alone.
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

GOOGLE = ("https://fonts.googleapis.com/css2"
          "?family=Instrument+Serif:ital@0;1"
          "&family=Libre+Caslon+Display"
          "&family=Young+Serif"
          "&family=Bodoni+Moda:opsz,wght@6..96,500;6..96,700"
          "&family=Lora:wght@600;700"
          "&family=Crimson+Pro:wght@500;600"
          "&family=Petrona:wght@500;600"
          "&family=Gloock"
          "&family=Bitter:wght@600;700"
          "&family=Zilla+Slab:wght@500;600"
          "&family=Syne:wght@700;800"
          "&family=Familjen+Grotesk:wght@600;700"
          "&family=Unbounded:wght@600"
          "&family=Cormorant+Garamond:wght@600;700"
          "&display=swap")

# single quotes: this string goes into an HTML style attribute, and double
# quotes inside it silently truncated the rule
SITE_SERIF = ("'Iowan Old Style','Palatino Linotype',Palatino,Georgia,"
              "'Times New Roman',serif")

OPTIONS = [
    ("Now: Instrument Serif",
     "font: 400 54px/1.0 'Instrument Serif',Georgia,serif; letter-spacing:-0.005em;"),
    ("Instrument Serif, italic",
     "font: italic 400 54px/1.0 'Instrument Serif',Georgia,serif;"),
    ("Libre Caslon Display",
     "font: 400 46px/1.05 'Libre Caslon Display',Georgia,serif; letter-spacing:-0.01em;"),
    ("Young Serif",
     "font: 400 45px/1.05 'Young Serif',Georgia,serif; letter-spacing:-0.015em;"),
    ("Bodoni Moda 700",
     "font: 700 46px/1.05 'Bodoni Moda',Didot,Georgia,serif; letter-spacing:-0.01em;"),
    ("Gloock",
     "font: 400 47px/1.02 Gloock,Georgia,serif; letter-spacing:-0.01em;"),
    ("Cormorant Garamond 700",
     "font: 700 54px/1.0 'Cormorant Garamond',Garamond,serif; letter-spacing:-0.005em;"),
    ("Lora 700",
     "font: 700 42px/1.05 Lora,Georgia,serif; letter-spacing:-0.02em;"),
    ("Crimson Pro 600",
     "font: 600 48px/1.02 'Crimson Pro',Georgia,serif; letter-spacing:-0.015em;"),
    ("Petrona 600",
     "font: 600 46px/1.03 Petrona,Georgia,serif; letter-spacing:-0.015em;"),
    ("Zilla Slab 600",
     "font: 600 43px/1.05 'Zilla Slab',Georgia,serif; letter-spacing:-0.02em;"),
    ("Bitter 700",
     "font: 700 41px/1.05 Bitter,Georgia,serif; letter-spacing:-0.025em;"),
    ("Syne 800",
     "font: 800 41px/1.05 Syne,sans-serif; letter-spacing:-0.03em;"),
    ("Familjen Grotesk 700",
     "font: 700 43px/1.05 'Familjen Grotesk',sans-serif; letter-spacing:-0.03em;"),
    ("Unbounded 600",
     "font: 600 38px/1.08 Unbounded,sans-serif; letter-spacing:-0.03em;"),
    ("Site serif, regular",
     f"font: 400 46px/1.05 {SITE_SERIF}; letter-spacing:-0.015em;"),
]

MARK = """<svg class="mark" viewBox="0 8 58 48" aria-hidden="true">
  <line x1="9" y1="12" x2="55" y2="12" stroke="currentColor" stroke-width="3.4" stroke-linecap="round"/>
  <line x1="20" y1="12" x2="9" y2="35" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" opacity=".55"/>
  <circle cx="8" cy="40" r="6.8" fill="#2f6fb2"/>
  <line x1="32" y1="12" x2="32" y2="41" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" opacity=".55"/>
  <circle cx="32" cy="47" r="6.8" fill="#7d5ba6"/>
  <line x1="44" y1="12" x2="45" y2="41" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" opacity=".55"/>
  <circle cx="45" cy="47" r="6.8" fill="#c33c3c"/>
</svg>"""


def main() -> int:
    cells = "".join(
        f'<div class="cell"><p class="tag">{name}</p>'
        f'<div class="title" style="{css}">{MARK}<span>Pendulum</span></div>'
        f'<p class="stand">Most charts of world politics count countries, which makes '
        f'Tuvalu equal to India.</p></div>'
        for name, css in OPTIONS)

    html = f"""<!doctype html><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{GOOGLE}">
<style>
 body {{ margin:0; background:#fbfbfa; color:#1a1c1f; padding:26px 26px 12px;
        font:15px/1.6 -apple-system,'Segoe UI',sans-serif; }}
 h1 {{ font-size:17px; margin:0 0 18px; }}
 .grid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:16px; }}
 .cell {{ background:#fff; border:1px solid #e2e5e9; border-radius:12px; padding:18px 20px 16px; }}
 .tag {{ margin:0 0 10px; font-size:12px; letter-spacing:.07em; text-transform:uppercase;
        color:#8b9199; font-weight:600; }}
 .title {{ display:flex; align-items:center; gap:14px; color:#1a1c1f; }}
 .title .mark {{ height:1.02em; width:auto; flex:none; color:#5a6068; }}
 .stand {{ margin:10px 0 0; color:#5a6068; font-size:15px;
          font-family:-apple-system,'Segoe UI',sans-serif; max-width:40ch; }}
</style>
<h1>Pendulum title typefaces, round two</h1>
<div class="grid">{cells}</div>"""

    out_html = ROOT / "site" / "title_options.html"
    out_html.write_text(html, encoding="utf-8")
    out_png = ROOT / "site" / "title_options.png"

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1120, "height": 900},
                                device_scale_factor=2)
        page.goto(out_html.as_uri())
        page.wait_for_timeout(2500)          # let the webfonts land
        page.screenshot(path=str(out_png), full_page=True)
        browser.close()
    print(f"wrote {out_png.relative_to(ROOT)}  {out_png.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
