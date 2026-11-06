"""Fetch the raw inputs no other script fetches, into data/raw/.

    python scripts/fetch_raw.py            # all three
    python scripts/fetch_raw.py wikidata   # one

continents.csv            OWID's continent per country (build_index.load_continents)
ne_110m_countries.geojson Natural Earth 1:110m admin-0, public domain (build_map)
wikidata_hog.json         heads of government with their party's alignment (resolve.load_wikidata)

dpi2023.csv is NOT here: the IDB answers scripted requests with 403. Download DPI2023
by hand from the page in docs/data-sources.md and save it as data/raw/dpi2023.csv.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
UA = "pendulum/0.1 (charlietrenorden.com; data viz project)"

CONTINENTS = ("https://ourworldindata.org/grapher/continents-according-to-our-world-in-data.csv"
              "?v=1&csvType=full&useColumnShortNames=true")
NATURAL_EARTH = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/"
                 "geojson/ne_110m_admin_0_countries.geojson")

# The party membership statement's own dates must overlap the term, or a head of
# government is joined to every party they ever belonged to (Macron came back as
# Renaissance, the Socialist Party and En Marche at once). docs/data-sources.md.
QUERY = """
SELECT DISTINCT ?countryLabel ?partyLabel ?start ?end ?posLabel WHERE {
  ?country wdt:P31 wd:Q3624078 ;
           p:P6 ?term .
  ?term ps:P6 ?hog ;
        pq:P580 ?start .
  OPTIONAL { ?term pq:P582 ?end . }
  FILTER(!BOUND(?end) || ?end >= "2015-01-01T00:00:00Z"^^xsd:dateTime)
  ?hog p:P102 ?member .
  ?member ps:P102 ?party .
  OPTIONAL { ?member pq:P580 ?mStart . }
  OPTIONAL { ?member pq:P582 ?mEnd . }
  FILTER(!BOUND(?mStart) || !BOUND(?end) || ?mStart <= ?end)
  FILTER(!BOUND(?mEnd) || ?mEnd >= ?start)
  ?party wdt:P1387 ?pos .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
"""


def get(url: str, accept: str = "*/*") -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def continents() -> Path:
    out = RAW / "continents.csv"
    body = get(CONTINENTS).decode("utf-8-sig")
    # OWID names the region column after the indicator; the loader reads owid_region.
    head, _, rest = body.partition("\n")
    cols = head.split(",")
    cols[-1] = "owid_region"
    out.write_text(",".join(c.strip() for c in cols) + "\n" + rest, encoding="utf-8")
    return out


def natural_earth() -> Path:
    out = RAW / "ne_110m_countries.geojson"
    out.write_bytes(get(NATURAL_EARTH))
    return out


def wikidata() -> Path:
    out = RAW / "wikidata_hog.json"
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": QUERY, "format": "json"})
    rows = json.loads(get(url, "application/sparql-results+json"))["results"]["bindings"]
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=0), encoding="utf-8")
    return out


JOBS = {"continents": continents, "natural_earth": natural_earth, "wikidata": wikidata}


def main(argv: list[str]) -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    failed = []
    for name in argv or JOBS:
        try:
            path = JOBS[name]()
            print(f"  ok  {path.name}  {path.stat().st_size:,} bytes")
        except Exception as exc:  # noqa: BLE001 - report and carry on
            print(f"  !!  {name}: {type(exc).__name__}: {exc}"[:160])
            failed.append(name)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
