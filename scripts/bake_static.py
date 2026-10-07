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

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PAGE = SITE / "index.html"

LEDE = "How the world's governments have moved along the political spectrum since 1975."


def rendered_caption() -> str:
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


if __name__ == "__main__":
    main()
