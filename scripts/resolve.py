"""Resolve a country-year to a left-right bucket, with provenance.

Resolution chain, most authoritative first:

  1. DPI 2023        annual, 1975-2023, but blank for ~25% of world population
  2. V-Party v2      expert survey, election-years forward-filled, ends 2019
  3. carry-forward   V-Party's rating of a party, applied to later years where
                     DPI still records that same party in power
  4. hand_coded      our own coding, from data/seed/hand_coded.csv, each row
                     carrying a written basis and a verification date
  5. wikidata       Wikidata P1387 party alignment joined to dated head-of-
                     government terms. Broadest and most current source, but
                     crowd-maintained, so it ranks below the academic ones and
                     only fills what they leave empty.
  6. no_reading      left-right genuinely does not apply: absolute monarchies,
                     military governments, big-tent personality vehicles. A
                     real answer.
  7. unresolved      we simply lack data. Distinct from no_reading, and the
                     two must not be drawn as one band.

Every resolved point carries the source that produced it so the site can show
its own coverage rather than implying uniform confidence.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

DPI_BUCKET = {"Left": "left", "Center": "centre", "Right": "right"}
# v2pariglef_ord is source-defined 0 (far left) .. 6 (far right); verified
# monotone against the continuous v2pariglef score.
ORD_BUCKET = {0: "left", 1: "left", 2: "left", 3: "centre",
              4: "right", 5: "right", 6: "right"}
VPARTY_END = 2019
HAND_BUCKET = {"-1": "left", "0": "centre", "1": "right", "no_reading": "no_reading"}


def load_hand_coded(path: Path) -> dict:
    """(entity, year) -> {bucket, basis}. Expanded from year ranges."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            bucket = HAND_BUCKET[row["orientation"]]
            for year in range(int(row["year_from"]), int(row["year_to"]) + 1):
                out[(row["entity"], year)] = {"bucket": bucket, "basis": row["basis"]}
    return out


def norm_party(name: str) -> str:
    """PDI-P and PDIP are the same party. Strip everything that isn't a letter
    or digit so the two datasets' naming styles can meet."""
    return re.sub(r"[^A-Za-z0-9]", "", name or "").upper()


def load_dpi(cmap: dict) -> list[dict]:
    """DPI rows, one per country-year.

    Two DPI names can fold onto the same country: it carries Swaziland to 2020
    and eSwatini from 2019, so 2019 and 2020 arrived twice and were counted
    twice in every weighted total. Where that happens, keep the row that
    actually says something.
    """
    rename, drop = cmap["rename"], set(cmap["drop"])
    best: dict[tuple[str, int], dict] = {}
    with open(RAW / "dpi2023.csv", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row["countryname"] in drop:
                continue
            rec = {
                "entity": rename.get(row["countryname"], row["countryname"]),
                "year": int(str(row["year"])[:4]),
                "bucket": DPI_BUCKET.get(row["execrlc"]),
                "party": row["execme"],
                "party_key": norm_party(row["execme"]),
            }
            key = (rec["entity"], rec["year"])
            kept = best.get(key)
            if kept is None or _informative(rec) > _informative(kept):
                best[key] = rec
    return sorted(best.values(), key=lambda r: (r["entity"], r["year"]))


def _informative(rec: dict) -> int:
    """A coded row beats a named one, which beats an empty one."""
    return (2 if rec["bucket"] else 0) + (1 if rec["party_key"] else 0)


def load_aliases(path: Path) -> dict:
    """(entity, normalised DPI party) -> normalised V-Party short name."""
    import yaml
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))["aliases"] or {}
    return {(entity, norm_party(dpi)): norm_party(vp)
            for entity, pairs in raw.items() for dpi, vp in pairs.items()}


def load_vparty(cmap: dict):
    """Returns (annual lookup, party-rating lookup). Requires pyreadr."""
    import pyreadr

    df = pyreadr.read_r(str(RAW / "vparty.RData"))["vparty"]
    rename, drop = cmap["vparty_rename"], set(cmap["vparty_drop"])
    sen = df[(df.v2pagovsup == 0) & df.v2pariglef_ord.notna()]

    annual, ratings = {}, {}
    for country, grp in sen.groupby("country_name"):
        if country in drop:
            continue
        entity = rename.get(country, country)
        obs = [(int(r.year), int(r.v2pariglef_ord), float(r.v2pariglef), r.v2pashname)
               for r in grp.sort_values("year").itertuples()]
        for i, (year, ordv, score, short) in enumerate(obs):
            nxt = obs[i + 1][0] if i + 1 < len(obs) else VPARTY_END
            # year + 1, not year: V-Party is keyed on the ELECTION, and the
            # winner of an election in year Y does not hold office on 1 January
            # of Y - the government it beat does. Starting the new rating in the
            # election year itself put the winner in power up to twelve months
            # early and invented a swing in a year no government changed. Japan
            # 2012 read right off the December election while the DPJ governed
            # all year; Chile 2017 read right off Pinera's December win while
            # Bachelet was still in office. Same bug the Wikidata layer had.
            for y in range(year + 1, min(nxt, VPARTY_END) + 1):
                annual[(entity, y)] = {"bucket": ORD_BUCKET[ordv], "score": score, "ord": ordv}
            ratings[(entity, norm_party(short))] = {
                "bucket": ORD_BUCKET[ordv], "score": score, "ord": ordv, "last_seen": year}
    return annual, ratings


