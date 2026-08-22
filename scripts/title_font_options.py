"""Render title-font candidates for both pages, as one contact sheet.

Both wordmarks shown in every face so the pair can be judged together, which is
the actual decision: they sit two clicks apart and have to look like siblings.

The site currently uses the plain serif stack charlietrenorden.com sets on its
body, chosen over fourteen webfonts in an earlier round. Anything here that
needs a Google Font is marked, because loading one costs a request and a late
swap that the current setup does not pay.

    python scripts/title_font_options.py
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "_title_fonts.png"

# SINGLE quotes inside the stacks. These go into a style="..." attribute, and a
# double quote there closes the attribute, which silently left every cell in the
# fallback sans and made all eleven faces look identical.
SYSTEM = ("'Iowan Old Style','Palatino Linotype',Palatino,Georgia,"
          "'Times New Roman',serif")

# name -> (css font-family, google family or None, weight, letter-spacing, note)
FACES = [
    ("Current: Iowan / Palatino", SYSTEM, None, 400, "-.015em",
     "what is live. No request, no swap, matches the homepage"),
    ("Spectral", "'Spectral',serif", "Spectral:wght@300;400", 300, "-.01em",
     "already loaded elsewhere on the site"),
    ("EB Garamond", "'EB Garamond',serif", "EB+Garamond:wght@400;500", 400, "0",
     "old-style, wide, bookish"),
    ("Libre Baskerville", "'Libre Baskerville',serif", "Libre+Baskerville:wght@400", 400, "-.02em",
     "high contrast, sturdy, a touch newspaper"),
    ("Fraunces", "'Fraunces',serif", "Fraunces:opsz,wght@9..144,400;9..144,600", 400, "-.015em",
     "soft, contemporary, slightly odd on purpose"),
    ("Instrument Serif", "'Instrument Serif',serif", "Instrument+Serif:ital@0;1", 400, "-.02em",
     "very tight, display-only, was offered before"),
    ("Playfair Display", "'Playfair Display',serif", "Playfair+Display:wght@400;500", 400, "-.015em",
     "high contrast, editorial, common"),
    ("Cormorant Garamond", "'Cormorant Garamond',serif", "Cormorant+Garamond:wght@400;500", 500, "0",
     "delicate, small on the body, wants size"),
    ("Newsreader", "'Newsreader',serif", "Newsreader:opsz,wght@6..72,400;6..72,500", 400, "-.01em",
     "made for screens, plainer than Playfair"),
    ("Inter Tight", "'Inter Tight',sans-serif", "Inter+Tight:wght@500;600", 600, "-.03em",
     "sans, would break from the rest of the site"),
    ("Space Grotesk", "'Space Grotesk',sans-serif", "Space+Grotesk:wght@500", 500, "-.02em",
     "sans, technical, reads as a tool"),
]

CRADLE = """<svg viewBox="0 8 58 48" style="height:1.06em;width:auto;overflow:visible;color:#a7aeb8">
  <line x1="9" y1="12" x2="55" y2="12" stroke="currentColor" stroke-width="3.4" stroke-linecap="round"/>
  <g transform="rotate(32 20 12)"><line x1="20" y1="12" x2="20" y2="41" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" opacity=".55"/><circle cx="20" cy="47" r="6" fill="#2f6fb2"/></g>
  <line x1="32" y1="12" x2="32" y2="41" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" opacity=".55"/><circle cx="32" cy="47" r="6" fill="#9042d4"/>
  <line x1="44" y1="12" x2="44" y2="41" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" opacity=".55"/><circle cx="44" cy="47" r="6" fill="#c33c3c"/>
