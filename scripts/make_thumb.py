"""Static SVG thumbnail for the site index.

Drawn from the real data rather than a screenshot, so it cannot drift out of
date in a way that misrepresents the page.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data" / "out" / "orientation.json").read_text(encoding="utf-8"))

W, H = 1400, 874
PAD = {"l": 70, "r": 60, "t": 150, "b": 90}
BANDS = ["left", "centre", "right", "no_reading", "unresolved"]

series = [r for r in DATA["groups"]["world"]["by_population"] if r["year"] <= 2023]
pal = DATA["palette"]["buckets"]
years = [r["year"] for r in series]
y0, y1 = min(years), max(years)
iw, ih = W - PAD["l"] - PAD["r"], H - PAD["t"] - PAD["b"]
sx = lambda y: PAD["l"] + (y - y0) / (y1 - y0) * iw
sy = lambda v: PAD["t"] + (1 - v) * ih

parts = [f'<rect width="{W}" height="{H}" fill="#fbfbfa"/>']
base = [0.0] * len(series)
for key in BANDS:
    top = [base[i] + (series[i][key] or 0) for i in range(len(series))]
    pts = ([f"{sx(series[i]['year']):.1f},{sy(top[i]):.1f}" for i in range(len(series))] +
           [f"{sx(series[i]['year']):.1f},{sy(base[i]):.1f}" for i in range(len(series) - 1, -1, -1)])
    parts.append(f'<polygon points="{" ".join(pts)}" fill="{pal[key]["colour"]}"/>')
    base = top

parts.append(f'<text x="{PAD["l"]}" y="78" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
             f'font-size="52" font-weight="700" fill="#1a1c1f">Pendulum</text>')
parts.append(f'<text x="{PAD["l"]}" y="118" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
             f'font-size="26" fill="#5a6068">Share of the world&#8217;s people by how their '
             f'country is governed, {y0} to {y1}</text>')
for yr in range(1980, y1 + 1, 10):
    parts.append(f'<text x="{sx(yr):.0f}" y="{H - 46}" text-anchor="middle" '
                 f'font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="24" '
                 f'fill="#767d86">{yr}</text>')
x = PAD["l"]
for key in ["left", "centre", "right"]:
    parts.append(f'<rect x="{x}" y="{H - 32}" width="20" height="20" rx="4" fill="{pal[key]["colour"]}"/>')
    parts.append(f'<text x="{x + 28}" y="{H - 15}" font-family="Segoe UI, Helvetica, Arial, sans-serif" '
                 f'font-size="23" fill="#5a6068">{pal[key]["label"]}</text>')
    x += 150

out = ROOT / "site" / "thumb.svg"
out.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
               f'height="{H}">{"".join(parts)}</svg>', encoding="utf-8")
print(f"wrote {out.relative_to(ROOT)}  {out.stat().st_size:,} bytes")
