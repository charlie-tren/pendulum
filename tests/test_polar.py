"""Checks on data/out/polarisation.json.

The risk here is not arithmetic, it is CONFLATION and OVERCLAIM. Three layers
answer three different questions on three different scales, and the page's whole
argument is a contrast between axes, so the tests hold the layers apart and pin
the contrast itself.

    python -m pytest tests -q
"""
from __future__ import annotations

import json
import re
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

# BOTH FILES. Most of the panel copy is generated in app.js now that it names
# the selected country and its own baseline decade, so a test reading only the
# markup would be checking the shell rather than the sentences.
PAGE = (ROOT / "site" / "polarisation" / "index.html").read_text(encoding="utf-8")
APP = (ROOT / "site" / "polarisation" / "app.js").read_text(encoding="utf-8")
# Comments are stripped, because this is the text a READER meets. The first
# run without it failed on a code comment explaining why a count is computed
# rather than typed - a check matching its own warning.
COPY = re.sub(r"/\*.*?\*/|^\s*//.*$", "", PAGE + APP, flags=re.S | re.M)
BUILD = (ROOT / "scripts" / "build_polar.py").read_text(encoding="utf-8")


def test_no_country_count_is_typed_into_the_copy():
    """Every count on the page is read off the payload at render time. A typed
    one goes stale the next time V-Dem extends coverage, and nothing would say
    so: the page would simply be wrong by one or two countries for ever."""
    # The meta description is exempt: scripts/bake_static.py writes it from the
    # payload, and test_sibling_descriptions_match_their_data fails if it goes stale.
    copy = re.sub(r'<meta name="description" content="[^"]*">', "", COPY)
    for pat in (r"middle half of (\d+)", r"(\d{3}) countries"):
        hit = re.search(pat, copy)
        assert hit is None, f"hardcoded count in the page copy: {hit.group(0)!r}"


def test_the_share_title_names_a_period_the_data_supports():
    """og:title claims the world is about as divided as it was in the
    mid-1970s. It said 1978 first, which was twice as far from today's median as
    1974 and 1975 are, so the claim was picking a year for sounding precise."""
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


def test_the_build_enforces_the_coverage_floor_the_payload_advertises():
    """An election is scored only where the parties carrying a coded position
    hold at least this share of the vote V-Party records for it. The figure is
    in the payload so the build and anything reading it cannot drift apart."""
    assert P["meta"]["min_coverage"] == 0.70
    assert "0.70" in BUILD, "the build no longer names the floor it publishes"


def test_the_copy_never_states_a_bare_vote_coverage_figure():
    """The floor is 70% of the vote V-PARTY LISTS, and V-Party lists a median of
    91% of the vote cast, not all of it. Saying '70% of the vote' claims the
    stricter of the two. The method paragraph that said it has come off the
    page, so this guards the figure on its way back rather than asserting copy
    that must be there: it may return, unqualified it may not."""
    if "70% of the vote" not in COPY:
        return
    assert "V-Party" in COPY.split("70% of the vote")[1][:40], (
        "the copy says '70% of the vote' without saying 70% of WHICH vote")


