"""Resolve a country-year to a left-right bucket, with provenance.

Resolution chain, most authoritative first:

  1. DPI 2023        annual, 1975-2023, but blank for ~25% of world population
  2. V-Party v2      expert survey, election-years forward-filled, ends 2019
  3. carry-forward   V-Party's rating of a party, applied to later years where
                     DPI still records that same party in power
  4. uncoded         genuinely no left-right reading (absolute monarchies,
                     non-party states). A real answer, not a hole.

Every resolved point carries the source that produced it so the site can show
its own coverage rather than implying uniform confidence.
"""
from __future__ import annotations

import csv
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


def norm_party(name: str) -> str:
    """PDI-P and PDIP are the same party. Strip everything that isn't a letter
    or digit so the two datasets' naming styles can meet."""
    return re.sub(r"[^A-Za-z0-9]", "", name or "").upper()


def load_dpi(cmap: dict) -> list[dict]:
    rename, drop = cmap["rename"], set(cmap["drop"])
    out = []
    with open(RAW / "dpi2023.csv", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row["countryname"] in drop:
                continue
            out.append({
                "entity": rename.get(row["countryname"], row["countryname"]),
                "year": int(str(row["year"])[:4]),
                "bucket": DPI_BUCKET.get(row["execrlc"]),
                "party": row["execme"],
                "party_key": norm_party(row["execme"]),
            })
    return out


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
            for y in range(year, min(nxt, VPARTY_END) + 1):
                annual[(entity, y)] = {"bucket": ORD_BUCKET[ordv], "score": score, "ord": ordv}
            ratings[(entity, norm_party(short))] = {
                "bucket": ORD_BUCKET[ordv], "score": score, "ord": ordv, "last_seen": year}
    return annual, ratings


def resolve(records: list[dict], annual: dict, ratings: dict) -> list[dict]:
    for rec in records:
        key = (rec["entity"], rec["year"])
        if rec["bucket"]:
            rec["source"] = "dpi"
            rec["score"] = None
        elif key in annual:
            hit = annual[key]
            rec.update(bucket=hit["bucket"], score=hit["score"], source="vparty")
        elif (rec["entity"], rec["party_key"]) in ratings and rec["party_key"]:
            hit = ratings[(rec["entity"], rec["party_key"])]
            if rec["year"] > hit["last_seen"]:
                rec.update(bucket=hit["bucket"], score=hit["score"], source="carry_forward")
            else:
                rec.update(bucket="uncoded", score=None, source="none")
        else:
            rec.update(bucket="uncoded", score=None, source="none")
    return records
