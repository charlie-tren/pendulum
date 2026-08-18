"""Inline the CSS, JS and data into one openable HTML file.

The deployed site stays as separate files — this exists so the page can be
handed to someone as a single attachment and still work with no server.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

html = (SITE / "index.html").read_text(encoding="utf-8")
css = (SITE / "style.css").read_text(encoding="utf-8")
js = (SITE / "app.js").read_text(encoding="utf-8")
data = json.loads((SITE / "orientation.json").read_text(encoding="utf-8"))

# app.js already prefers window.__PENDULUM__ over fetch, so nothing to rewrite —
# but assert that contract still holds rather than silently shipping a file that
# tries to fetch from file:// and renders blank.
assert "window.__PENDULUM__ || fetch(" in js, "boot block changed — standalone would break"

html = html.replace('<link rel="stylesheet" href="style.css">', f"<style>\n{css}\n</style>")
html = html.replace(
    '<script src="app.js"></script>',
    f"<script>window.__PENDULUM__ = {json.dumps(data, separators=(',', ':'))};</script>\n"
    f"<script>\n{js}\n</script>",
)
html = html.replace(
    "</main>",
    '<p class="fine wrap" style="max-width:none;padding:0">'
    "Single-file build. The deployed site loads its data separately.</p></main>",
)

out = SITE / "standalone.html"
out.write_text(html, encoding="utf-8")
print(f"wrote {out.relative_to(ROOT)}  {out.stat().st_size:,} bytes")