</svg>"""

RX, RY, ST, BASE = 6.6, 2.6, 4.2, 51.0
METAL = {"bronze": ("#b06a28", "#d98f45"), "silver": ("#98a2ac", "#c6ced7"),
         "gold": ("#c69a22", "#ecc457")}


def coin_stack(metal, cx, n):
    body, face = METAL[metal]
    top = BASE - (n - 1) * ST
    rims = "".join(
        f'<path d="M{cx - RX} {BASE - i * ST} A{RX} {RY} 0 0 0 {cx + RX} {BASE - i * ST}" '
        f'fill="none" stroke="{face}" stroke-width=".55" opacity=".7"/>' for i in range(n - 1))
    return (f'<path d="M{cx - RX} {top} L{cx - RX} {BASE} A{RX} {RY} 0 0 0 {cx + RX} {BASE} '
            f'L{cx + RX} {top} Z" fill="{body}"/>{rims}'
            f'<ellipse cx="{cx}" cy="{top}" rx="{RX}" ry="{RY}" fill="{face}"/>')


COINS = ('<svg viewBox="0 8 58 48" style="height:1.06em;width:auto;overflow:visible">'
         + coin_stack("bronze", 13, 2) + coin_stack("silver", 29, 3)
         + coin_stack("gold", 45, 9) + "</svg>")

ROW = """<div class="cell">
  <div class="pair" style="font-family:{fam};font-weight:{w};letter-spacing:{ls}">
    <div class="wm">{cradle}<span>Pendulum</span></div>
    <div class="wm">{coins}<span>Inequality</span></div>
  </div>
  <div class="meta"><b>{n}. {name}</b>{tag}<span class="note">{note}</span></div>
</div>"""

HTML = """<!doctype html><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?{families}&display=block" rel="stylesheet">
<style>
  * {{ margin:0; box-sizing:border-box; }}
  body {{ background:#131519; color:#e9ecf0; padding:32px 30px 26px; width:1180px;
         font:14px/1.5 -apple-system,"Segoe UI",Roboto,sans-serif; }}
  h1 {{ font:400 26px/1.2 {system}; margin-bottom:4px; }}
  p.intro {{ color:#98a0aa; margin-bottom:24px; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px 20px; }}
  .cell {{ border:1px solid #2b2f36; border-radius:12px; background:#1a1d22; padding:16px 18px 13px; }}
  .pair {{ display:flex; flex-direction:column; gap:6px; }}
  .wm {{ display:flex; align-items:center; gap:18px; font-size:38px; line-height:1.15; }}
  .meta {{ margin-top:12px; font-size:12px; color:#98a0aa; display:flex;
          align-items:baseline; gap:8px; flex-wrap:wrap; }}
  .meta b {{ color:#e9ecf0; font-size:12.5px; }}
  .tag {{ border:1px solid #2b2f36; border-radius:999px; padding:1px 7px; font-size:11px; }}
  .note {{ flex:1 1 100%; }}
</style>
<h1>Title faces</h1>
<p class="intro">Both wordmarks in every face. They sit two clicks apart, so the pair is the decision.</p>
<div class="grid">{cells}</div>
"""


def main() -> int:
    fams = "&".join(f"family={g}" for _, _, g, _, _, _ in
                    ((n, f, g, w, ls, note) for n, f, g, w, ls, note in FACES) if g)
    cells = "".join(
        ROW.format(fam=fam, w=w, ls=ls, cradle=CRADLE, coins=COINS, n=i + 1, name=name,
                   note=note,
                   tag='<span class="tag">webfont</span>' if g else '<span class="tag">no request</span>')
        for i, (name, fam, g, w, ls, note) in enumerate(FACES))
    tmp = ROOT / "site" / "_fonts.html"
    tmp.write_text(HTML.format(families=fams, cells=cells, system=SYSTEM), encoding="utf-8")
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": 1180, "height": 900}, device_scale_factor=2)
        pg.goto(tmp.as_uri())
        pg.wait_for_timeout(2500)          # webfonts must actually arrive
        pg.screenshot(path=str(OUT), full_page=True)
        br.close()
    tmp.unlink()
    print(f"wrote {OUT.relative_to(ROOT)}  {OUT.stat().st_size:,} bytes, {len(FACES)} faces")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
