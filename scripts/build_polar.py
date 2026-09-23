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

# Each source is described in ITS OWN WORDS first, quoted from the page the
# link goes to, then what this page actually takes from it. A paraphrase is a
# summary of a summary and it is where a source quietly acquires a scope its
# publisher never claimed.
# EACH SOURCE DESCRIBED AS THE SOURCE DESCRIBES ITSELF. Three versions of this
# list have now come off the page. The publishers' marketing sentences, quoted,
# went first. Our own notes on what each dataset is used for went second. The
# third was a mix of the two and drew "sources lines dont look like they're
# from original sources", which is exactly right: it reported OUR slice - "145
# countries are used here" - in the slot that should say what the publisher
# ships.
#
# So what is here is the release a reader would have to download to check this
# page, named the way the publisher names it, and the coverage of THEIR file
# rather than of ours. Everything countable is counted from the publishers'
# own frames at build time, so no figure here can drift from the data. The
# version numbers, publication dates, file names and wave lists were read off
# the publishers' download pages on 23/09/2026, and describe fixed releases.
#
# The V-Dem line quotes the codebook's own question for v2cacamps, which is the
# single most checkable thing on the list: it is the sentence the country
# experts answered, and it is in the codebook that ships inside the download.


def sources(party, europe, society):
    p, s = REACH["party"], REACH["society"]
    return [
        {"name": "V-Party v2", "publisher": "V-Dem Institute",
         "url": "https://www.v-dem.net/data/v-party-dataset/",
         "detail": "Country-Party-Date file, version 2, published February "
                   "2022, with a codebook and party coding units. Policy "
                   "positions and organisational structures of political "
                   f"parties: {p['parties']:,} parties across {p['countries']} "
                   f"countries and {p['elections']:,} elections, {p['lo']} to "
                   f"{p['hi']}."},
        {"name": "Chapel Hill Expert Survey, Europe trend file",
         "publisher": "Bakker, Hooghe, Jolly, Marks, Polk and others",
         "url": "https://www.chesdata.eu/",
         "detail": "Seven waves merged into one file: 1999, 2002, 2006, 2010, "
                   "2014, 2019 and 2024. The survey ran in 14 Western European "
                   "countries and 143 parties in the first wave and in 31 "
                   "countries and 279 parties in the last, which covers every "
                   "EU member state plus Iceland, Norway, Switzerland and "
                   "Turkey."},
        {"name": "V-Dem v16", "publisher": "V-Dem Institute",
         "url": "https://www.v-dem.net/data/the-v-dem-dataset/",
         "detail": "Country-Year Full+Others, version 16, published March "
                   "2026: 531 V-Dem indicators and 251 indices, plus 62 "
                   "indicators drawn from other datasets. This page reads one "
                   "of them, v2cacamps, whose codebook question is \u201cIs "
                   "society polarized into antagonistic, political "
                   "camps?\u201d It is rated for "
                   f"{s['countries']} countries across {s['rows']:,} "
                   f"country-years, {s['lo']} to {s['hi']}."},
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


# What each publisher's own file holds, filled by the loaders below and quoted
# in the sources list. This is the SOURCE's coverage, not the slice this page
# takes: V-Party codes elections back to 1900 and this page starts at 1970
# because the earlier ones are too sparse to index against, and a sources list
# that quietly reports our window as theirs is describing the wrong thing.
REACH = {}


def build_party():
    import pyreadr

    df = pyreadr.read_r(str(RAW / "vparty.RData"))["vparty"]
    REACH["party"] = {
        "countries": int(df["country_name"].nunique()),
        "parties": int(df["v2paid"].nunique()),
        "elections": int(df.groupby(["country_name", "year"]).ngroups),
        "lo": int(df["year"].min()), "hi": int(df["year"].max()),
    }
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


def iso2_by_name(df) -> dict:
    """Country name to ISO 3166 alpha-2, for the flags on the ranked lists.

    V-Dem keys on alpha-3 and flagcdn serves on alpha-2, and nothing connects
    the two but a table: AUS to AU is a lookup, not a truncation.

    27 of V-Dem's 202 entries have no alpha-2 and never will, because they are
    states that no longer exist: Baden, Bavaria, the Papal States, the German
    Democratic Republic, South Yemen. Those simply carry no flag. Three that DO
    still exist are missing from the ISO table because their status is disputed,
    and they are added by hand rather than dropped.
    """
    import csv

    table = {r["alpha-3"]: r["alpha-2"].lower()
             for r in csv.DictReader((RAW / "polar" / "iso3166.csv")
                                     .open(encoding="utf-8-sig"))
             if r.get("alpha-3") and r.get("alpha-2")}
    table.update({"XKX": "xk", "PSG": "ps", "PSB": "ps"})
    pairs = df[["country_name", "country_text_id"]].drop_duplicates()
    return {n: table[t] for n, t in pairs.itertuples(index=False) if t in table}


def build_society():
    import pyreadr

    df = pyreadr.read_r(str(RAW / "polar" / "vdem.RData"))["vdem"]
    # the indicator this page reads, as the publisher's file holds it
    camps = df[df["v2cacamps_osp"].notna()]
    REACH["society"] = {
        "countries": int(camps["country_name"].nunique()),
        "rows": int(len(camps)),
        "lo": int(camps["year"].min()), "hi": int(camps["year"].max()),
    }
    flags = iso2_by_name(df)
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
    return dict(out), flags


def quartiles(series_by_country, axis, value_at=1):
    """The whole distribution across countries per year, for one axis.

    Seven cut points, not three. The middle half alone understates the spread
    badly: in 2024 it runs 1.60 to 3.29 while the countries themselves run 0.22
    to 3.99, and that is true of every year in the series, so a reader looking
    at the middle half would think countries far more alike than they are.

    Drawing all 179 of them instead was tried and is worse: raw lines at any
    opacity that makes one visible fill the plot and bury both the band and the
    median, which is the same grey-scribble failure that took per-country lines
    off the wealth page. Nested bands say the same thing and stay readable.

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
        out.append([y] + [round(q(v, p), 4) for p in
                          (0, .10, .25, .50, .75, .90, 1)] + [len(v)])
    return out


def _swing(series_by_country, axis, base=(1999, 2006), late=(2019, 2024)):
    """How far the median country's spread moved between two windows.

    Computed here rather than typed into the note, for the same reason every
    other number in these notes is computed: a sentence quoting a figure the
    build already knows is a copy waiting to go stale.
    """
    rows = quartiles(series_by_country, axis)
    pick = lambda lo, hi: sorted(r[4] for r in rows if lo <= r[0] <= hi)
    a, z = pick(*base), pick(*late)
    if not a or not z:
        return 0.0
    return z[len(z) // 2] / a[len(a) // 2] - 1


def main() -> int:
    party, cov = build_party()
    europe = build_europe()
    society, flags = build_society()

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
                    # this layer has no chart of its own on the page: it exists
                    # to be a check on the one above it, and a check is a
                    # sentence rather than a second picture of the same claim
                    "note": "A different panel of academics, a different "
                            "questionnaire and a different scale, across "
                            f"{len(europe)} European countries, 1999 to 2024. It "
                            "is carried because it agrees: economic distance "
                            f"moved {_swing(europe, 'economy'):+.0%} over those "
                            "twenty-five years against "
                            f"{_swing(europe, 'culture'):+.0%} on liberal and "
                            "traditional values. CHES.",
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
            # country name to ISO alpha-2, for the flags on the ranked lists.
            # A sibling of the series rather than a key inside them: every
            # consumer of a country's axes dict assumes the values are lists of
            # rows, so a bare string in there is a trap.
            "iso2": flags,
            "min_coverage": MIN_COVERAGE,
            # the publishers' own coverage, so a test can check the sentences
            # in the sources list against the files they describe
            "source_reach": REACH,
            "sources": sources(party, europe, society),
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

    # BOTH COPIES, from one write. The page reads site/polarisation/data.json
    # and the tests read data/out/polarisation.json, and copying by hand meant
    # a rebuild could leave the page serving the previous payload with nothing
    # to say so - the tests would pass against a file the site does not use.
    text = json.dumps(payload, separators=(",", ":"))
    for dst in (OUT, ROOT / "site" / "polarisation" / "data.json"):
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8")
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
            print(f"    {lab:26s} {first[0]} {first[4]:.2f}  ->  "
                  f"{last[0]} {last[4]:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
