"""Build the inequality page's own favicon: one gold stack, square.

The wordmark's SVG is 58x48 and cropped tight to the artwork, so a browser
squashes it into a 16x13 sliver where the coins vanish. This draws into a
square box with its own padding and a solid ground, which is the same lesson
the pendulum favicon already carries.

It is ONE stack rather than the wordmark's three, and that is a deliberate
divergence rather than an oversight. A favicon is read at 16 CSS pixels: three
stacks put 13 coins, 3 face ellipses and 3 milled rings inside 16px of height,
which is roughly one shape per pixel, and rendered at that size they collapsed
into a brown-grey-yellow smudge. Five coins in one column is the same idea with
enough room for the ridges between them to survive. Contact sheet of the ten
candidates: scripts/favicon_options.py.

Colours are baked rather than taken from CSS variables: a favicon is fetched
outside the page, so `var(--coin-gold)` resolves to nothing.

    python scripts/make_coin_icons.py
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "inequality"

BG = "#131519"
# the dark-mode metals, which hold up on the dark tile at any size
METAL = {
    "bronze": ("#b06a28", "#d98f45", "#f0b982"),
    "silver": ("#98a2ac", "#c6ced7", "#e3e9ef"),
    "gold": ("#c69a22", "#ecc457", "#f7e2a4"),
}
# A squarer box than the wordmark, and much fatter coins so they survive 16px.
# The stack is sized to FIT: the top ellipse's crown sits at y=6.4 and the
# bottom body's skirt at y=94.8, because at the contact sheet's proportions the
# skirt ran off the bottom of the tile and the flat cut read as a broken render
# rather than a crop.
RX, RY, STEP, BASE = 26.0, 9.2, 14.0, 71.6
STACKS = [("gold", 50.0, 5)]


def stack(metal: str, cx: float, n: int) -> str:
    """A pile of n coins seen slightly from above, drawn bottom up.

    Each body is STEP + RY tall, not STEP. At STEP alone a coin covers only the
    flat half of the ellipse below it and the curved half shows through as a
    ring. That bug shipped in the wordmark, was fixed there, and then shipped
    again in the GIF renderer, which had its own copy of this function.
    """
    body, face, edge = METAL[metal]
    top = BASE - (n - 1) * STEP
    coins = "".join(
        f'<path d="M{cx - RX} {BASE - i * STEP} L{cx - RX} {BASE - i * STEP + STEP + RY} '
        f'A{RX} {RY} 0 0 0 {cx + RX} {BASE - i * STEP + STEP + RY} '
        f'L{cx + RX} {BASE - i * STEP} Z" fill="{body}" stroke="{edge}" '
        f'stroke-width=".6" stroke-opacity=".45"/>'
        for i in range(n)
    )
    return (f"{coins}"
            f'<ellipse cx="{cx}" cy="{top}" rx="{RX}" ry="{RY}" fill="{face}"/>')


def svg(size: int = 100) -> str:
    art = "".join(stack(m, cx, n) for m, cx, n in STACKS)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}">'
            f'<rect width="{size}" height="{size}" rx="18" fill="{BG}"/>{art}</svg>')


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "coins.svg").write_text(svg(), encoding="utf-8")

    # iOS masks the icon itself and paints any transparency black, so the
    # touch icon is square-cornered and fully opaque
    flat = svg().replace(' rx="18"', "")
    html = (f'<!doctype html><meta charset="utf-8">'
            f'<style>*{{margin:0}}body{{width:180px;height:180px}}'
            f'svg{{width:180px;height:180px;display:block}}</style>{flat}')
    tmp = OUT / "_icon.html"
    tmp.write_text(html, encoding="utf-8")
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": 180, "height": 180}, device_scale_factor=1)
        pg.goto(tmp.as_uri())
        pg.wait_for_timeout(250)
        pg.screenshot(path=str(OUT / "coins-180.png"))
        br.close()
    tmp.unlink()
    for f in ("coins.svg", "coins-180.png"):
        print(f"wrote site/inequality/{f}  {(OUT / f).stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
