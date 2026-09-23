"""Fetch the raw inputs for the polarisation page into data/raw/polar/.

Only ONE file is fetched. The other two inputs are already in data/raw/ because
Pendulum's main page uses them: vparty.RData supplies the party positions and
ches_trend.csv the European expert survey. They are checked for, not
re-downloaded.

V-Dem's own download page puts the dataset behind a form. It does not need an
account or a password, and email, gender and the consent tick are all optional
there - only the file format is required - but the V-Dem Institute also
publishes the identical data through its R package on GitHub, ungated. That is
the route taken here, and it is the route the repo ALREADY uses: the
vparty.RData sitting in data/raw/ is byte-for-byte the file in that same
repository. One source, one method, no form.

    python scripts/fetch_polar.py
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = RAW / "polar"

# the V-Dem Institute's own R package, which ships the released dataset
VDEM = "https://github.com/vdeminstitute/vdemdata/raw/master/data/vdem.RData"
# ISO 3166 alpha-3 to alpha-2, so the ranked lists can show a flag. V-Dem keys
# on alpha-3 and flagcdn serves on alpha-2, and there is no rule connecting the
# two: AUS to AU is a lookup, not a truncation.
ISO = ("https://raw.githubusercontent.com/lukes/"
       "ISO-3166-Countries-with-Regional-Codes/master/all/all.csv")

# already here for the main page; named so a missing one is a clear error
LOCAL = {
    "vparty.RData": "party positions and vote shares, V-Party v2",
    "ches_trend.csv": "Chapel Hill Expert Survey trend file, 1999 to 2024",
}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    missing = [n for n in LOCAL if not (RAW / n).exists()]
    if missing:
        print("MISSING, and this script does not fetch them because the main "
              "page owns them:", file=sys.stderr)
        for n in missing:
            print(f"  data/raw/{n}  -  {LOCAL[n]}", file=sys.stderr)
        return 1
    for n, what in LOCAL.items():
        print(f"  have  data/raw/{n:18s} {(RAW / n).stat().st_size:>11,} bytes  {what}")

    for name, url in (("vdem.RData", VDEM), ("iso3166.csv", ISO)):
        dest = OUT / name
        if dest.exists():
            print(f"  have  data/raw/polar/{name}  {dest.stat().st_size:,} bytes")
            continue
        print(f"  fetch {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "pendulum/1.0"})
        with urllib.request.urlopen(req, timeout=300) as r, dest.open("wb") as fh:
            fh.write(r.read())
        print(f"  wrote data/raw/polar/{name}  {dest.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
