"""Checks on data/out/polarisation.json.

The risk here is not arithmetic, it is CONFLATION and OVERCLAIM. Three layers
answer three different questions on three different scales, and the page's whole
argument is a contrast between axes, so the tests hold the layers apart and pin
the contrast itself.

    python -m pytest tests -q
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = json.loads((ROOT / "data" / "out" / "polarisation.json").read_text(encoding="utf-8"))

LAYERS = ("party", "europe", "society")
CULTURAL = ("immigration", "lgbt", "minorities")


# a band row is [year, min, p10, p25, p50, p75, p90, max, n]. Named, because
# this index moved once already: the row was widened from three cut points to
# seven and every test here went on reading r[2], which had silently become the
# tenth percentile. They all still passed, against the wrong statistic.
MIN, P10, P25, P50, P75, P90, MAX, N = 1, 2, 3, 4, 5, 6, 7, 8


def decade_median(layer, axis, lo, hi):
    """Median of the per-year median across the countries in a window."""
    rows = [r for r in P["bands"][layer][axis] if lo <= r[0] <= hi]
    if not rows:
        return None
    v = sorted(r[P50] for r in rows)
    return v[len(v) // 2]


def test_every_layer_is_present_and_none_is_empty():
    for layer in LAYERS:
        assert P[layer], layer
        assert P["bands"][layer], layer


def test_series_are_sorted_and_never_repeat_a_year():
    for layer in LAYERS:
        for country, axes in P[layer].items():
            for axis, rows in axes.items():
                years = [r[0] for r in rows]
                assert years == sorted(years), f"{layer}/{country}/{axis} unsorted"
                assert len(years) == len(set(years)), f"{layer}/{country}/{axis} repeats"


def test_a_spread_is_never_negative_and_a_society_rating_stays_on_its_scale():
    """A standard deviation below zero means the weights went wrong. The V-Dem
    ordinal-scale projection is bounded 0 to 4 by construction, so a value
    outside it means the wrong column was read."""
    for country, axes in P["party"].items():
        for axis, rows in axes.items():
            for year, sd, mu, n in rows:
                assert sd >= 0, f"{country} {axis} {year}: spread {sd}"
                assert n >= 2, f"{country} {axis} {year}: {n} parties"
    for country, axes in P["society"].items():
        for axis, rows in axes.items():
            for year, v in rows:
                assert 0 <= v <= 4, f"{country} {axis} {year}: {v}"


def test_the_layers_cannot_be_confused_for_one_another():
    """A party row is [year, spread, mean, parties]; a society row is [year,
    rating]. Four kinds of number against two. If these ever match in shape,
    something has started averaging a spread with a rating."""
    party = next(iter(P["party"].values()))
    society = next(iter(P["society"].values()))
    assert len(next(iter(party.values()))[0]) == 4
    assert len(next(iter(society.values()))[0]) == 2


def test_the_vote_coverage_floor_actually_excluded_something():
    """The floor exists because joint lists like Fidesz-KDNP carry the vote on a
    row with no coding, so dropping uncoded parties would score the election on
    whoever is left. A floor that never fires is a floor that is not wired up."""
    cov = P["meta"]["coverage"]
    assert cov["kept"] > 500, cov
    assert cov["dropped_low_coverage"] > 0, (
        "no election was ever dropped, so the coverage floor is not doing anything")


def test_band_rows_are_a_sorted_ladder_over_at_least_four_countries():
    """Seven cut points, in order, every year. Out of order means the
    percentile function or the column order went wrong, and the chart would draw
    envelopes that cross each other rather than nest."""
    for layer in LAYERS:
        for axis, rows in P["bands"][layer].items():
            for row in rows:
                assert row[N] >= 4, f"{layer}/{axis} {row[0]}: n={row[N]}"
                ladder = row[MIN:N]
                assert ladder == sorted(ladder), f"{layer}/{axis} {row[0]}: {ladder}"


def test_the_full_range_is_much_wider_than_the_middle_half():
    """The reason the outer envelopes are drawn at all. If the middle half ever
    came to describe the population well, the extra bands would be clutter and
    this should say so rather than the page carrying them out of habit."""
    rows = [r for r in P["bands"]["society"]["camps"] if r[0] >= 1950]
    assert rows
    ratio = sorted((r[MAX] - r[MIN]) / (r[P75] - r[P25]) for r in rows)
    # measured rather than guessed: over the 76 years since 1950 the ratio runs
    # 1.94 to 2.46 with a median of 2.24, so the full range is consistently
    # about twice the middle half. 1.6 is well below the observed floor and well
    # above 1.0, which is the value at which the outer bands would be redundant.
    assert ratio[0] > 1.6, (
        f"the narrowest year has a full range only {ratio[0]:.2f} times its "
        "middle half, so the outer bands have stopped telling the reader "
        "anything the inner one does not")


def test_the_economic_axis_moved_less_than_every_cultural_one():
    """THE PAGE'S ARGUMENT, asserted so it cannot silently invert.

    Parties did not move further apart on the economy; they moved apart on
    culture. If a future rebuild, a rescale or a source update reverses that,
    the headline is wrong and this should fail rather than the page quietly
    saying something untrue.

    The negative control is real: swap `economy` for `lgbt` below and it fails,
    because LGBT is not flat."""
    econ_a = decade_median("party", "economy", 1970, 1979)
    econ_z = decade_median("party", "economy", 2010, 2019)
    econ_swing = (econ_z - econ_a) / econ_a

    for axis in CULTURAL:
        a = decade_median("party", axis, 1970, 1979)
        z = decade_median("party", axis, 2010, 2019)
        swing = (z - a) / a
        assert swing > econ_swing + 0.25, (
            f"{axis} rose {swing:.0%} against economy {econ_swing:.0%}; the "
            "contrast the page is built on has gone")
    assert econ_swing < 0.30, f"the economic axis rose {econ_swing:.0%}, not flat"


def test_europe_agrees_with_the_party_layer_on_the_same_contrast():
    """CHES is a different panel, different questions, different scale and a
    different set of countries. It is only worth carrying if it is an
    independent check, which means it has to agree about the contrast."""
    econ_a = decade_median("europe", "economy", 1999, 2006)
    econ_z = decade_median("europe", "economy", 2019, 2024)
    cult_a = decade_median("europe", "culture", 1999, 2006)
    cult_z = decade_median("europe", "culture", 2019, 2024)
    econ = (econ_z - econ_a) / econ_a
    cult = (cult_z - cult_a) / cult_a
    assert cult > econ, f"CHES: culture {cult:.0%} vs economy {econ:.0%}"


def test_society_is_not_at_an_all_time_high():
    """The other half of the honesty. Society-level polarisation is U-shaped:
    the 2020s are a return to 1970s levels, not an unprecedented peak. A page
    that said 'the most polarised ever' would be wrong, so the shape is pinned."""
    seventies = decade_median("society", "camps", 1970, 1979)
    nineties = decade_median("society", "camps", 1990, 1999)
    twenties = decade_median("society", "camps", 2020, 2025)
    assert nineties < seventies, "the fall after the Cold War has gone"
    assert twenties > nineties, "the rise since the 1990s has gone"
    assert twenties < seventies * 1.15, (
        f"the 2020s ({twenties:.2f}) now clear the 1970s ({seventies:.2f}) by "
        "enough that calling it a return rather than a peak is overclaiming")


def test_society_reaches_past_the_party_data():
    """The only reason this layer is here rather than being another spread: it
    is the one that can see 2020 onwards at all."""
    last_party = max(r[0] for axes in P["party"].values()
                     for rows in axes.values() for r in rows)
    last_society = max(r[0] for axes in P["society"].values()
                       for rows in axes.values() for r in rows)
    assert last_party <= 2019, last_party
    assert last_society >= 2024, last_society


# ---- the copy, checked against the data it describes -----------------------
# These read the page, not a transcription of it. The recurring failure on these
# pages is not wrong arithmetic, it is a sentence that was true when it was
# written and quietly stopped being true, so the claims live here.

PAGE = (ROOT / "site" / "polarisation" / "index.html").read_text(encoding="utf-8")


def test_no_country_count_is_typed_into_the_copy():
    """Every count on the page is read off the payload at render time. A typed
    one goes stale the next time V-Dem extends coverage, and nothing would say
    so: the page would simply be wrong by one or two countries for ever."""
    import re
    for pat in (r"middle half of (\d+)", r"(\d{3}) countries"):
        hit = re.search(pat, PAGE)
        assert hit is None, f"hardcoded count in the page copy: {hit.group(0)!r}"


def test_the_share_title_names_a_period_the_data_supports():
    """og:title claims the world is about as divided as it was in the
    mid-1970s. It said 1978 first, which was twice as far from today's median as
    1974 and 1975 are, so the claim was picking a year for sounding precise."""
    import re
    med = {r[0]: r[P50] for r in P["bands"]["society"]["camps"]}
    now = med[max(med)]
    claimed = re.search(r'og:title" content="([^"]+)"', PAGE).group(1)
    assert "mid-1970s" in claimed, claimed
    window = [v for y, v in med.items() if 1974 <= y <= 1976]
    assert window, "no mid-1970s data"
    gap = abs(now - sum(window) / len(window))
    assert gap < 0.25, (
        f"today's median {now:.2f} is {gap:.2f} from the mid-1970s, too far to "
        "call them about the same on a 0 to 4 scale")


def test_the_method_does_not_overstate_the_vote_coverage():
    """The floor is 70% of the vote V-PARTY LISTS, and V-Party lists a median of
    91% of the vote cast, not all of it. Saying '70% of the vote' claims the
    stricter of the two, so the sentence has to name which one it means."""
    assert "70% of the vote" in PAGE
    assert "V-Party" in PAGE.split("70% of the vote")[1][:40], (
        "the method says '70% of the vote' without saying 70% of WHICH vote")


def test_every_source_date_range_matches_the_data_behind_it():
    """Three sources, three spans, all quoted in the sources list."""
    spans = {
        "party": (1970, 2019),
        "europe": (1999, 2024),
        "society": (1900, 2025),
    }
    for layer, (lo, hi) in spans.items():
        years = [r[0] for c in P[layer].values() for rows in c.values() for r in rows]
        assert min(years) == lo and max(years) == hi, (
            f"{layer} runs {min(years)}-{max(years)}, the sources say {lo}-{hi}")
        for n in (lo, hi):
            assert str(n) in json.dumps(P["meta"]["sources"]), (
                f"{n} is not quoted in any source's role text")
