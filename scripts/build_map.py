"""Project Natural Earth country outlines into SVG paths at build time.

The projection is done here rather than in the browser so the site needs no
mapping library at all: it ships a dictionary of ISO3 to path string and colours
them in. Robinson, because this is a world thematic map and Mercator would make
the argument about population look absurd.

Input  : data/raw/ne_110m_countries.geojson (Natural Earth 1:110m, public domain)
Output : data/out/map.json
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "out"

WIDTH = 1000
# Antarctica is a projection artefact more than a country here, and no
# government sits on it.
SKIP = {"ATA"}

# Robinson lookup, 0 to 90 degrees in 5 degree steps. X is the length of the
# parallel relative to the equator, Y its distance from the equator.
ROBINSON_X = [1.0000, 0.9986, 0.9954, 0.9900, 0.9822, 0.9730, 0.9600, 0.9427,
              0.9216, 0.8962, 0.8679, 0.8350, 0.7986, 0.7597, 0.7186, 0.6732,
              0.6213, 0.5722, 0.5322]
ROBINSON_Y = [0.0000, 0.0620, 0.1240, 0.1860, 0.2480, 0.3100, 0.3720, 0.4340,
              0.4958, 0.5571, 0.6176, 0.6769, 0.7346, 0.7903, 0.8435, 0.8936,
              0.9394, 0.9761, 1.0000]


def robinson(lon: float, lat: float) -> tuple[float, float]:
    a = min(abs(lat), 89.999) / 5.0
    i = min(int(a), 17)
    f = a - i
    x = ROBINSON_X[i] + (ROBINSON_X[i + 1] - ROBINSON_X[i]) * f
    y = ROBINSON_Y[i] + (ROBINSON_Y[i + 1] - ROBINSON_Y[i]) * f
    return 0.8487 * x * (lon * 3.14159265358979 / 180.0), 1.3523 * y * (1 if lat >= 0 else -1)


def iso3(props: dict) -> str | None:
    for key in ("ISO_A3", "ISO_A3_EH", "ADM0_A3"):
        value = props.get(key)
        if value and value not in ("-99", "-099"):
            return value
    return None


def rings(geometry: dict):
    kind, coords = geometry["type"], geometry["coordinates"]
    if kind == "Polygon":
        return coords
    if kind == "MultiPolygon":
        return [ring for poly in coords for ring in poly]
    return []


def main() -> int:
    data = json.loads((RAW / "ne_110m_countries.geojson").read_text(encoding="utf-8"))

    projected, names, xs, ys = {}, {}, [], []
    for feature in data["features"]:
        code = iso3(feature["properties"])
        if not code or code in SKIP:
            continue
        shapes = []
        for ring in rings(feature["geometry"]):
            pts = [robinson(lon, lat) for lon, lat in ring]
            if len(pts) < 3:
                continue
            shapes.append(pts)
            xs.extend(p[0] for p in pts)
            ys.extend(p[1] for p in pts)
        if shapes:
            projected.setdefault(code, []).extend(shapes)
            names.setdefault(code, feature["properties"].get("NAME") or code)

    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    scale = WIDTH / (x1 - x0)
    height = round((y1 - y0) * scale)

    paths = {}
    for code, shapes in projected.items():
        out = []
        for pts in shapes:
            # y is flipped: projection space counts north as positive, SVG does not
            d = [f"M{(pts[0][0] - x0) * scale:.1f} {(y1 - pts[0][1]) * scale:.1f}"]
            last = None
            for px, py in pts[1:]:
                sx, sy = round((px - x0) * scale, 1), round((y1 - py) * scale, 1)
                if (sx, sy) == last:
                    continue          # 110m data has repeated points once rounded
                d.append(f"L{sx} {sy}")
                last = (sx, sy)
            if len(d) > 3:
                out.append("".join(d) + "Z")
        if out:
            paths[code] = "".join(out)

    OUT.mkdir(parents=True, exist_ok=True)
    blob = json.dumps({"width": WIDTH, "height": height, "paths": paths,
                       "names": {k: v for k, v in names.items() if k in paths}},
                      separators=(",", ":"))
    (OUT / "map.json").write_text(blob, encoding="utf-8")
    (ROOT / "site" / "map.json").write_text(blob, encoding="utf-8")
    print(f"wrote map.json  {len(blob):,} bytes  {len(paths)} countries  "
          f"{WIDTH}x{height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
