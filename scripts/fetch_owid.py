"""Fetch Our World in Data grapher CSVs into data/raw/.

No API key. OWID sits behind Cloudflare, which 1010s a missing User-Agent,
so the header is not optional.
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
BASE = "https://ourworldindata.org/grapher/{slug}.csv"
QUERY = "?v=1&csvType=full&useColumnShortNames=true"
UA = "pendulum/0.1 (charlietrenorden.com; data viz project)"

SLUGS = [
    "political-regime",                          # V-Dem Regimes of the World, to 2025
    "people-living-in-democracies-autocracies",  # population by regime type
    "electoral-democracy-index",
    "population",                                # for our own population weighting
]


def fetch(slug: str) -> Path:
    url = BASE.format(slug=slug) + QUERY
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read()
    out = RAW / f"{slug}.csv"
    out.write_bytes(body)
    return out


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    failed = []
    for slug in SLUGS:
        try:
            path = fetch(slug)
            rows = path.read_text(encoding="utf-8").count("\n")
            print(f"ok    {slug:48s} {rows:>7,} rows  {path.stat().st_size:>9,} bytes")
        except Exception as exc:  # noqa: BLE001 - report, don't mask
            failed.append(slug)
            print(f"FAIL  {slug:48s} {exc}", file=sys.stderr)
    if failed:
        print(f"\n{len(failed)} slug(s) failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