def test_every_country_codes_all_nine_axes_at_every_election():
    """The party chart indexes a country against its OWN first decade, and that
    is only one dotted line rather than nine because a country's axes all start
    together. If V-Party ever codes an axis from a later wave, the baseline
    stops meaning one thing and the chart has to say so."""
    for name, axes in P["party"].items():
        years = {k: {r[0] for r in rows} for k, rows in axes.items()}
        if not years:
            continue
        first = min(min(v) for v in years.values() if v)
        dec = (first // 10) * 10
        for k, v in years.items():
            assert any(dec <= y <= dec + 9 for y in v), (
                f"{name}: {k} has nothing in its own baseline decade {dec}s")


def test_the_site_serves_the_payload_the_tests_read():
    """Two copies of one file, and only one of them is checked here. The build
    writes both from a single dump so they cannot part company; this fails if
    somebody goes back to copying it by hand and forgets."""
    served = (ROOT / "site" / "polarisation" / "data.json").read_bytes()
    built = (ROOT / "data" / "out" / "polarisation.json").read_bytes()
    assert served == built, (
        "the page is serving a different payload from the one under test")


def test_the_twenty_year_window_is_real_for_almost_every_country():
    """The ranked lists compare a country with itself twenty years earlier, so
    a country rated in only one of the two years drops out silently. If that
    ever became common the lists would rank a rump rather than the world."""
    band = P["bands"]["society"]["camps"]
    to = band[-1][0]
    have = sum(1 for axes in P["society"].values()
               if {to, to - 20} <= {r[0] for r in axes.get("camps", [])})
    assert have >= len(P["society"]) - 15, (
        f"only {have} of {len(P['society'])} countries have both ends of the "
        f"{to - 20} to {to} window")


def test_no_layer_counts_a_polity_twice():
    """V-Dem's coding units are POLITIES, and one of them is inside another:
    Zanzibar's own metadata calls it "a semi-autonomous region of Tanzania",
    Tanzania's calls itself "the United Republic of Tanzania [Zanzibar joins
    Tanganyika]", and Zanzibaris vote in Tanzanian national elections. So the
    island was in every cross-section twice, and in a list of countries
    besides, which is where Charlie found it.

    Merging is not the alternative: the two are coded separately because they
    are separately governed, and over twenty years they moved in opposite
    directions, so an average is a number nobody measured.

    WHAT IS DELIBERATELY STILL HERE is the other half of this test. Hong Kong
    is described by V-Dem in the same shape of words and is kept anyway, by
    decision, because it is governed under its own legal order and franchise.
    Somaliland and the German Democratic Republic are self-governing and
    sovereign respectively. If a future pass cuts any of them as tidying, this
    fails and says so."""
    parent = {"Zanzibar": "Tanzania"}
    for layer in LAYERS:
        for unit in parent:
            assert unit not in P[layer], f"{layer} still counts {unit} twice"
    for whole in parent.values():
        assert whole in P["society"], f"{whole} is missing, so the part was cut for nothing"
    assert not set(parent) & set(P["meta"]["iso2"]), (
        "a dropped unit still has a flag, so something can still render it")

    for kept in ("Hong Kong", "Somaliland", "German Democratic Republic"):
        assert kept in P["society"], (
            f"{kept} was dropped. It is not double counted by anything here: "
            "Hong Kong is kept by decision, Somaliland governs itself, and the "
            "GDR was sovereign for every year it is coded")


def test_every_change_the_page_prints_survives_moving_the_window():
    """A number the page states has to be a measurement, not a reading of two
    particular years.

    It was not. Computed from single years, 2005 to 2025, the biggest fall on
    earth was Kyrgyzstan at -1.56 - and shifting the window one year turns that
    into +0.61. Its 2005 was the Tulip Revolution, a spike between 2.05 and
    1.43, and its 2025 is one year lower than the three flat years before it.
    On trailing five-year means the same country reads +0.18.

    What is checked is the VALUE, not the membership. A top five cut through a
    continuum always churns at the boundary and testing that would be fitting a
    test to today's data. What must not happen is a printed number changing
    sign, or moving by as much as it claims.

    Measured: on five-year means the worst listed country moves 0.87 across a
    two-year shift and most move under 0.45. On single years the worst moves
    2.17, so this fails loudly if anyone puts them back."""
    soc = {n: dict(a["camps"]) for n, a in P["society"].items() if a.get("camps")}
    band = P["bands"]["society"]["camps"]
    to0, window, smooth = band[-1][0], 20, 5

    def change(name, to):
        d = soc[name]

        def trail(end):
            v = [d[y] for y in range(end - smooth + 1, end + 1) if y in d]
            return sum(v) / smooth if len(v) == smooth else None

        a, b = trail(to - window), trail(to)
        return None if a is None or b is None else b - a

    rows = sorted((c, n) for n in soc if (c := change(n, to0)) is not None)
    assert len(rows) > 150, f"only {len(rows)} countries have the full window"

    for listed in (rows[:5], rows[-5:]):
        for base, name in listed:
            # the window can only slide backwards: there is no data after the
            # last year, and sliding forward would empty it
            for shift in (-1, -2):
                moved = change(name, to0 + shift)
                assert moved is not None, f"{name} has no {to0 + shift} window"
                assert (base > 0) == (moved > 0), (
                    f"{name} is printed as {base:+.2f} and reads {moved:+.2f} "
                    f"with the window {shift:+d} year: the sign is an artefact "
                    "of which years the ends landed on")
                assert abs(base - moved) < 1.0, (
                    f"{name} is printed as {base:+.2f} and moves "
                    f"{abs(base - moved):.2f} over {shift:+d} year")


def test_the_ranked_lists_rank_something_that_actually_differs():
    """The lists were moved off levels because the hostile end was saturated:
    the five most divided countries sat inside 0.02 of each other on a 0 to 4
    scale, which is not an ordering. Whatever they rank has to separate."""
    band = P["bands"]["society"]["camps"]
    to = band[-1][0]
    moves = sorted(
        dict(axes["camps"])[to] - dict(axes["camps"])[to - 20]
        for axes in P["society"].values()
        if {to, to - 20} <= {r[0] for r in axes.get("camps", [])})
    for end in (moves[:5], moves[-5:]):
        assert max(end) - min(end) > 0.2, (
            f"the top five span {max(end) - min(end):.2f}, too close to call "
            "an order")


def test_the_layers_span_the_years_the_page_is_built_on():
    """The window each layer actually carries. Not the same as the publishers'
    coverage, which the sources list quotes: V-Party codes elections back to
    1900 and this page starts at 1970, because the earlier ones are too sparse
    to index a country against."""
    spans = {
        "party": (1970, 2019),
        "europe": (1999, 2024),
        "society": (1900, 2025),
    }
    for layer, (lo, hi) in spans.items():
        years = [r[0] for c in P[layer].values() for rows in c.values() for r in rows]
        assert min(years) == lo and max(years) == hi, (
            f"{layer} runs {min(years)}-{max(years)}, expected {lo}-{hi}")


def test_the_sources_quote_the_publishers_coverage_not_our_slice():
    """A sources list says what the publisher ships, so a reader can download
    it and find the same thing. Reporting our own window there was the fault
    that got the previous version taken off the page. Every figure is counted
    from the publishers' own frames at build time, and this checks the rendered
    sentences against those counts."""
    reach = P["meta"]["source_reach"]
    detail = {s["name"]: s["detail"] for s in P["meta"]["sources"]}

    vp, vd = reach["party"], reach["society"]
    for n in (f"{vp['parties']:,}", str(vp["countries"]), f"{vp['elections']:,}",
              str(vp["lo"]), str(vp["hi"])):
        assert n in detail["V-Party v2"], f"V-Party detail omits {n}"
    for n in (str(vd["countries"]), f"{vd['rows']:,}",
              str(vd["lo"]), str(vd["hi"])):
        assert n in detail["V-Dem v16"], f"V-Dem detail omits {n}"

    # and our slice must sit INSIDE what the publisher is said to cover
    for layer, key in (("party", "party"), ("society", "society")):
        years = [r[0] for c in P[layer].values() for rows in c.values() for r in rows]
        assert reach[key]["lo"] <= min(years) and max(years) <= reach[key]["hi"], (
            f"{layer} runs outside the coverage the sources list claims")


def test_the_ches_waves_named_in_the_sources_are_the_waves_in_the_data():
    """CHES has no raw frame to count, so its line lists the seven waves. Every
    wave named has to be a year the trend file actually carries, or the list is
    advertising a survey the page does not hold."""
    import re
    line = next(s["detail"] for s in P["meta"]["sources"] if "Chapel Hill" in s["name"])
    named = {int(y) for y in re.findall(r"\b(?:19|20)\d{2}\b", line)}
    have = {r[0] for c in P["europe"].values() for rows in c.values() for r in rows}
    assert named, "the CHES line names no waves"
    assert named <= have, f"named but absent from the data: {sorted(named - have)}"
