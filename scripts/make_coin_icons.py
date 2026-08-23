"""Build the inequality page's own favicon: one gold coin, face on, square.

The wordmark's SVG is 58x48 and cropped tight to the artwork, so a browser
squashes it into a 16x13 sliver where the coins vanish. This draws into a
square box with its own padding and a solid ground, which is the same lesson
the pendulum favicon already carries.

It is ONE coin rather than the wordmark's three stacks, and that is a
deliberate divergence rather than an oversight. A favicon is read at 16 CSS
pixels: three stacks put 13 coins, 3 face ellipses and 3 milled rings inside
16px of height, roughly one shape per pixel, and they collapsed into a
brown-grey-yellow smudge. A single stack was better but still a column of
horizontal bands, and sub-pixel bands blur into a plain gold rectangle. A disc
survives because its silhouette is a circle. Contact sheet of the ten
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
# One coin, face on, filling the tile. Not a stack: a stack is a column of
# horizontal bands, and at 16px the bands are sub-pixel, so the ridges blur into
# a plain gold rectangle and the mark stops being a coin at all. A disc with a
# milled inner ring keeps its silhouette at every size, because the silhouette
# is a circle and a circle survives being one pixel across.
CR = 33.0


def coin(cx: float, cy: float, r: float, metal: str = "gold") -> str:
    """A coin seen face on: a disc, a rim, and a milled inner ring.

    Stroke widths are fractions of the radius rather than fixed, so the rim and
    the ring stay in proportion when the tile is rendered at 180 for iOS and at
    16 for a tab strip.
    """
    body, face, edge = METAL[metal]
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{face}" '
            f'stroke="{body}" stroke-width="{r * 0.13:.2f}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r * 0.66:.2f}" fill="none" '
            f'stroke="{edge}" stroke-width="{r * 0.09:.2f}" stroke-opacity=".75"/>')


def svg(size: int = 100) -> str:
    art = coin(size / 2, size / 2, CR)
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
