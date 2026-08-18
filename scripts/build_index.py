"""Build the orientation series the site reads.

Inputs : data/raw/{dpi2023,population,continents}.csv, vparty.RData,
         wikidata_hog.json, config/*.yaml
Output : data/out/orientation.json

Two weightings are emitted for every country group: one country one vote, and
one person one vote. `no_reading` and `unresolved` are first-class categories
and the shares are never renormalised to exclude them. `no_reading` is an
answer - an absolute monarchy has no left-right position. `unresolved` is an
admission. Merging them would dress up a gap as a finding.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resolve import (load_aliases, load_dpi, load_hand_coded,  # noqa: E402
                     load_vparty, load_wikidata, resolve)

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT, CFG, SEED = (ROOT / "data" / "raw", ROOT / "data" / "out",
                       ROOT / "config", ROOT / "data" / "seed")

CATEGORIES = ["left", "centre", "right", "no_reading", "unresolved"]
SOURCES = ["dpi", "vparty", "carry_forward", "hand", "wikidata",
           "no_reading", "unresolved"]
SCORE = {"left": -1.0, "centre": 0.0, "right": 1.0}
# V-Dem Regimes of the World, via OWID. Codes confirmed against the dataset's
# own metadata rather than assumed - inverting these would invert the chart.
REGIMES = {"0": "closed_autocracy", "1": "electoral_autocracy",
           "2": "electoral_democracy", "3": "liberal_democracy"}
REGIME_ORDER = ["closed_autocracy", "electoral_autocracy",
                "electoral_democracy", "liberal_democracy", "unknown"]
END_YEAR = 2026


def load_population():
    """Historical to 2023, UN WPP medium projection beyond. The projection is
    used only for weighting country-years we already resolve politically, and
    a 2026 population estimate is not a controversial number - but it IS a
    projection, and the site should say so rather than imply a census."""
    pop = {}
    with open(RAW / "pop_proj.csv", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if not row["code"] or row["code"].startswith("OWID"):
                continue
            value = row["population_historical"] or row["population_projection__projected"]
            try:
                pop[(row["entity"], int(row["year"]))] = float(value)
            except ValueError:
                continue
    return pop


def load_regimes():
    """(entity, year) -> regime label. V-Dem RoW runs to 2025; 2026 has none,
    which surfaces as `unknown` rather than being back-filled."""
    out = {}
    with open(RAW / "political-regime.csv", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if not row["code"] or row["code"].startswith("OWID"):
                continue
            label = REGIMES.get(row["regime_row_owid"])
            if label:
                out[(row["entity"], int(row["year"]))] = label
    return out


def country_runs(records, pop, regimes):
    """Per-country timeline, run-length encoded.

    Governments persist for years at a time, so storing runs rather than one
    entry per country-year keeps the payload small enough to ship whole.
    """
    by_entity = defaultdict(list)
    for rec in records:
        by_entity[rec["entity"]].append(rec)

    out = []
    for entity, recs in sorted(by_entity.items()):
        recs.sort(key=lambda r: r["year"])
        runs = []
        for rec in recs:
            # a stale carried-forward name that no later layer confirmed is
            # dropped rather than shown against someone else's government
            party = "" if (rec.get("party_stale") and rec["source"] in
                           ("unresolved", "no_reading")) else (rec["party"] or "")
            key = (rec["bucket"], rec["source"], party,
                   regimes.get((entity, rec["year"]), "unknown"))
            if runs and runs[-1]["k"] == key and runs[-1]["y1"] == rec["year"] - 1:
                runs[-1]["y1"] = rec["year"]
            else:
                runs.append({"k": key, "y0": rec["year"], "y1": rec["year"]})
        latest = max((y for (e, y) in pop if e == entity), default=None)
        out.append({
            "entity": entity,
            "pop": round(pop.get((entity, latest), 0)) if latest else 0,
            "runs": [{"y0": r["y0"], "y1": r["y1"], "b": r["k"][0], "s": r["k"][1],
                      "p": r["k"][2], "r": r["k"][3]} for r in runs],
        })
    return out


def cross_tab(records, pop, members, regimes):
    """Population and country shares across the regime x ideology grid.

    Every cell is a share of the WHOLE group, so the grid sums to 1 and the
    mosaic can be read directly: the cell area is the answer to "how many
    people live under a right-wing electoral autocracy".
    """
    by_year = defaultdict(list)
    for rec in records:
        if members is not None and rec["entity"] not in members:
            continue
        by_year[rec["year"]].append(rec)

    out = []
    for year in sorted(by_year):
        recs = by_year[year]
        cells = {r: {b: 0.0 for b in CATEGORIES} for r in REGIME_ORDER}
        ncells = {r: {b: 0 for b in CATEGORIES} for r in REGIME_ORDER}
        total = 0.0
        for rec in recs:
            regime = regimes.get((rec["entity"], year), "unknown")
            ncells[regime][rec["bucket"]] += 1
            p = pop.get((rec["entity"], year))
            if p is None:
                continue
            cells[regime][rec["bucket"]] += p
            total += p
        if not total:
            continue
        out.append({
            "year": year,
            "pop": round(total),
            "cells": {r: {b: round(v / total, 5) for b, v in row.items() if v}
                      for r, row in cells.items() if any(row.values())},
            "counts": {r: {b: v for b, v in row.items() if v}
                       for r, row in ncells.items() if any(row.values())},
        })
    return out


def load_continents():
    out = {}
    with open(RAW / "continents.csv", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            out[row["entity"]] = row["owid_region"]
    return out


def extend_years(records, end=END_YEAR):
    """DPI stops at 2023. Create empty country-years past it so the later
    layers (hand-coding, Wikidata) have somewhere to land."""
    last = max(r["year"] for r in records)
    entities = {r["entity"] for r in records if r["year"] == last}
    parties = {r["entity"]: r["party"] for r in records if r["year"] == last}
    for year in range(last + 1, end + 1):
        for entity in entities:
            # party_key stays empty so carry-forward cannot fire on a name that
            # DPI never actually recorded for this year. `party` is kept only so
            # a later layer can fall back to it, and any layer that resolves the
            # year is expected to overwrite it with its own.
            records.append({"entity": entity, "year": year, "bucket": None,
                            "party": parties.get(entity, ""), "party_key": "",
                            "party_stale": True})
    return records


def aggregate(records, pop, members):
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
        src = {k: 0.0 for k in SOURCES}
        for rec in recs:
            c[rec["bucket"]] += 1
            src[rec["source"]] += 1
            p = pop.get((rec["entity"], year))
            if p is not None:
                w[rec["bucket"]] += p
        n, total = len(recs), sum(w.values())
        counts.append({"year": year, "n": n,
                       "source": {k: round(src[k] / n, 4) for k in SOURCES},
                       **{k: round(c[k] / n, 4) for k in CATEGORIES}})
        weights.append({"year": year, "pop": round(total),
                        **{k: round(w[k] / total, 4) if total else None
                           for k in CATEGORIES}})
        cn = n - c["no_reading"] - c["unresolved"]
        cp = total - w["no_reading"] - w["unresolved"]
        index.append({
            "year": year,
            "coded_share_countries": round(cn / n, 4) if n else None,
            "coded_share_pop": round(cp / total, 4) if total else None,
            "mean_by_country": round(sum(SCORE[k] * c[k] for k in SCORE) / cn, 4) if cn else None,
            "mean_by_population": round(sum(SCORE[k] * w[k] for k in SCORE) / cp, 4) if cp else None,
        })
    return {"by_country": counts, "by_population": weights, "index": index}


def trailing_ma(series, key, window=3):
    """Trailing, never centred. A centred mean would peek at t+1."""
    vals = [row[key] for row in series]
    for i, row in enumerate(series):
        chunk = [v for v in vals[max(0, i - window + 1): i + 1] if v is not None]
        row[f"{key}_ma{window}"] = (round(sum(chunk) / len(chunk), 4)
                                    if i >= window - 1 and len(chunk) == window else None)


def resolve_members(spec, iso_to_entity, continents, pop, entities):
    kind = spec["members"]
    if kind == "ALL":
        return None
    if kind == "CONTINENT":
        return {e for e in entities if continents.get(e) == spec["continent"]}
    if kind == "TOP20_POP":
        latest = max(y for (_, y) in pop)
        ranked = sorted(((pop.get((e, latest), 0), e) for e in entities), reverse=True)
        return {e for _, e in ranked[:20]}
    return {iso_to_entity[c] for c in kind if c in iso_to_entity}


def main() -> int:
    cmap = yaml.safe_load((CFG / "country_map.yaml").read_text(encoding="utf-8"))
    groups = yaml.safe_load((CFG / "country_groups.yaml").read_text(encoding="utf-8"))["groups"]
    pop, continents, regimes = load_population(), load_continents(), load_regimes()

    records = extend_years(load_dpi(cmap))
    records = resolve(
        records, *load_vparty(cmap),
        aliases=load_aliases(CFG / "party_aliases.yaml"),
        hand=load_hand_coded(SEED / "hand_coded.csv"),
        wikidata=load_wikidata(RAW / "wikidata_hog.json",
                               CFG / "wikidata_positions.yaml", cmap["vparty_rename"]),
    )
    entities = {r["entity"] for r in records}

    iso_to_entity = {}
    with open(RAW / "population.csv", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row["code"] and not row["code"].startswith("OWID"):
                iso_to_entity.setdefault(row["code"], row["entity"])

    result = {}
    for key, spec in groups.items():
        members = resolve_members(spec, iso_to_entity, continents, pop, entities)
        agg = aggregate(records, pop, members)
        agg["cross"] = cross_tab(records, pop, members, regimes)
        trailing_ma(agg["index"], "mean_by_country")
        trailing_ma(agg["index"], "mean_by_population")
        agg["by_country"] = [{**r, "source": {k: v for k, v in r["source"].items() if v}}
                             for r in agg["by_country"]]
        result[key] = {"label": spec["label"], "note": spec.get("note"),
                       "n_members": len(members) if members else len(entities), **agg}

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            "sources": [
                "Database of Political Institutions 2023 (IDB), CC-BY 4.0, 1975-2023",
                "V-Party v2 (V-Dem Institute, 2022), party positions to ~2019",
                "Wikidata P1387 party alignment joined to dated head-of-government terms",
                "Hand-coded rows in data/seed/hand_coded.csv, each with a written basis",
                "Political regime: V-Dem Regimes of the World via Our World in Data, "
                "1789-2025",
                "Population: Our World in Data / UN WPP - historical to 2023, medium-variant projection for 2024-2026",
            ],
            "coverage": f"1975-{END_YEAR}",
            # the regime series stops before the political one; the slider is
            # capped from this rather than from a number typed into the JS
            "regime_coverage_end": max(y for (_, y) in regimes),
            "note": ("no_reading means left-right genuinely does not apply - an absolute "
                     "monarchy, a military government, a big-tent personality vehicle. "
                     "unresolved means we lack data. They are different claims and are "
                     "never merged. Each year reports which source resolved it."),
        },
        "palette": yaml.safe_load((CFG / "palette.yaml").read_text(encoding="utf-8")),
        "countries": country_runs(records, pop, regimes),
        "members": {k: sorted(resolve_members(spec, iso_to_entity, continents, pop, entities)
                              or entities)
                    for k, spec in groups.items()},
        "groups": result,
    }
    blob = json.dumps(payload, separators=(",", ":"))
    (OUT / "orientation.json").write_text(blob, encoding="utf-8")
    # the site is served as static files; give it its own copy rather than
    # making the page reach up out of its directory
    (ROOT / "site" / "orientation.json").write_text(blob, encoding="utf-8")
    print(f"wrote data/out/orientation.json  "
          f"{(OUT / 'orientation.json').stat().st_size:,} bytes  {len(result)} groups")
    for key in ("world", "g20", "africa", "asia", "europe"):
        idx = result[key]["index"]
        for year in (2023, END_YEAR):
            row = next((r for r in idx if r["year"] == year), None)
            if row and row["coded_share_pop"]:
                print(f"  {key:8s} {year}  coded {row['coded_share_pop']:.0%} of pop  "
                      f"mean {row['mean_by_population']:+.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
