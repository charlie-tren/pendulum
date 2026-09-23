"""Build data/out/polarisation.json from V-Party, CHES and V-Dem.

THREE LAYERS, NEVER MERGED, because they answer three different questions.

  party    how far apart the PARTIES stand, per election, per axis. V-Party,
           1970-2019, and the axes are the point: the economic one is flat and
           the cultural ones roughly double.
  europe   the same question asked of a different expert panel on a different
           scale. CHES, 1999-2024, 28 European countries. It is the
           independent check, and it is what carries the story past 2019.
  society  whether the VOTERS are in antagonistic camps, which is not the same
           question at all. V-Dem v2cacamps, expert coded, 1900-2025.

The first two are a spread across parties weighted by votes. The third is a
single expert rating of a whole society. A chart that averaged them together
would be meaningless, so nothing here does.

TWO FAULTS INHERITED from the populism work that was scoped and declined in
September, both of which any V-Party aggregate walks into:

  - A THRESHOLD makes a two-party country a step function. Counting the vote
    for parties above some score gave the USA 0% until one party crossed the
    line and it jumped to 46% in a single election. Everything here is a
    vote-weighted moment instead, so a party moving 0.49 to 0.51 moves the
    number by what it is worth.
  - COALITION ROWS LOSE THEIR VOTE. Hungary's Fidesz has a score but its vote
    sits on a joint `Fidesz-KDNP` row whose score is NaN. Silently dropping
    those parties would score the election on whoever is left, so an election
    is only kept when the coded parties hold at least MIN_COVERAGE of the vote
    cast, and the coverage that survived is carried in the payload.

    python scripts/fetch_polar.py && python scripts/build_polar.py
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "out" / "polarisation.json"

# an election is scored only if the parties carrying a coding hold this much of
# the vote. 0.70 keeps 1,163 of the 1,201 elections that have any coding at all
MIN_COVERAGE = 0.70
MIN_PARTIES = 2

# V-Party's axes. `flip` is nothing to do with polarisation, it is only which
# end of the scale reads as "more", and it is unused by the spread, which is
# sign-blind. Kept so the level series is readable.
PARTY_AXES = [
    ("economy", "v2pariglef", "Economic left and right",
     "Where the party stands on state intervention in the economy."),
    ("immigration", "v2paimmig", "Immigration",
     "How restrictive the party is on immigration."),
    ("lgbt", "v2palgbt", "LGBT rights",
     "Whether the party supports equal rights for LGBT people."),
    ("minorities", "v2paminor", "Minority rights",
     "Whether the party supports the rights of minorities."),
    ("religion", "v2parelig", "Religious principles",
     "How far the party wants religious principles in public policy."),
    ("pluralism", "v2paplur", "Political pluralism",
     "Whether the party accepts that opponents are legitimate."),
    ("violence", "v2paviol", "Political violence",
     "Whether the party encourages, or refuses to condemn, political violence "
     "by its own supporters."),
    ("populism", "v2xpa_popul", "Populism",
     "How far the party runs on a pure people against a corrupt elite."),
    ("antiplural", "v2xpa_antiplural", "Anti-pluralism",
     "How far the party rejects the rules that let it be voted out."),
]

CHES_AXES = [
    ("economy", "lrecon", "Economic left and right"),
    ("culture", "galtan", "Liberal and traditional values"),
    ("immigration", "immigrate_policy", "Immigration"),
    ("eu", "eu_position", "European integration"),
    ("general", "lrgen", "General left and right"),
]

SOCIETY_AXES = [
    ("camps", "v2cacamps_osp", "Society in antagonistic camps",
     "V-Dem asks its country experts whether supporters of opposing political "
     "camps interact only within their own group. 0 is none, 4 is a society "
     "split in two."),
    ("violence", "v2caviol_osp", "Political violence by citizens",
     "Whether ordinary citizens use violence to pursue political goals."),
]

SOURCES = [
    {"name": "V-Party v2", "publisher": "V-Dem Institute",
     "url": "https://www.v-dem.net/data/v-party-dataset/",
     "role": "Party positions and vote shares, 1970 to 2019. The spread across "
             "parties at each election is computed here, not published there."},
    {"name": "Chapel Hill Expert Survey, trend file",
     "publisher": "Polk, Jolly, Bakker and others",
     "url": "https://www.chesdata.eu/",
     "role": "A second expert panel on 28 European countries, 1999 to 2024. "
             "Different questions and a different scale, so it is a check on "
             "the first layer rather than more of it."},
    {"name": "V-Dem v16", "publisher": "V-Dem Institute",
     "url": "https://www.v-dem.net/data/the-v-dem-dataset/",
     "role": "Whether society itself is split into antagonistic camps, expert "
             "coded, 1900 to 2025. The only layer that reaches past 2019."},
]


def spread(pairs):
    """Vote-weighted standard deviation of a set of party positions.

    The Dalton index, without his division by the scale's half-width: the scales
    here differ between sources, so the number is only ever compared with itself.
    """
    tot = sum(w for _, w in pairs)
    if tot <= 0:
        return None, None
    mu = sum(x * w for x, w in pairs) / tot
    var = sum(w * (x - mu) ** 2 for x, w in pairs) / tot
    return math.sqrt(max(0.0, var)), mu


def num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f


def build_party():
    import pyreadr

    df = pyreadr.read_r(str(RAW / "vparty.RData"))["vparty"]
    cols = ["country_name", "year", "v2pavote"] + [c for _, c, _, _ in PARTY_AXES]
    d = df[cols]

    out = defaultdict(dict)       # country -> axis -> [[year, spread, mean, n]]
    cov_kept, cov_dropped = 0, 0
    for (country, year), g in d.groupby(["country_name", "year"]):
        cast = g["v2pavote"].sum(skipna=True)
        if not cast or cast <= 0:
            continue
        for key, col, _, _ in PARTY_AXES:
            ok = [(num(r), num(w)) for r, w in zip(g[col], g["v2pavote"])]
            ok = [(x, w) for x, w in ok if x is not None and w is not None and w > 0]
            if len(ok) < MIN_PARTIES:
                continue
            coverage = sum(w for _, w in ok) / cast
            if coverage < MIN_COVERAGE:
                if key == "economy":
                    cov_dropped += 1
                continue
            if key == "economy":
                cov_kept += 1
            sd, mu = spread(ok)
            out[country].setdefault(key, []).append(
                [int(year), round(sd, 4), round(mu, 4), len(ok)])

    for c in out:
        for k in out[c]:
            out[c][k].sort()
    return dict(out), {"kept": cov_kept, "dropped_low_coverage": cov_dropped}


def build_europe():
    import csv

    rows = list((RAW / "ches_trend.csv").open(encoding="utf-8-sig"))
    rd = list(csv.DictReader(rows))
    out = defaultdict(dict)
    for key, col, _ in CHES_AXES:
        by = defaultdict(list)
        for r in rd:
            x, w = num(r.get(col)), num(r.get("vote"))
            y = num(r.get("year"))
            if x is None or w is None or y is None or w <= 0:
                continue
            by[(r["country"], int(y))].append((x, w))
        for (country, year), obs in by.items():
            # CHES vote shares are percentages of the vote cast; the same
            # coverage floor applies, and a wave that polls under it is dropped
            if len(obs) < MIN_PARTIES or sum(w for _, w in obs) < MIN_COVERAGE * 100:
                continue
            sd, mu = spread(obs)
            out[country].setdefault(key, []).append(
                [year, round(sd, 4), round(mu, 4), len(obs)])
    for c in out:
        for k in out[c]:
            out[c][k].sort()
    return dict(out)


def build_society():
    import pyreadr

    df = pyreadr.read_r(str(RAW / "polar" / "vdem.RData"))["vdem"]
    cols = ["country_name", "year"] + [c for _, c, _, _ in SOCIETY_AXES]
    d = df[cols]
    d = d[d["year"] >= 1900]

    out = defaultdict(dict)
    for r in d.itertuples(index=False):
        for key, col, _, _ in SOCIETY_AXES:
            v = num(getattr(r, col))
            if v is None:
                continue
            out[r.country_name].setdefault(key, []).append([int(r.year), round(v, 3)])
    for c in out:
        for k in out[c]:
            out[c][k].sort()
    return dict(out)


def quartiles(series_by_country, axis, value_at=1):
    """p25/p50/p75 across countries per year, for one axis.

    A quartile over three countries is noise, so a year needs four.
    """
    by_year = defaultdict(list)
    for c, axes in series_by_country.items():
        for row in axes.get(axis, []):
            by_year[row[0]].append(row[value_at])

    def q(v, p):
        i = (len(v) - 1) * p
        lo, hi = int(i), min(int(i) + 1, len(v) - 1)
        return v[lo] + (v[hi] - v[lo]) * (i - lo)

    out = []
    for y in sorted(by_year):
        v = sorted(by_year[y])
        if len(v) < 4:
            continue
        out.append([y, round(q(v, .25), 4), round(q(v, .5), 4),
                    round(q(v, .75), 4), len(v)])
    return out


def main() -> int:
    party, cov = build_party()
    europe = build_europe()
    society = build_society()

    payload = {
        "meta": {
            "layers": {
                "party": {
                    "label": "Party positions",
                    "note": "How far apart the parties stood at each election, "
                            "weighted by the votes they got. V-Party, "
                            f"{len(party)} countries.",
                    "axes": [{"key": k, "label": lab, "note": n}
                             for k, _, lab, n in PARTY_AXES],
                },
                "europe": {
                    "label": "European expert survey",
                    "note": "The same measure from a second expert panel, on a "
                            f"different scale. CHES, {len(europe)} countries.",
                    "axes": [{"key": k, "label": lab} for k, _, lab in CHES_AXES],
                },
                "society": {
                    "label": "Society",
                    "note": "Not a spread across parties: one expert rating of "
                            "whether the public itself is split into camps. "
                            f"V-Dem, {len(society)} countries.",
                    "axes": [{"key": k, "label": lab, "note": n}
                             for k, _, lab, n in SOCIETY_AXES],
                },
            },
            "coverage": cov,
            "min_coverage": MIN_COVERAGE,
            "sources": SOURCES,
        },
        "party": party,
        "europe": europe,
        "society": society,
        "bands": {
            "party": {k: quartiles(party, k) for k, _, _, _ in PARTY_AXES},
            "europe": {k: quartiles(europe, k) for k, _, _ in CHES_AXES},
            "society": {k: quartiles(society, k) for k, _, _, _ in SOCIETY_AXES},
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  {OUT.stat().st_size:,} bytes")
    print(f"  party   {len(party):4d} countries, "
          f"{cov['kept']} elections kept, {cov['dropped_low_coverage']} "
          f"dropped under {MIN_COVERAGE:.0%} vote coverage")
    print(f"  europe  {len(europe):4d} countries")
    print(f"  society {len(society):4d} countries")
    for k, _, lab, _ in PARTY_AXES:
        b = payload["bands"]["party"][k]
        if len(b) > 8:
            first, last = b[0], b[-1]
            print(f"    {lab:26s} {first[0]} {first[2]:.2f}  ->  "
                  f"{last[0]} {last[2]:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
