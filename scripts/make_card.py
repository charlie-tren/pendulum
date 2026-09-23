"""Render the link-preview card for a page, from that page's own chart.

    python scripts/make_card.py inequality
    python scripts/make_card.py polarisation

THE CHART ON THE CARD IS THE PAGE'S OWN CHART, lifted out of a real render.

An earlier version redrew the data itself, on the theory that a hand-drawn chart
could not go stale the way a screenshot could. It went stale anyway, just more
quietly: it drew one source as lines where the page drew dots, kept panel
headers the page had dropped, and labelled its panels with names the key had
moved on from. Every one of those is the same failure, a second implementation
of a drawing that already exists. So this loads the page, waits for it to draw,
and takes its title, its standfirst, its key and its chart verbatim.

ONE RENDERER FOR BOTH PAGES, for the same reason. What differs between them is
four selectors, which is all PAGES holds; a second copy of this file would drift
from the first exactly as the first drifted from the page.

The page is rendered wider than a browser window allows, by lifting the .wrap
max-width before the chart measures itself, because a 960px chart stretched into
a 1200px card is soft. Dark, like the chat window it will be unfurled in.
2400x1260 output, twice what the scrapers ask for.
"""
from __future__ import annotations

import contextlib
import functools
import http.server
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

# the title's class, the key, the chart to lift, and a mark inside that chart
# which only exists once it has actually drawn
PAGES = {
    "inequality": {"title": "h1.coin-title", "legend": "#legend-eras",
                   "chart": "#eras", "ready": "#eras polygon"},
    "polarisation": {"title": "h1.split-title", "legend": "#legend-camps",
                     "chart": "#camps", "ready": "#camps polygon"},
}

W, H = 1200, 630
PAD = 70
# how tall the lifted chart is allowed to be once it is scaled into the card
CHART_H = 348
BG = "#131519"


@contextlib.contextmanager
def served(root: Path):
    """The page over http, not file://.

    It fetches data.json, and a file:// origin cannot, so a file:// render is a
    page that never draws anything: the first attempt at this timed out waiting
    for a polygon that was never going to appear.
    """
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(root))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{srv.server_address[1]}/"
    finally:
        srv.shutdown()
        srv.server_close()


def lift(site: Path, page: dict) -> dict:
    """Open the real page and take its header, its key and its chart.

    The wordmark used to be a copy of the page's SVG pasted into this file as a
    string, and the copy lost: the page's stylesheet, which the card also loads,
    gives `.mark` a flex:none that a pasted mark does not carry, so it stretched
    to fill the flex row and came out four hundred pixels tall. Lifting the
    title fixes that the same way lifting the chart fixed the chart.
    """
    with served(site) as base, sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": 1320, "height": 1000},
                         color_scheme="dark", device_scale_factor=1)
        pg.goto(base, wait_until="networkidle")
        pg.wait_for_selector(page["ready"], timeout=15000)
        # widen the column BEFORE the chart measures itself, then make it
        # re-measure: a chart takes its pixel width from its container
        pg.add_style_tag(content=".wrap { max-width: 1240px !important; }")
        pg.evaluate("() => window.dispatchEvent(new Event('resize'))")
        pg.wait_for_timeout(600)
        out = {k: pg.eval_on_selector(sel, "e => e.outerHTML") for k, sel in (
            ("head", page["title"]), ("sf", ".standfirst"),
            ("legend", page["legend"]), ("svg", page["chart"]))}
        box = pg.eval_on_selector(
            page["chart"],
            "e => e.getAttribute('viewBox').split(' ').slice(2).map(Number)")
        br.close()
    out["ratio"] = box[1] / box[0]
    return out


def card_html(bits: dict, page: dict) -> str:
    # scale to the tallest the card can take, but never wider than the column
    width = min(W - PAD * 2, CHART_H / bits["ratio"])
    title, legend = page["title"], page["legend"]
    return f"""<!doctype html><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400&display=block" rel="stylesheet">
<link rel="stylesheet" href="style.css">
<style>
  body {{ width:{W}px; height:{H}px; background:{BG}; overflow:hidden;
          margin:0; padding:44px {PAD}px 0; }}
  /* the header is the page's own, at the card's scale rather than the page's
     clamp, which is tuned for a browser window and not for a 1200px still */
  {title} {{ font-size:60px; }}
  .standfirst {{ font-size:29px; max-width:none; }}
  {legend} {{ margin-top:26px; font-size:16px; }}
  /* the key keeps its colours and loses its affordances: a picture cannot be
     pressed, so the button chrome and the hover underline are noise on it */
  {legend} .key {{ background:none; border:none; padding:0; }}
  {legend} .explained {{ text-decoration:none; border:0; }}
  .chart {{ width:{width:.0f}px; margin-top:22px; }}
  .chart svg {{ width:100%; height:auto; display:block; }}
</style>
{bits["head"]}
{bits["sf"]}
{bits["legend"]}
<div class="chart">{bits["svg"]}</div>
"""


def main(argv) -> int:
    name = argv[1] if len(argv) > 1 else ""
    if name not in PAGES:
        print(f"usage: make_card.py <{'|'.join(PAGES)}>", file=sys.stderr)
        return 2
    page = PAGES[name]
    site = ROOT / "site" / name

    tmp = site / "_og.html"
    out = site / "og-card.png"
    tmp.write_text(card_html(lift(site, page), page), encoding="utf-8")
    with served(site) as base, sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": W, "height": H},
                         color_scheme="dark", device_scale_factor=2)
        pg.goto(base + tmp.name)
        pg.wait_for_timeout(2500)  # the webfont has to arrive
        pg.screenshot(path=str(out))
        br.close()
    tmp.unlink()
    print(f"wrote {out.relative_to(ROOT)}  {out.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
