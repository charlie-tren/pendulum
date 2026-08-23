"""Checks on data/out/wealth.json.

The risk on this page is not arithmetic, it is CONFLATION: four kinds of
evidence that do not share a unit, quietly ending up on one line. So most of
these assert that the layers stayed apart and that each observation still knows
where it came from.

    python -m pytest tests -q
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
W = json.loads((ROOT / "data" / "out" / "wealth.json").read_text(encoding="utf-8"))

LAYERS = {"deep", "preindustrial", "industrial", "modern"}


def test_every_observation_names_its_layer_and_its_basis():
    """A dot with no provenance is the thing this page must never ship: it looks
    identical to every other dot and means something completely different."""
    for p in W["points"]:
        assert p["layer"] in LAYERS, f"{p['place']} has layer {p['layer']!r}"
        assert p.get("basis"), f"{p['place']} {p['year']} has no basis"


def test_shares_are_percentages_and_ginis_are_fractions():
    """The two are an easy swap and the charts would still draw. A Gini of 57
    plotted on a 0-to-1 axis just vanishes off the top."""
    for p in W["points"]:
        assert 0 < p["gini"] < 1, f"{p['place']} {p['year']} gini={p['gini']}"
        for k in ("top10", "top1"):
            if p.get(k) is not None:
                assert 0 <= p[k] <= 100, f"{p['place']} {p['year']} {k}={p[k]}"
    for c in W["countries"].values():
        for y, v in c["industrial"]["gini"]:
            assert 0 < v < 1, f"{c['iso']} {y} industrial gini={v}"
        for key in ("top1", "top10"):
            for y, v in c["modern"][key]:
                assert 0 <= v <= 100, f"{c['iso']} {y} {key}={v}"


def test_the_richest_tenth_holds_at_least_as_much_as_the_richest_hundredth():
    """A nesting error in the decile columns would show up here and nowhere
    else: both series would still look plausible on their own."""
    for p in W["points"]:
        if p.get("top10") is not None and p.get("top1") is not None:
            assert p["top10"] >= p["top1"] - 1e-6, \
                f"{p['place']} {p['year']}: top1 {p['top1']} exceeds top10 {p['top10']}"
    for c in W["countries"].values():
        one = dict(c["modern"]["top1"])
        for y, ten in c["modern"]["top10"]:
            if y in one:
                assert ten >= one[y] - 1e-6, f"{c['iso']} {y}: top1 {one[y]} exceeds top10 {ten}"


def test_rollups_are_marked_so_they_are_not_drawn_as_towns():
    """The Piedmont file mixes single towns with three roll-ups of the same tax
    registers. Plotted as dots they double-count their own components and make
    the evidence look denser than it is."""
    rolled = [p for p in W["points"] if p.get("rollup")]
    assert {p["place"] for p in rolled} == {
        "Piedmont (overall)", "Piedmont (cities only)", "Piedmont (rural areas only)"}
    assert all(not p.get("rollup") for p in W["points"] if p["group"] == "England")


def test_series_are_sorted_and_have_no_duplicate_years():
    """A polyline is drawn in array order, so an unsorted series draws a zigzag
    that looks like volatility rather than a bug."""
    for c in W["countries"].values():
        for layer in ("industrial", "modern"):
            for key, pts in c[layer].items():
                years = [y for y, _ in pts]
                assert years == sorted(years), f"{c['iso']} {layer}.{key} is out of order"
                assert len(years) == len(set(years)), f"{c['iso']} {layer}.{key} repeats a year"
    for s in W["regions"]:
        years = [y for y, _ in s["gini"]]
        assert years == sorted(years) and len(years) == len(set(years)), s["id"]


def test_country_labels_are_names_not_iso_codes():
    """Alfani's sheet puts the ISO code in its Country column for a lot of rows,
    so a country loaded from there before OWID was labelled "GBR" in the picker."""
    bad = [c["iso"] for c in W["countries"].values() if c["label"] == c["iso"]]
    named = [c for c in W["countries"].values() if c["modern"]["top10"]]
    assert len(bad) < len(named) * 0.1, f"{len(bad)} countries still labelled by code: {bad[:8]}"


def test_the_early_layer_really_does_reach_back_past_1300():
    """The whole point of the page. If a parser change silently drops the
    English counties, the chart still draws and starts in 1820."""
    assert W["meta"]["year0"] <= 1283
    early = [p for p in W["points"] if p["year"] < 1400]
    assert len(early) >= 20, f"only {len(early)} observations before 1400"
    assert {p["group"] for p in early} >= {"England", "Piedmont"}


def test_metrics_the_page_offers_actually_exist_in_the_data():
    """The measure picker offers three. Each has to be carried by at least two
    layers or the chart is a single lonely series."""
    for metric in ("top10", "top1", "gini"):
        layers = set()
        if any(p.get(metric) is not None for p in W["points"]):
            layers.add("preindustrial")
        if metric != "top1" and any(c["industrial"].get(metric) for c in W["countries"].values()):
            layers.add("industrial")
        if metric != "gini" and any(c["modern"].get(metric) for c in W["countries"].values()):
            layers.add("modern")
        assert len(layers) >= 2, f"{metric} is only carried by {layers}"


@pytest.mark.parametrize("key", ["layers", "sources", "year0", "year1", "deep_present"])
def test_meta_carries_what_the_page_reads(key):
    assert key in W["meta"], f"the page reads meta.{key} and the build did not write it"


def test_the_archaeological_layer_is_present_and_prehistoric():
    """Kohler et al. 2017 ships by default, openly, from Springer. If the fetch
    silently fails the page still draws three tidy panels and quietly stops
    being about the deep past at all, which is the whole reason it exists."""
    deep = [p for p in W["points"] if p["layer"] == "deep"]
    assert len(deep) >= 50, f"only {len(deep)} archaeological sites"
    assert min(p["year"] for p in deep) < -5000, "nothing older than 5000 BC"
    assert W["meta"]["year0"] < -9000


def test_each_era_carries_at_least_one_measure_the_page_can_draw():
    """Every panel has to have something in it on at least one measure, or the
    layer list names a layer the reader can never see."""
    for era in ("deep", "preindustrial"):
        pts = [p for p in W["points"] if p["layer"] == era]
        assert any(p.get(m) is not None for p in pts for m in ("gini", "top10", "top1")), era
    for era in ("industrial", "modern"):
        assert any(any(c[era].values()) for c in W["countries"].values()), era


def test_no_layer_claims_a_measure_it_cannot_support():
    """The Gini is not a share and a share is not a Gini. The archaeological
    layer has no decile breakdown at all, so it must not carry a top-tenth
    figure that would silently plot on the same axis as a real one."""
    for p in W["points"]:
        if p["layer"] == "deep":
            assert p.get("top10") is None and p.get("top1") is None,                 f"{p['place']} claims a share the house-size method cannot produce"


def test_the_two_stylesheets_are_byte_identical():
    """`site/inequality/style.css` is a DEPLOY copy that lives in the source
    tree, because the two pages ship to sibling directories at the site root and
    a shared `../style.css` there would resolve to the personal site's own
    stylesheet, not this one. CLAUDE.md names `site/style.css` as the single
    source, but nothing enforced it, so an edit to the source silently missed
    the page that actually loads the copy: four colour variables and a title
    nudge went into a file the inequality page never reads.

    The negative control for this test is simply changing one byte of either
    file, which is what produced it."""
    src = (ROOT / "site" / "style.css").read_bytes()
    dup = (ROOT / "site" / "inequality" / "style.css").read_bytes()
    assert src, "the source stylesheet is empty, so this check could not fail"
    assert src == dup, (
        "site/inequality/style.css has drifted from site/style.css; "
        "copy the source over it rather than editing the copy"
    )


def test_imputed_regional_twins_are_flagged_and_real_countries_are_not():
    """WID has no wealth survey for most microstates and imputes them from a
    regional group, so fifteen Caribbean entries carry the same curve to within
    a hundredth of a point. The page offered each one in its country picker as
    though it were that country's own measurement.

    Both halves matter. The flag has to catch the twins, and it has to leave
    alone countries that merely happen to sit at a similar level: Australia and
    Montenegro agree to 0.78 points across 45 years and are not twins."""
    twinned = [c for c in W["countries"].values() if c.get("twin_of")]
    assert len(twinned) > 20, "the detector found almost nothing, so it cannot fail"

    aia = W["countries"]["AIA"]
    assert "Antigua and Barbuda" in (aia.get("twin_of") or []), aia.get("twin_of")

    for iso in ("USA", "GBR", "AUS", "FRA", "DEU", "JPN", "CHN", "IND"):
        assert not W["countries"][iso].get("twin_of"), (
            f"{iso} was flagged as an imputed twin, which it is not")


def test_twin_flags_are_symmetric():
    """A one-sided flag would tell the reader that Anguilla is a copy of
    Antigua while Antigua looks like an original. Neither is."""
    for iso, c in W["countries"].items():
        for other in c.get("twin_of") or []:
            mate = next(x for x in W["countries"].values() if x["label"] == other)
            assert c["label"] in (mate.get("twin_of") or []), f"{iso} -> {other}"
