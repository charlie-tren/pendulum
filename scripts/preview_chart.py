"""Throwaway static preview so the numbers can be eyeballed before any real
frontend exists. Generates inline SVG — no JS, no deps."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data" / "out" / "orientation.json").read_text(encoding="utf-8"))

BANDS = [("left", "#c0392b", "Left"), ("centre", "#b0a44f", "Centre"),
         ("right", "#2c5f8a", "Right"), ("uncoded", "#cfcfcf", "No left-right code")]
W, H, PAD = 900, 300, {"l": 46, "r": 12, "t": 14, "b": 30}


def stacked(series, key_pop=True):
    years = [r["year"] for r in series]
    x0, x1 = min(years), max(years)
    iw, ih = W - PAD["l"] - PAD["r"], H - PAD["t"] - PAD["b"]
    sx = lambda y: PAD["l"] + (y - x0) / (x1 - x0) * iw
    sy = lambda v: PAD["t"] + (1 - v) * ih
    out, base = [], [0.0] * len(series)
    for key, colour, _ in BANDS:
        top = [base[i] + (series[i][key] or 0) for i in range(len(series))]
        pts = ([f"{sx(series[i]['year']):.1f},{sy(top[i]):.1f}" for i in range(len(series))] +
               [f"{sx(series[i]['year']):.1f},{sy(base[i]):.1f}" for i in range(len(series) - 1, -1, -1)])
        out.append(f'<polygon points="{" ".join(pts)}" fill="{colour}"/>')
        base = top
    for y in range(1980, x1 + 1, 10):
        out.append(f'<text x="{sx(y):.0f}" y="{H-10}" font-size="11" fill="#666" '
                   f'text-anchor="middle">{y}</text>')
    for v in (0, .25, .5, .75, 1):
        out.append(f'<text x="{PAD["l"]-6}" y="{sy(v)+4:.0f}" font-size="11" fill="#666" '
                   f'text-anchor="end">{v:.0%}</text>')
    return f'<svg viewBox="0 0 {W} {H}" width="100%">{"".join(out)}</svg>'


def legend():
    items = "".join(f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:18px">'
                    f'<span style="width:13px;height:13px;background:{c};display:inline-block;'
                    f'border-radius:2px"></span>{lab}</span>' for _, c, lab in BANDS)
    return f'<div style="font-size:13px;margin:6px 0 14px">{items}</div>'


panels = []
for gk, title, note in [
    ("world", "World — share of population by government orientation",
     "Grey is now ~2% for 1975–2019, down from ~25% on DPI alone. The step up in 2020 is "
     "<b>not a political event</b> — it is V-Party's coverage ending in 2019. It must be "
     "annotated on the real site or it reads as a finding."),
    ("asean", "ASEAN — share of population",
     "Was 18% coded on DPI alone, which rendered ASEAN as 100% left-wing off Vietnam and Laos. "
     "Now 60%, with Indonesia resolved as left via V-Party."),
    ("g7", "G7 — share of population", "Fully coded throughout. No grey at all."),
]:
    g = DATA["groups"][gk]
    panels.append(f'<h2 style="font:600 17px system-ui;margin:26px 0 2px">{title}</h2>'
                  f'<p style="font:14px/1.5 system-ui;color:#555;margin:0 0 8px">{note}</p>'
                  f'{legend()}{stacked(g["by_population"])}')

# provenance panel - which source resolved each year
SRC = [("dpi", "#4a6fa5", "DPI"), ("vparty", "#7aa06b", "V-Party"),
       ("carry_forward", "#d4a55c", "Carry-forward"), ("none", "#cfcfcf", "Unresolved")]
w = DATA["groups"]["world"]["by_country"]
years = [r["year"] for r in w]
x0, x1 = min(years), max(years)
iw, ih = W - PAD["l"] - PAD["r"], H - PAD["t"] - PAD["b"]
sx = lambda y: PAD["l"] + (y - x0) / (x1 - x0) * iw
sy = lambda v: PAD["t"] + (1 - v) * ih
parts, base = [], [0.0] * len(w)
for key, colour, _ in SRC:
    top = [base[i] + w[i]["source"][key] for i in range(len(w))]
    pts = ([f"{sx(w[i]['year']):.1f},{sy(top[i]):.1f}" for i in range(len(w))] +
           [f"{sx(w[i]['year']):.1f},{sy(base[i]):.1f}" for i in range(len(w) - 1, -1, -1)])
    parts.append(f'<polygon points="{" ".join(pts)}" fill="{colour}"/>')
    base = top
for y in range(1980, x1 + 1, 10):
    parts.append(f'<text x="{sx(y):.0f}" y="{H-10}" font-size="11" fill="#666" '
                 f'text-anchor="middle">{y}</text>')
leg = "".join(f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:18px">'
              f'<span style="width:13px;height:13px;background:{c};display:inline-block;'
              f'border-radius:2px"></span>{lab}</span>' for _, c, lab in SRC)
panels.append('<h2 style="font:600 17px system-ui;margin:26px 0 2px">Provenance — which '
              'source resolved each country-year</h2>'
              '<p style="font:14px/1.5 system-ui;color:#555;margin:0 0 8px">The V-Party cliff at '
              '2020 is plain here. Carry-forward partially covers it; the rest needs hand-coding.</p>'
              f'<div style="font-size:13px;margin:6px 0 14px">{leg}</div>'
              f'<svg viewBox="0 0 {W} {H}" width="100%">{"".join(parts)}</svg>')

html = f"""<title>Pendulum — data preview</title>
<div style="max-width:940px;margin:32px auto;padding:0 18px;font-family:system-ui">
<h1 style="font-size:24px;margin:0">Pendulum — pipeline preview</h1>
<p style="font:14px/1.6 system-ui;color:#555">
Database of Political Institutions 2023 (IDB), CC-BY 4.0, 1975&ndash;2023.
Population from Our World in Data / UN WPP. Red=left and blue=right follows the
international convention, which is inverted relative to US media.</p>
{"".join(panels)}
</div>"""
(ROOT / "site" / "preview.html").write_text(html, encoding="utf-8")
print("wrote site/preview.html")