def resolve(records: list[dict], annual: dict, ratings: dict,
            aliases: dict | None = None, hand: dict | None = None,
            wikidata: dict | None = None) -> list[dict]:
    aliases, hand, wikidata = aliases or {}, hand or {}, wikidata or {}

    # The last year DPI codes each country, and what it said. Used to stop the
    # DPI-to-Wikidata handover from inventing a change of position in a
    # government that never changed: Wikidata calls the US Democratic Party
    # "centrism" where DPI calls it Left, so Biden's second term appeared to
    # drift to the centre with no election in between.
    dpi_last: dict[str, tuple[int, str]] = {}
    for rec in records:
        if rec["bucket"]:
            prev = dpi_last.get(rec["entity"])
            if prev is None or rec["year"] > prev[0]:
                dpi_last[rec["entity"]] = (rec["year"], rec["bucket"])
    for rec in records:
        key = (rec["entity"], rec["year"])
        if rec["bucket"]:
            rec["source"] = "dpi"
            rec["score"] = None
        elif key in annual:
            hit = annual[key]
            rec.update(bucket=hit["bucket"], score=hit["score"], source="vparty")
        elif rec["party_key"] and (
                (rec["entity"], aliases.get((rec["entity"], rec["party_key"]),
                                            rec["party_key"])) in ratings):
            key = aliases.get((rec["entity"], rec["party_key"]), rec["party_key"])
            hit = ratings[(rec["entity"], key)]
            if rec["year"] > hit["last_seen"]:
                rec.update(bucket=hit["bucket"], score=hit["score"], source="carry_forward")
            else:
                rec.update(bucket="unresolved", score=None, source="unresolved")
        elif key in hand:
            hit = hand[key]
            rec.update(bucket=hit["bucket"], score=None, basis=hit["basis"],
                       source="no_reading" if hit["bucket"] == "no_reading" else "hand")
        elif key in wikidata:
            hit = wikidata[key]
            bucket, source = hit["bucket"], "wikidata"
            # If the term Wikidata is describing had already begun while DPI was
            # still reporting, then DPI has already judged this same government
            # and its reading wins. Otherwise the handover year shows a swing
            # that no election produced.
            last = dpi_last.get(rec["entity"])
            if last and hit.get("start") is not None and hit["start"] <= last[0]:
                bucket, source = last[1], "dpi_carried"
            # the DPI party name carried into extended years belongs to an
            # earlier government; replace it rather than mislabel this one
            rec.update(bucket=bucket, score=None,
                       party=hit["party"] or rec["party"],
                       source="no_reading" if bucket == "no_reading" else source)
        else:
            rec.update(bucket="unresolved", score=None, source="unresolved")
    return records


def load_wikidata(path: Path, cfg_path: Path, rename: dict) -> dict:
    """(entity, year) -> bucket, from dated head-of-government terms.

    Terms without a start date are skipped — an undated term cannot be placed
    on a timeline, and guessing one would be fabrication.
    """
    import yaml

    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    scale, off_axis = cfg["scale"], set(cfg["not_on_axis"])
    lo = cfg["thresholds"]["left_at_or_below"]
    hi = cfg["thresholds"]["right_at_or_above"]

    terms: dict[tuple[str, str, str, str], dict] = {}
    for row in json.loads(path.read_text(encoding="utf-8")):
        if "start" not in row:
            continue
        entity = rename.get(row["countryLabel"]["value"], row["countryLabel"]["value"])
        party = row.get("partyLabel", {}).get("value", "")
        start = row["start"]["value"][:10]
        end = row["end"]["value"][:10] if "end" in row else "9999-12-31"
        label = row["posLabel"]["value"]
        if label not in scale and label not in off_axis:
            raise ValueError(f"unmapped Wikidata alignment label: {label!r}")
        slot = terms.setdefault((entity, start, end, party), {"labels": [], "party": party})
        slot["labels"].append(label)

    # Assign to years by the project's 1 January convention: a term owns year Y
    # only if it was already in office on 1 January of Y. A government formed in
    # September 2024 therefore counts from 2025, exactly as DPI would have it.
    # Terms are applied in start order so a later one overwrites an earlier one.
    out: dict[tuple[str, int], dict] = {}
    for (entity, start, end, _party), slot in sorted(terms.items(), key=lambda kv: kv[0][1]):
        on = [scale[x] for x in slot["labels"] if x in scale]
        if on:
            mean = sum(on) / len(on)
            bucket = "left" if mean <= lo else ("right" if mean >= hi else "centre")
        else:
            bucket = "no_reading"
        first = int(start[:4]) + (0 if start[5:10] == "01-01" else 1)
        last = int(end[:4]) if end != "9999-12-31" else 2026
        if end != "9999-12-31" and end[5:10] < "01-01":
            last -= 1
        for year in range(max(first, 1975), min(last, 2026) + 1):
            out[(entity, year)] = {"bucket": bucket, "party": slot["party"],
                                   "start": int(start[:4])}
    return out
