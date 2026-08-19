"""Flag hand-coded rows that contradict DPI's own coding of the same party.

Hand-coding mostly covers years past DPI's 2023 end. Where the governing party
has not changed, disagreeing with DPI invents a jump in the series that no
election produced. Russia was the case that prompted this: DPI codes United
Russia as Center through 2023, and a hand-coded "right" for 2024 put a step in
the chart with no change of government behind it.

Run after editing data/seed/hand_coded.csv.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from resolve import load_dpi, norm_party  # noqa: E402

BUCKET = {"-1": "left", "0": "centre", "1": "right"}
# DPI writes this for any executive with no party, so a match on it says nothing
# about continuity: an Italian technocrat in 2020 is not a 1994 government.
GENERIC = {"INDEPENDENT", ""}


def main() -> int:
    cmap = yaml.safe_load((ROOT / "config" / "country_map.yaml").read_text(encoding="utf-8"))
    last = {}
    for rec in load_dpi(cmap):
        if rec["bucket"]:
            last[(rec["entity"], norm_party(rec["party"]))] = (rec["year"], rec["bucket"])

    problems = []
    with open(ROOT / "data" / "seed" / "hand_coded.csv", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            mine = BUCKET.get(row["orientation"])
            key = norm_party(row["dpi_party"])
            if not mine or key in GENERIC:
                continue
            hit = last.get((row["entity"], key))
            if hit and hit[1] != mine:
                problems.append((row["entity"], row["year_from"], row["year_to"],
                                 row["dpi_party"], mine, hit[1], hit[0]))

    for entity, y0, y1, party, mine, theirs, when in problems:
        print(f"{entity} {y0}-{y1}: {party} coded {mine} here, {theirs} by DPI as of {when}")
    print(f"{len(problems)} contradiction(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
