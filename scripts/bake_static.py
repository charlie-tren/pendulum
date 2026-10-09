"""Write the page's headline finding into index.html, so it exists without JavaScript.

ChatGPT, Perplexity and most search crawlers read a page without running its
scripts. Pendulum builds every figure in app.js, so to them the page was 176
words of headings and "Loading the data", with no finding they could quote.
ChatGPT was already sending visitors (7 referrals on 04/10/2026) to a page it
could link but not cite.

Nothing new is shown to a reader. The caption under the headline chart is
lifted from the RENDERED page, so the baked text is byte-for-byte the sentence
app.js writes there on load, and app.js still overwrites it when the reader
changes a control. The meta description carries the same sentence.

Run after any data rebuild, since the sentence names a year and two shares:

    python scripts/bake_static.py
"""
from __future__ import annotations

import functools
import html
import http.server
import re
import socket
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PAGE = SITE / "index.html"

LEDE = "How the world's governments have moved along the political spectrum since 1975."


def rendered_caption() -> str:
    # Local so tests can import this module without playwright installed.
    from playwright.sync_api import sync_playwright

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    httpd.log_message = lambda *a, **k: None
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            page = b.new_page()
            page.goto(f"http://127.0.0.1:{port}/", wait_until="networkidle")
            page.wait_for_function("document.querySelector('#caption').textContent.length > 0")
            text = page.evaluate("document.querySelector('#caption').textContent")
            b.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
    return text.strip()


def main() -> None:
    caption = rendered_caption()
    src = PAGE.read_text(encoding="utf-8")

    out, n1 = re.subn(r'(<p class="caption" id="caption">)[^<]*(</p>)',
                      lambda m: m.group(1) + html.escape(caption, quote=False) + m.group(2), src)
    out, n2 = re.subn(r'(<meta name="description" content=")[^"]*(">)',
                      lambda m: m.group(1) + html.escape(f"{LEDE} {caption}", quote=False).replace('"', "&quot;") + m.group(2), out)
    assert n1 == 1 and n2 == 1, f"markers not found: caption {n1}, description {n2}"

    PAGE.write_text(out, encoding="utf-8")
    back = PAGE.read_text(encoding="utf-8")
    assert html.escape(caption, quote=False) in back, "caption did not land"
    print(f"baked: {caption}")


# --- Sibling pages: meta description only ---------------------------------
#
# Inequality and Polarisation get a meta description built from their own data,
# never typed, so the figures move when the data does. Nothing here is visible
# on the page (Charlie, 07/10/2026: crawler text must stay out of sight), so the
# tab title and every element a reader sees are left alone.
#
# Each line was picked from twenty variations for one job: answer a question
# people actually ask an answer engine, in its own words, with a dated figure
# and named places it can cite. Front-loaded, since Google shows ~155 characters.

def polarisation_description() -> str:
    import json
    d = json.loads((SITE / "polarisation" / "data.json").read_text(encoding="utf-8"))
    band = d["bands"]["society"]["camps"]
    year, n = band[-1][0], band[-1][-1]
    def at(country, y):
        return dict(map(tuple, d["society"][country]["camps"]))[y]
    latest = {c: dict(map(tuple, s["camps"])).get(year) for c, s in d["society"].items()}
    top = sorted((c for c in latest if latest[c] is not None), key=lambda c: -latest[c])[:4]
    top = [{"Burma/Myanmar": "Myanmar"}.get(c, c) for c in top]
    us = "United States of America"
    return (f"How polarised is the world? Expert ratings for {n} countries, 1900 to {year}. "
            f"The United States went from {at(us, 1975):.1f} in 1975 to {at(us, year):.1f} "
            f"on a 0 to 4 hostility scale; {', '.join(top[:-1])} and {top[-1]} rate the most "
            f"divided in {year}.")


def inequality_description() -> str:
    import json
    e = json.loads((SITE / "inequality" / "data.json").read_text(encoding="utf-8"))
    sites = sum(1 for p in e["points"] if p["layer"] == "deep")
    year, share = e["countries"]["USA"]["modern"]["top1"][-1]
    start = -e["meta"]["year0"]
    return (f"How unequal has wealth been through history? Wealth Ginis from house floors at "
            f"{sites} excavated sites since {start:,} BC, medieval tax rolls and national "
            f"accounts. In {year} the richest 1% held {share:.0f}% of US wealth.")


SIBLINGS = {
    SITE / "polarisation" / "index.html": polarisation_description,
    SITE / "inequality" / "index.html": inequality_description,
}


def bake_siblings() -> None:
    for page, build in SIBLINGS.items():
        text = build()
        src = page.read_text(encoding="utf-8")
        out, n = re.subn(r'(<meta name="description" content=")[^"]*(">)',
                         lambda m: m.group(1) + html.escape(text, quote=False).replace('"', "&quot;")
                         + m.group(2), src)
        assert n == 1, f"{page}: description marker found {n} times"
        page.write_text(out, encoding="utf-8")
        assert html.escape(text, quote=False) in page.read_text(encoding="utf-8"), f"{page}: did not land"
        print(f"{page.parent.name}: {text}  ({len(text)} chars)")


if __name__ == "__main__":
    main()
    bake_siblings()
