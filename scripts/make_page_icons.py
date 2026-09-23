"""The raster tab icons for the two sub-pages, from the SVG each already has.

    python scripts/make_page_icons.py

WHY THESE EXIST. Inequality and Polarisation each shipped ONE icon tag, an SVG.
Firefox and current Chrome take it; Safari and older Chrome do not, and a page
with no icon they can read falls back to the ORIGIN's `/favicon.ico` - which on
this domain is the hub's aperture mark. So two Pendulum pages were wearing
another project's icon in the one browser most likely to be a phone.

TWO TARGETS THAT WANT OPPOSITE ALPHA, which is the whole reason this is a
script and not a hand export:

- **Tab icons** (`<stem>.ico`, `<stem>-48.png`, `<stem>-192.png`) keep the
  rounded corners TRANSPARENT, so the tile reads as a tile. Flattened onto
  white they put four white dots in the corner of every dark tab bar.
- **apple-touch** (`<stem>-180.png`) is flattened, square and full-bleed in the
  tile colour, because iOS applies its own mask and paints transparency BLACK.
  That one is already written by the two mark scripts and is not touched here.

Rasterised with Playwright, like the hub's `tools/make_icons.py`, so this needs
nothing installed beyond what the card renderer already uses.
"""
from __future__ import annotations

import io
import re
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

# page directory -> the stem its existing SVG and apple-touch icon already use
PAGES = {
    "site/inequality": "coins",
    "site/polarisation": "split",
}
SIZES = (48, 192)


def render(pw, svg: str, size: int) -> Image.Image:
    """One square of the mark at `size`, on nothing."""
    b = pw.chromium.launch()
    try:
        pg = b.new_page(viewport={"width": size, "height": size},
                        device_scale_factor=1)
        pg.set_content(
            "<style>html,body{margin:0;padding:0;background:transparent}"
            f"svg{{display:block;width:{size}px;height:{size}px}}</style>{svg}")
        return Image.open(io.BytesIO(pg.screenshot(omit_background=True)))
    finally:
        b.close()


def main() -> int:
    wrote = []
    with sync_playwright() as pw:
        for rel, stem in PAGES.items():
            d = ROOT / rel
            svg = (d / f"{stem}.svg").read_text(encoding="utf-8")
            # the ground stays, the CORNERS come off: the rect is what gives the
            # mark its tile, and rx is what makes the corners transparent
            assert 'rx="18"' in svg, f"{stem}.svg has no rounded tile to keep"
            imgs = {n: render(pw, svg, n) for n in SIZES}
            for n, im in imgs.items():
                im.save(d / f"{stem}-{n}.png")
                wrote.append(f"{rel}/{stem}-{n}.png")
            # .ico carries the small sizes a tab bar actually asks for
            ico = d / f"{stem}.ico"
            imgs[192].save(ico, sizes=[(16, 16), (32, 32), (48, 48)])
            wrote.append(f"{rel}/{stem}.ico")

    for f in wrote:
        print(f"wrote {f}  {(ROOT / f).stat().st_size:,} bytes")

    # the alpha is the point, so check it rather than trusting it
    for rel, stem in PAGES.items():
        im = Image.open(ROOT / rel / f"{stem}-192.png").convert("RGBA")
        corner = im.getpixel((1, 1))
        assert corner[3] == 0, f"{stem}-192.png has an opaque corner: {corner}"
        mid = im.getpixel((96, 96))
        assert mid[3] == 255, f"{stem}-192.png is transparent in the middle"
    print("corners transparent, centres opaque")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
