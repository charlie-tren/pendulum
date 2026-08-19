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
# V-Party's last election round. The finer spectrum stops here rather than
# trailing a growing "not rated" band across years it never covered.
SPECTRUM_END = 2019
SPECTRUM_BANDS = [f"f{i}" for i in range(7)] + ["uncovered"]


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


def map_series(records, iso_of):
    """One string per country, one character per year, for the map.

    A dict of 175 countries x 52 years as objects would be most of the payload;
    as run characters it is a few kilobytes.
    """
    code = {"left": "l", "centre": "c", "right": "r",
            "no_reading": "n", "unresolved": "u"}
    years = sorted({r["year"] for r in records})
    grid = defaultdict(dict)
    for rec in records:
        iso = iso_of.get(rec["entity"])
        if iso:
            grid[iso][rec["year"]] = code[rec["bucket"]]
    return {
        "year0": years[0],
        "year1": years[-1],
        "codes": {iso: "".join(row.get(y, "u") for y in years)
                  for iso, row in sorted(grid.items())},
    }


def spectrum(records, pop, members, ordinals):
    """Shares across V-Party's seven-point scale rather than three buckets.

    Read straight from V-Party for every country-year it covers, NOT from the
    resolution chain: in the chain V-Party only fills what DPI leaves blank, so
    taking the score from there would describe a quarter of the world and call
    it the spectrum.
    """
    by_year = defaultdict(list)
    for rec in records:
        if rec["year"] > SPECTRUM_END:
            continue
        if members is not None and rec["entity"] not in members:
            continue
        by_year[rec["year"]].append(rec)

    by_pop, by_country = [], []
    for year in sorted(by_year):
        w = {b: 0.0 for b in SPECTRUM_BANDS}
        c = {b: 0.0 for b in SPECTRUM_BANDS}
        total = 0.0
        for rec in by_year[year]:
            hit = ordinals.get((rec["entity"], year))
            band = f"f{hit['ord']}" if hit else "uncovered"
            c[band] += 1
            p = pop.get((rec["entity"], year))
            if p is None:
                continue
            w[band] += p
            total += p
        n = len(by_year[year])
        if total:
            by_pop.append({"year": year, "pop": round(total),
                           **{b: round(w[b] / total, 5) for b in SPECTRUM_BANDS}})
        if n:
            by_country.append({"year": year, "n": n,
                               **{b: round(c[b] / n, 5) for b in SPECTRUM_BANDS}})
    return {"by_population": by_pop, "by_country": by_country}


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


def source_agreement(cmap, vparty_annual):
    """How often the two main sources agree, where both code the same year.

    Worth measuring rather than assuming: they agree only two times in three,
    and DPI reads the world further left because it barely uses its centre
    bucket. That is a property of the data the site should admit to, not a
    detail to leave in a commit message.
    """
    from resolve import load_dpi
    dpi = {(r["entity"], r["year"]): r["bucket"] for r in load_dpi(cmap) if r["bucket"]}
    pairs = [(dpi[k], vparty_annual[k]["bucket"]) for k in vparty_annual if k in dpi]
    if not pairs:
        return None
    score = {"left": -1, "centre": 0, "right": 1}
    agree = sum(1 for a, b in pairs if a == b)
    return {
        "compared": len(pairs),
        "agree": agree,
        "agree_share": round(agree / len(pairs), 4),
        "mean_dpi": round(sum(score[a] for a, _ in pairs) / len(pairs), 4),
        "mean_vparty": round(sum(score[b] for _, b in pairs) / len(pairs), 4),
    }


def load_continents():
    out = {}
    with open(RAW / "continents.csv", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            out[row["entity"]] = row["owid_region"]
    return out


def seed_entities(records, path, end=END_YEAR):
    """Create empty country-years for states no source in the chain introduces.

    The resolver can only fill a row that exists, and rows come from DPI. A
    country DPI never covered is therefore unreachable however good the later
    sources are: Serbia has a V-Party record and a Wikidata head of government,
    and still rendered as "no data" for every year.
    """
    spec = yaml.safe_load(Path(path).read_text(encoding="utf-8"))["seed"]
    have = {(r["entity"], r["year"]) for r in records}
    for entity, cfg in spec.items():
        stop = int(cfg.get("to", end))
        for year in range(int(cfg["from"]), stop + 1):
            # a country can be missing for only part of the range: Russia has no
            # DPI row before 1992 but plenty after, and seeding a duplicate would
            # count it twice
            if (entity, year) in have:
                continue
            records.append({"entity": entity, "year": year, "bucket": None,
                            "party": "", "party_key": "", "party_stale": True})
    return records


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
    records = seed_entities(records, CFG / "seed_entities.yaml")
    vparty_annual, vparty_ratings = load_vparty(cmap)
    records = resolve(
        records, vparty_annual, vparty_ratings,
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
        agg["spectrum"] = spectrum(records, pop, members, vparty_annual)
        trailing_ma(agg["index"], "mean_by_country")
        trailing_ma(agg["index"], "mean_by_population")
        agg["by_country"] = [{**r, "source": {k: v for k, v in r["source"].items() if v}}
                             for r in agg["by_country"]]
        result[key] = {"label": spec["label"], "note": spec.get("note"),
                       "article": spec.get("article", "the "),
                       "leans_as": spec.get("leans_as", spec["label"]),
                       "n_members": len(members) if members else len(entities), **agg}

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            # YAML parses an unquoted date into a date object, which json cannot
            # serialise, so stringify anything that is not already a string
            "sources": [{k: (v if isinstance(v, str) else str(v)) for k, v in s.items()}
                        for s in yaml.safe_load(
                            (CFG / "sources.yaml").read_text(encoding="utf-8"))["sources"]],
            "coverage": f"1975-{END_YEAR}",
            "agreement": source_agreement(cmap, vparty_annual),
            # the regime series stops before the political one; the slider is
            # capped from this rather than from a number typed into the JS
            "regime_coverage_end": max(y for (_, y) in regimes),
            "note": ("no_reading means nothing places the government on the left-right "
                     "axis: an absolute monarchy, a military government, or a party "
                     "organised around one leader rather than a set of policies. "
                     "unresolved means we lack data. They are different claims and are "
                     "never merged. Each year reports which source resolved it."),
        },
        "palette": yaml.safe_load((CFG / "palette.yaml").read_text(encoding="utf-8")),
        "map": map_series(records, {v: k for k, v in iso_to_entity.items()}),
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
