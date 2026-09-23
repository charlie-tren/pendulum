"""Build the polarisation page's favicon: two humps, square.

Same lesson as the other two marks. The wordmark is 64x44 and cropped tight, so
a browser squashes it into a sliver; this redraws it into a square box with its
own padding and a solid ground.

The humps are FATTER and FURTHER APART than the wordmark's, because at 16 CSS
pixels the thing that has to survive is the gap between them. A bimodal curve
whose two peaks merge is just a curve, and a curve is not the idea. The
coin-stack favicon lost its ridges the same way and ended up a single coin.

    python scripts/make_split_icons.py
"""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "polarisation"

BG = "#131519"
# the dark-mode blues and reds, which hold up on a dark tile at any size
LEFT, RIGHT = "#6ea8e0", "#d95555"
BASE = "#4c545f"


def humps(size: int = 100) -> str:
    """Two peaks and the floor they stand on.

    Drawn as cubic curves from the floor up to a peak and back down, so the
    silhouette is a filled mound rather than an outline: a 1px outline is
    invisible at favicon size, a filled mass is not.
    """
    y0, top = 78.0, 24.0
    gap = 6.0                       # the dead space at the centre, in units
    mid = size / 2
    left = (f'<path d="M10 {y0} C 20 {y0} 20 {top} 30 {top} '
            f'C 40 {top} 40 {y0} {mid - gap / 2} {y0} Z" fill="{LEFT}"/>')
    right = (f'<path d="M{mid + gap / 2} {y0} C 60 {y0} 60 {top} 70 {top} '
             f'C 80 {top} 80 {y0} 90 {y0} Z" fill="{RIGHT}"/>')
    floor = (f'<rect x="10" y="{y0}" width="80" height="6" rx="3" fill="{BASE}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}">'
            f'<rect width="{size}" height="{size}" rx="18" fill="{BG}"/>'
            f"{floor}{left}{right}</svg>")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "split.svg").write_text(humps(), encoding="utf-8")

    # iOS masks the icon itself and paints any transparency black, so the touch
    # icon is square-cornered and fully opaque
    flat = humps().replace(' rx="18"', "", 1)
    tmp = OUT / "_icon.html"
    tmp.write_text(
        f'<!doctype html><meta charset="utf-8">'
        f'<style>*{{margin:0}}body{{width:180px;height:180px}}'
        f'svg{{width:180px;height:180px;display:block}}</style>{flat}',
        encoding="utf-8")
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": 180, "height": 180}, device_scale_factor=1)
        pg.goto(tmp.as_uri())
        pg.wait_for_timeout(250)
        pg.screenshot(path=str(OUT / "split-180.png"))
        br.close()
    tmp.unlink()
    for f in ("split.svg", "split-180.png"):
        print(f"wrote site/polarisation/{f}  {(OUT / f).stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
