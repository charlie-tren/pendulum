"""Render the link-preview card for the inequality page.

THE CHART ON THIS CARD IS THE PAGE'S OWN CHART, lifted out of a real render.

The card used to redraw the data itself, on the theory that a hand-drawn chart
could not go stale the way a screenshot could. It went stale anyway, just more
quietly: it drew Alfani's regional series as four lines when the page draws
them as dots, it kept panel headers after the page dropped them, it labelled
the panels "Excavated settlements" and "Whole countries" after the key had
settled on "Excavated sites" and "All countries", it had equal-width panels
where the page weights them by the log of their span, and it had neither the
kernel averages nor the picked country's line, because reimplementing those
here would have been a second copy of an estimator to keep in step.

Every one of those is the same failure: a second implementation of a drawing
that already exists, diverging one commit at a time. So this loads the page,
waits for it to draw, and takes its `#eras` SVG and its key verbatim. There is
nothing left to drift.

The page is rendered wider than a browser window would allow, by lifting the
.wrap max-width before the chart measures itself, because the card is 1200
wide and a 960px chart stretched into it would be soft. Dark, like the other
card and like the chat window it will be unfurled in. 2400x1260 output, twice
what the scrapers ask for.

    python scripts/make_inequality_card.py
"""
from __future__ import annotations

import contextlib
import functools
import http.server
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site" / "inequality"

W, H = 1200, 630
PAD = 70
# how tall the lifted chart is allowed to be once it is scaled into the card
CHART_H = 348
# the page's own dark palette, so the card reads as the page at night
BG, INK, INK_SOFT = "#131519", "#e9ecf0", "#a7aeb8"

@contextlib.contextmanager
def served(root: Path):
    """The page over http, not file://.

    It fetches data.json, and a file:// origin cannot, so a file:// render is a
    page that never draws anything. The chart simply never appeared and the
    first attempt at this timed out waiting for a polygon.
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


def lift() -> dict:
    """Open the real page and take its header, its key and its chart.

    The wordmark used to be a copy of the page's SVG pasted into this file as a
    string, and the copy lost: the page's own stylesheet, which the card also
    loads, styles `.mark` with a flex:none and an em height, and a pasted mark
    without that class stretched to fill the flex row. The coins came out four
    hundred pixels tall. Lifting the h1 solves it the same way lifting the chart
    solved the chart, by having one implementation instead of two.
    """
    with served(SITE) as base, sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={"width": 1320, "height": 1000},
                         color_scheme="dark", device_scale_factor=1)
        pg.goto(base, wait_until="networkidle")
        pg.wait_for_selector("#eras polygon", timeout=15000)
        # widen the column BEFORE the chart measures itself, then make it
        # re-measure: the chart takes its pixel width from its container, and
        # the page caps that at 960
        pg.add_style_tag(content=".wrap { max-width: 1240px !important; }")
        pg.evaluate("() => window.dispatchEvent(new Event('resize'))")
        pg.wait_for_timeout(600)
        out = {k: pg.eval_on_selector(sel, "e => e.outerHTML") for k, sel in (
            ("head", "h1.coin-title"), ("sf", ".standfirst"),
            ("legend", "#legend-eras"), ("svg", "#eras"))}
        box = pg.eval_on_selector(
            "#eras", "e => e.getAttribute('viewBox').split(' ').slice(2).map(Number)")
        br.close()
    out["ratio"] = box[1] / box[0]
    return out


def card_html(bits: dict) -> str:
    # scale to the tallest the card can take, but never wider than the column
    width = min(W - PAD * 2, CHART_H / bits["ratio"])
    return f"""<!doctype html><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400&display=block" rel="stylesheet">
<link rel="stylesheet" href="style.css">
<style>
  body {{ width:{W}px; height:{H}px; background:{BG}; overflow:hidden;
          margin:0; padding:44px {PAD}px 0; }}
  /* the header is the page's own, at the card's scale rather than the page's
     clamp, which is tuned for a browser window and not for a 1200px still */
  h1.coin-title {{ font-size:60px; }}
  .standfirst {{ font-size:29px; max-width:none; }}
  #legend-eras {{ margin-top:26px; font-size:16px; }}
  /* the key keeps its colours and loses its affordances: a picture cannot be
     pressed, so the button chrome and the hover underline are noise on it */
  #legend-eras .key {{ background:none; border:none; padding:0; }}
  #legend-eras .explained {{ text-decoration:none; border:0; }}
  .chart {{ width:{width:.0f}px; margin-top:22px; }}
  .chart svg {{ width:100%; height:auto; display:block; }}
</style>
{bits["head"]}
{bits["sf"]}
{bits["legend"]}
<div class="chart">{bits["svg"]}</div>
"""


def main() -> int:
    tmp = SITE / "_og.html"
    out = SITE / "og-card.png"
    tmp.write_text(card_html(lift()), encoding="utf-8")
    with served(SITE) as base, sync_playwright() as pw:
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
    raise SystemExit(main())
