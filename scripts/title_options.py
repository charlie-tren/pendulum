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
          "?family=Spectral:wght@500;600;700"
          "&family=Instrument+Serif"
          "&family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700"
          "&family=Playfair+Display:wght@600;700"
          "&family=Newsreader:opsz,wght@6..72,500;6..72,600"
          "&family=DM+Serif+Display"
          "&family=Space+Grotesk:wght@600;700"
          "&family=Bricolage+Grotesque:opsz,wght@12..96,700"
          "&display=swap")

# single quotes: this string goes into an HTML style attribute, and double
# quotes inside it silently truncated the rule
SITE_SERIF = ("'Iowan Old Style','Palatino Linotype',Palatino,Georgia,"
              "'Times New Roman',serif")

OPTIONS = [
    ("Now: system sans, bold",
     "font: 700 44px/1.05 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
     "letter-spacing:-0.02em;"),
    ("Site serif, regular",
     f"font: 400 46px/1.05 {SITE_SERIF}; letter-spacing:-0.015em;"),
    ("Site serif, italic",
     f"font: italic 400 46px/1.05 {SITE_SERIF}; letter-spacing:-0.01em;"),
    ("Spectral 600",
     "font: 600 44px/1.05 Spectral,Georgia,serif; letter-spacing:-0.015em;"),
    ("Instrument Serif",
     "font: 400 52px/1.0 'Instrument Serif',Georgia,serif; letter-spacing:-0.01em;"),
    ("Fraunces 600",
     "font: 600 44px/1.05 Fraunces,Georgia,serif; letter-spacing:-0.02em;"),
    ("Playfair Display 700",
     "font: 700 44px/1.05 'Playfair Display',Georgia,serif; letter-spacing:-0.02em;"),
    ("Newsreader 600",
     "font: 600 46px/1.05 Newsreader,Georgia,serif; letter-spacing:-0.015em;"),
    ("DM Serif Display",
     "font: 400 46px/1.05 'DM Serif Display',Georgia,serif; letter-spacing:-0.01em;"),
    ("Space Grotesk 700",
     "font: 700 43px/1.05 'Space Grotesk',sans-serif; letter-spacing:-0.03em;"),
    ("Bricolage Grotesque 700",
     "font: 700 43px/1.05 'Bricolage Grotesque',sans-serif; letter-spacing:-0.025em;"),
    ("Fraunces 700, wonky",
     "font: 700 44px/1.05 Fraunces,Georgia,serif; letter-spacing:-0.02em;"
     "font-variation-settings:'SOFT' 60,'WONK' 1;"),
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
<h1>Pendulum title typefaces</h1>
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
