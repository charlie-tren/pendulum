"""Build the orientation series the site reads.

Inputs : data/raw/dpi2023.csv, data/raw/population.csv, config/*.yaml
Output : data/out/orientation.json

Two weightings are emitted for every country group: one country one vote,
and one person one vote. `uncoded` is a first-class category in both. It is
never dropped and the shares are never renormalised to exclude it — about a
quarter of the world's population has no left-right code in DPI, and that
absence is concentrated in the Global South. Hiding it would turn a
Western-weighted sample into a claim about "the world".
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT, CFG = ROOT / "data" / "raw", ROOT / "data" / "out", ROOT / "config"

BUCKET = {"Left": "left", "Center": "centre", "Right": "right"}
CATEGORIES = ["left", "centre", "right", "uncoded"]
SCORE = {"left": -1.0, "centre": 0.0, "right": 1.0}


def year_of(raw: str) -> int:
    return int(str(raw)[:4])


def load_population() -> dict[tuple[str, int], float]:
    pop: dict[tuple[str, int], float] = {}
    with open(RAW / "population.csv", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if not row["code"] or row["code"].startswith("OWID"):
                continue
            try:
                pop[(row["entity"], int(row["year"]))] = float(row["population_historical"])
            except ValueError:
                continue
    return pop


def load_dpi(cmap: dict) -> list[dict]:
    rename, drop = cmap["rename"], set(cmap["drop"])
    out = []
    with open(RAW / "dpi2023.csv", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            name = row["countryname"]
            if name in drop:
                continue
            out.append({
                "entity": rename.get(name, name),
                "year": year_of(row["year"]),
                "bucket": BUCKET.get(row["execrlc"], "uncoded"),
                "party": row["execme"],
            })
    return out


def aggregate(records, pop, members) -> dict:
    """Shares by year for one country group, under both weightings."""
    by_year = defaultdict(list)
    for rec in records:
        if members is not None and rec["entity"] not in members:
            continue
        by_year[rec["year"]].append(rec)

    counts, weights, index = [], [], []
    for year in sorted(by_year):
        recs = by_year[year]
        c = {k: 0.0 for k in CATEGORIES}
        w = {k: 0.0 for k in CATEGORIES}
        missing_pop = 0
        for rec in recs:
            c[rec["bucket"]] += 1
            p = pop.get((rec["entity"], year))
            if p is None:
                missing_pop += 1
                continue
            w[rec["bucket"]] += p
        n, total_pop = len(recs), sum(w.values())
        counts.append({"year": year, "n": n, "missing_pop": missing_pop,
                       **{k: round(c[k] / n, 6) for k in CATEGORIES}})
        weights.append({"year": year, "pop": round(total_pop),
                        **{k: round(w[k] / total_pop, 6) if total_pop else None
                           for k in CATEGORIES}})
        # mean orientation across CODED countries only, both weightings
        coded_n = n - c["uncoded"]
        coded_p = total_pop - w["uncoded"]
        index.append({
            "year": year,
            "coded_share_countries": round(coded_n / n, 6) if n else None,
            "coded_share_pop": round(coded_p / total_pop, 6) if total_pop else None,
            "mean_by_country": round(sum(SCORE[k] * c[k] for k in SCORE) / coded_n, 6)
                               if coded_n else None,
            "mean_by_population": round(sum(SCORE[k] * w[k] for k in SCORE) / coded_p, 6)
                                  if coded_p else None,
        })
    return {"by_country": counts, "by_population": weights, "index": index}


def trailing_ma(series: list[dict], key: str, window: int = 3) -> None:
    """Add a TRAILING moving average in place. Never centred — no peeking at t+1."""
    vals = [row[key] for row in series]
    for i, row in enumerate(series):
        chunk = [v for v in vals[max(0, i - window + 1): i + 1] if v is not None]
        row[f"{key}_ma{window}"] = (round(sum(chunk) / len(chunk), 6)
                                    if i >= window - 1 and len(chunk) == window else None)


def main() -> int:
    cmap = yaml.safe_load((CFG / "country_map.yaml").read_text(encoding="utf-8"))
    groups = yaml.safe_load((CFG / "country_groups.yaml").read_text(encoding="utf-8"))["groups"]
    pop = load_population()
    records = load_dpi(cmap)

    iso_to_entity = {}
    for row in csv.DictReader(open(RAW / "population.csv", encoding="utf-8-sig")):
        if row["code"] and not row["code"].startswith("OWID"):
            iso_to_entity.setdefault(row["code"], row["entity"])

    result, unresolved = {}, {}
    for key, spec in groups.items():
        if spec["members"] == "ALL":
            members = None
        else:
            members = {iso_to_entity[c] for c in spec["members"] if c in iso_to_entity}
            missing = [c for c in spec["members"] if c not in iso_to_entity]
            if missing:
                unresolved[key] = missing
        agg = aggregate(records, pop, members)
        trailing_ma(agg["index"], "mean_by_country")
        trailing_ma(agg["index"], "mean_by_population")
        result[key] = {"label": spec["label"], **agg}

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            "source": "Database of Political Institutions 2023 (IDB), CC-BY 4.0",
            "source_url": "https://doi.org/10.60966/8tx1xs4i",
            "population": "Our World in Data / UN WPP",
            "coverage": "1975-2023",
            "built": "2026-08-18",
            "note": ("`uncoded` means DPI records no left-right orientation for that "
                     "executive. It is a real category, not missing data to be hidden."),
        },
        "groups": result,
    }
    (OUT / "orientation.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")

    if unresolved:
        print("WARNING unresolved ISO codes:", unresolved)
    size = (OUT / "orientation.json").stat().st_size
    print(f"wrote data/out/orientation.json  {size:,} bytes  {len(result)} groups")
    for key in result:
        idx = result[key]["index"][-1]
        print(f"  {key:8s} 2023  coded {idx['coded_share_pop']:.0%} of pop  "
              f"mean(by pop) {idx['mean_by_population']:+.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
