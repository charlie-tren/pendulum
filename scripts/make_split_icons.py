"""Build the polarisation page's favicon: two arrows leaving, square.

Same lesson as the other two marks. The wordmark is 64x44 and cropped tight, so
a browser squashes it into a sliver; this redraws it into a square box with its
own padding and a solid ground.

The mark replaces a two-humped curve, which was a picture of the distribution
being measured and therefore only legible to someone who had already read the
chart. An arrow needs no such introduction. The two are stacked rather than
level because a mirror-symmetrical pair reads as one double-headed arrow.

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


def arrows(size: int = 100) -> str:
    """Two arrows leaving each other, one above the other.

    Stacked rather than level, which is what was picked over a level pair: an
    offset reads as two things departing, where a mirror-symmetrical pair reads
    as one double-headed arrow. Stroked rather than solid, because a shaft with
    a chevron head keeps its shape when a favicon is resampled to 16 pixels and
    a filled triangle turns into a lump.
    """
    def arrow(x_tail, x_head, y, colour, w=9.0, head=12.0):
        d = -1 if x_head < x_tail else 1
        return (f'<g stroke="{colour}" stroke-width="{w}" stroke-linecap="round" '
                f'stroke-linejoin="round" fill="none">'
                f'<path d="M{x_tail} {y} H{x_head}"/>'
                f'<path d="M{x_head - d * head} {y - head} L{x_head} {y} '
                f'L{x_head - d * head} {y + head}"/></g>')

    art = arrow(58, 16, 34, LEFT) + arrow(42, 84, 66, RIGHT)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}">'
            f'<rect width="{size}" height="{size}" rx="18" fill="{BG}"/>{art}</svg>')


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "split.svg").write_text(arrows(), encoding="utf-8")

    # iOS masks the icon itself and paints any transparency black, so the touch
    # icon is square-cornered and fully opaque
    flat = arrows().replace(' rx="18"', "", 1)
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
