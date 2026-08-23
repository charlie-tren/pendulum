"""Build data/out/wealth.json from the four wealth-inequality layers.

Stdlib only. `scripts/fetch_wealth.py` has already turned the spreadsheets into
CSV, so nothing here needs openpyxl.

The layers are NOT merged. Each observation carries the layer it came from and
what it actually measured, because they do not share a unit or a population:

  deep           a wealth Gini computed from house floor areas at one dig site
  preindustrial  taxable wealth in one town or county, from tax records
  industrial     estimated household wealth for a whole country, per decade
  modern         national accounts and tax data, annual

Two things happen to be comparable enough to plot on one axis, and only two:
the Gini, and the share held by the richest tenth. Everything else stays in the
readout. The site says which layer a reader is looking at at all times.

    python scripts/build_wealth.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "wealth"
OUT = ROOT / "data" / "out" / "wealth.json"


def num(v: str | None):
    """Float, or None. The Alfani sheets use blanks and the odd stray marker."""
    if v is None:
        return None
    v = str(v).strip().replace("%", "")
    if not v or v in {"-", "n.a.", "na", "NA"}:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def rows(name: str) -> list[dict]:
    path = RAW / name
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------- preindustrial

def places() -> list[dict]:
    """One dot per town or county per tax assessment.

    England is the lay subsidies, so its unit is the taxpaying household in one
    county. Piedmont is the estimi, the property-tax registers of single towns.
    Both give a Gini and a full decile breakdown, which is why the richest-tenth
    line can start in 1283 rather than 1820.
    """
    out = []
    for r in rows("alfani_england_counties.csv"):
        # every county is given twice, as observed and as reconstructed. The
        # reconstructed figure adds back the households too poor to be taxed,
        # so it is the honest one for a wealth share and it is much higher.
        if (r.get("Observed/Reconstructed") or "").strip().lower() != "reconstructed":
            continue
        year, gini = num(r.get("Year")), num(r.get("Gini index"))
        if year is None or gini is None:
            continue
        out.append({
            "place": r["County"], "group": "England", "layer": "preindustrial",
            "rollup": False,
            "year": int(year), "gini": gini,
            "top10": num(r.get("D10")), "top1": num(r.get("Top1")),
            "n": num(r.get("N. Households")),
            "basis": "lay subsidy, reconstructed to include untaxed households",
        })
    for r in rows("alfani_piedmont_places.csv"):
        year, gini = num(r.get("Year (reference)")), num(r.get("Gini index"))
        if year is None or gini is None:
            continue
        place = (r.get("") or r.get("Place") or "").strip()
        # The file mixes single towns with three roll-ups of them: "Piedmont
        # (overall)", "(cities only)" and "(rural areas only)". Plotting those
        # as dots alongside their own components double-counts the same tax
        # registers and makes the cloud look denser than the evidence is. They
        # are kept, marked, so the page can draw the roll-up as a line through
        # the towns rather than as one more town.
        rollup = place.startswith("Piedmont (")
        out.append({
            "place": place,
            "group": "Piedmont", "layer": "preindustrial", "rollup": rollup,
            "year": int(year), "gini": gini,
            "top10": num(r.get("D10")), "top1": num(r.get("Top1%")),
            "n": num(r.get("N.Cases (households)")),
            "basis": "estimo, the town property-tax register",
        })
    return [p for p in out if p["place"]]


REGION_COLS = {
    "NorthernLC(Gini)": ("holland", "Holland"),
    "SouthernLC(Gini)": ("flanders", "Flanders and Brabant"),
    "Tuscany(FlorentineState)(Gini)": ("tuscany", "Tuscany"),
    "Piedmont(SabaudianState)(Gini)": ("piedmont", "Piedmont"),
}


def regions() -> list[dict]:
    """Four European regions, a wealth Gini every fifty years, 1500 to 1800."""
    acc: dict[str, dict] = {}
    for col, (key, label) in REGION_COLS.items():
        acc[key] = {"id": key, "label": label, "layer": "preindustrial", "gini": []}
    for r in rows("alfani_regions_1500_1800.csv"):
        year = num(r.get("Year"))
        if year is None:
            continue
        for col, (key, _) in REGION_COLS.items():
            v = num(r.get(col))
            if v is not None:
                acc[key]["gini"].append([int(year), round(v, 4)])
    for s in acc.values():
        s["gini"].sort()
    return [s for s in acc.values() if s["gini"]]


# ------------------------------------------------------------------- countries

def load_countries() -> dict[str, dict]:
    """Industrial and modern layers, keyed on ISO3 so the two can sit together.

    They are still two series, not one: Alfani and Schifano estimate a Gini for
    total household wealth per decade, WID reports shares of it annually, and
    the two are drawn apart.
    """
    out: dict[str, dict] = {}

    def slot(iso: str, label: str) -> dict:
        return out.setdefault(iso, {
            "iso": iso, "label": label,
            "industrial": {"gini": [], "top10": []},
            "modern": {"top1": [], "top10": []},
        })

    for r in rows("alfani_countries_1820_2010.csv"):
        iso = (r.get("iso3") or "").strip()
        year, gini, top10 = num(r.get("Year")), num(r.get("Gini")), num(r.get("Top10per"))
        if not iso or year is None:
            continue
        s = slot(iso, (r.get("Country") or iso).strip())
        if gini is not None:
            s["industrial"]["gini"].append([int(year), round(gini, 4)])
        if top10 is not None:
            s["industrial"]["top10"].append([int(year), round(top10, 2)])

    for name, key in (("wealth-share-richest-1-percent.csv", "top1"),
                      ("wealth-share-richest-10-percent.csv", "top10")):
        for r in rows(name):
            iso = (r.get("code") or "").strip()
            # OWID rows without a code are regions and income groups, not countries
            if not iso or len(iso) != 3:
                continue
            year = num(r.get("year"))
            value = next((num(v) for k, v in r.items()
                          if k not in ("entity", "code", "year") and v not in (None, "")), None)
            if year is None or value is None:
                continue
            s = slot(iso, (r.get("entity") or iso).strip())
            # OWID carries proper country names; the Alfani sheet's Country
            # column is the ISO code for a lot of rows, so a country loaded
            # from there first would be labelled "GBR" in the picker.
            entity = (r.get("entity") or "").strip()
            if entity and s["label"] == iso:
                s["label"] = entity
            s["modern"][key].append([int(year), round(value, 2)])

    for s in out.values():
        for layer in ("industrial", "modern"):
            for k in s[layer]:
                s[layer][k].sort()
    # a country with nothing in it is noise in the picker
    return {k: v for k, v in out.items()
            if any(v[l][m] for l in ("industrial", "modern") for m in v[l])}


# ------------------------------------------------------------------------ deep

def deep() -> list[dict]:
    """The archaeological layer: a wealth Gini per dig site, from house sizes.

    Two possible sources, and the bigger one wins if it is there. Kohler et al.
    2017 is 63 sites and openly downloadable, so it ships by default. The GINI
    Project database that superseded it is 47,000 houses at 1,100 sites but
    tDAR requires a free account, so it arrives by hand. See TODO D8.
    """
    out = []
    for r in rows("gini_project.csv"):
        year, gini = num(r.get("year") or r.get("Year")), num(r.get("gini") or r.get("Gini"))
        if year is None or gini is None:
            continue
        out.append({
            "place": (r.get("site") or r.get("Site") or "").strip() or "site",
            "group": (r.get("region") or r.get("Region") or "").strip() or "Archaeology",
            "layer": "deep", "year": int(year), "gini": gini,
            "top10": None, "top1": None, "n": num(r.get("n") or r.get("N")),
            "rollup": False, "basis": "house floor areas",
            "source": "The GINI Project",
        })
    if out:
        return out

    for r in rows("kohler2017_sites.csv"):
        year, gini = num(r.get("Date_AD")), num(r.get("Gini"))
        if year is None or gini is None:
            continue
        # "various" is the site column's placeholder where a phase pools several
        # excavations; the Sites column carries the label the paper plots.
        name = (r.get("Sites") or "").strip() or (r.get("Site") or "").strip()
        period = (r.get("Period") or "").strip()
        out.append({
            "place": name or period or "site",
            "group": (r.get("Big_Region") or "").strip() or "Archaeology",
            "layer": "deep", "year": int(year), "gini": gini,
            "top10": None, "top1": None,
            "n": num(r.get("Households_in_sample")),
            "rollup": False,
            "basis": f"house floor areas, {period}" if period else "house floor areas",
            "scale": (r.get("PolJE") or "").strip(),
            # camp, village, town, city. A cleaner cut than the political
            # taxonomy: the words need no glossary, the medians are monotonic,
            # and it is the same underlying claim about scale.
            "settlement": (r.get("Site_Type") or "").strip(),
            "feeding": (r.get("Adaptation") or "").strip(),
            # Kohler publishes an 80% interval per site. Drawing the point
            # estimate alone implies a precision the method does not have.
            "lo": num(r.get("Lower_B")), "hi": num(r.get("Upper_B")),
            "source": "Kohler et al. 2017",
        })
    return out


def mark_imputed_twins(countries: dict) -> int:
    """Flag countries whose modern series is a regional curve, not their own.

    WID has no wealth survey for most microstates, so it imputes them from a
    regional group. The result is that Anguilla, Antigua, Barbados, Grenada,
    Montserrat and ten other Caribbean entries carry the SAME curve to within a
    hundredth of a percentage point, and the page happily offered each of them
    in the country picker as though it were that country's own measurement.

    Detected rather than hand-listed, because a hand-list goes stale the next
    time WID extends its coverage. Two countries are twinned when their annual
    top-decile series never differ by more than half a point over at least
    twenty shared years. That threshold is where the data actually separates:
    the tightest genuine coincidence in the file is Australia against
    Montenegro at 0.78 points, and every pair below 0.5 falls into one of six
    obvious geographic blocks. Groups are transitive, so a block is found whole.

    Nothing is dropped. The quartile band keeps them, because taking them out
    moves the median by at most 1.1 points and usually under 0.6, and dropping
    real published figures to tidy a chart is worse than carrying them. The
    flag exists so the page can say what a reader is looking at when they pick
    one.
    """
    ser = {i: dict(c["modern"].get("top10") or []) for i, c in countries.items()}
    ser = {i: v for i, v in ser.items() if len(v) > 20}
    isos = sorted(ser)

    parent = {i: i for i in isos}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for ai, a in enumerate(isos):
        for b in isos[ai + 1:]:
            shared = set(ser[a]) & set(ser[b])
            if len(shared) < 20:
                continue
            if max(abs(ser[a][y] - ser[b][y]) for y in shared) <= 0.5:
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[ra] = rb

    groups: dict[str, list[str]] = {}
    for i in isos:
        groups.setdefault(find(i), []).append(i)

    flagged = 0
    for members in groups.values():
        if len(members) < 2:
            continue
        names = sorted(countries[i]["label"] for i in members)
        for i in members:
            others = [n for n in names if n != countries[i]["label"]]
            countries[i]["twin_of"] = others
            flagged += 1
    return flagged


def industrial_provenance() -> dict:
    """How the decadal estimates were actually arrived at.

    Alfani and Schifano record a source per figure, and the honest summary is
    that most of the layer is not a measurement: 81 of the Gini figures are
    marked Interpolate, another 80 are derived from the top-tenth series
    through a fitted correlation, and the rest come from named studies (WID,
    Roine and Waldenstrom, Davies and others, the Credit Suisse databook).
    Counted at build time so the note on the page cannot go stale.
    """
    kinds = {"named": 0, "interpolated": 0, "correlated": 0}
    for r in rows("alfani_countries_1820_2010.csv"):
        src = (r.get("SourceGini") or "").strip().lower()
        if not src:
            continue
        if src.startswith("interpolate"):
            kinds["interpolated"] += 1
        elif src.startswith("correlation"):
            kinds["correlated"] += 1
        else:
            kinds["named"] += 1
    return kinds


def layers() -> dict:
    """The four layers and what each one actually measures.

    A function rather than a constant because the industrial note QUOTES the
    provenance split, and a hand-written "about a third" is a second copy of a
    number the build already counts. The two drifted the moment the counts came
    out at 79, 81 and 80 rather than 80 apiece, and the page carried the vaguer
    of the two in the one place a reader goes to check the layer.
    """
    p = industrial_provenance()
    n = p["named"] + p["interpolated"] + p["correlated"]
    return {
        "deep": {
            "label": "Excavated settlements",
            "note": "A settlement whose houses have been dug and measured. Where "
                    "nothing was written down, the spread of floor areas across a "
                    "site is the standard stand-in for the spread of household "
                    "wealth: bigger house, richer household.",
        },
        "preindustrial": {
            "label": "Tax registers",
            "note": "Assessed wealth, household by household, from the roll the "
                    "levy was charged on. The untaxed poor are added back where "
                    "the roll leaves them out.",
        },
        "industrial": {
            "label": "Reconstructed estimates",
            "note": f"Whole-country wealth every decade. {p['named']} of the {n} "
                    f"country-decades come from a national study, "
                    f"{p['interpolated']} are interpolated between two of them, and "
                    f"{p['correlated']} are inferred from the top-decile share.",
        },
        "modern": {
            "label": "National accounts",
            "note": "Shares of household net wealth from tax data and balance "
                    "sheets.",
        },
    }

SOURCES = [
    {"name": "EINITE, wealth inequality in England 1283 to 1334",
     "publisher": "Guido Alfani", "url": "https://guidoalfani.eu/data/",
     "role": "County wealth Ginis and deciles from the lay subsidies."},
    {"name": "EINITE, wealth inequality in Piedmont 1300 to 1800",
     "publisher": "Guido Alfani", "url": "https://guidoalfani.eu/data/",
     "role": "Town-level wealth Ginis and deciles from the estimi."},
    {"name": "Inequality and inequality extraction, 1500 to 1800",
     "publisher": "Guido Alfani", "url": "https://guidoalfani.eu/data/",
     "role": "Regional wealth Ginis every fifty years for Italy and the Low Countries."},
    {"name": "Wealth inequality in the long run, 1820 to 2010",
     "publisher": "Guido Alfani and Sonia Schifano",
     "url": "https://guidoalfani.eu/data/",
     "role": "Wealth Gini and top-tenth share for 39 countries, per decade."},
    {"name": "World Inequality Database",
     "publisher": "WID, via Our World in Data",
     "url": "https://ourworldindata.org/grapher/wealth-share-richest-1-percent",
     "role": "Annual shares of household wealth held by the richest 1% and 10%."},
    {"name": "Greater post-Neolithic wealth disparities in Eurasia",
     "publisher": "Kohler and others, Nature 551 (2017)",
     "url": "https://www.nature.com/articles/nature24646",
     "role": "Wealth Ginis from house floor areas at 63 sites, 9200 BC to AD 1970."},
    {"name": "The Global Dynamics of Inequality (GINI) Project",
     "publisher": "Ortman, Kohler, Bogaard and others, via tDAR",
     "url": "https://core.tdar.org/project/496853/the-global-dynamics-of-inequality-gini-project",
     "role": "The 47,000-house successor to the above. Not yet loaded."},
]


def main() -> int:
    pts = places() + deep()
    regs = regions()
    ctry = load_countries()

    years = ([p["year"] for p in pts]
             + [y for s in regs for y, _ in s["gini"]]
             + [y for c in ctry.values() for l in ("industrial", "modern")
                for m in c[l] for y, _ in c[l][m]])

    twinned = mark_imputed_twins(ctry)

    payload = {
        "meta": {
            "twinned": twinned,
            "layers": layers(),
            "industrial_provenance": industrial_provenance(),
            "sources": SOURCES,
            "year0": min(years), "year1": max(years),
            "deep_present": bool(deep()),
        },
        "points": sorted(pts, key=lambda p: (p["year"], p["place"])),
        "regions": regs,
        "countries": ctry,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")

    print(f"wrote {OUT.relative_to(ROOT)}  {OUT.stat().st_size:,} bytes")
    print(f"  {len(pts):,} place observations, {min(years)} to {max(years)}")
    print(f"  {len(regs)} regional series")
    print(f"  {len(ctry)} countries")
    for key in payload["meta"]["layers"]:
        n = sum(1 for p in pts if p["layer"] == key)
        if key == "industrial":
            n = sum(1 for c in ctry.values() if c["industrial"]["gini"])
        if key == "modern":
            n = sum(1 for c in ctry.values() if c["modern"]["top10"])
        print(f"  layer {key:14s} {n}")
    print(f"  {twinned} countries share an imputed regional series")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
