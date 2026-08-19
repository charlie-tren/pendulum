"""Checks on the built payload and the aggregation maths.

Most of these run against data/out/orientation.json rather than calling the
functions directly, because the failures worth catching are the ones that
survive into what the site actually reads: a band that quietly stops summing to
one, a mean taken over the wrong denominator, a moving average that starts
peeking at the future again.

    python -m pytest tests -q
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

DATA = json.loads((ROOT / "data" / "out" / "orientation.json").read_text(encoding="utf-8"))
MAP = json.loads((ROOT / "data" / "out" / "map.json").read_text(encoding="utf-8"))

BANDS = ["left", "centre", "right", "no_reading", "unresolved"]
SPECTRUM = [f"f{i}" for i in range(7)] + ["uncovered"]
TOL = 2e-3          # shares are rounded to 4dp before they are written out


def groups():
    return DATA["groups"].items()


# --------------------------------------------------------------------------- shares

@pytest.mark.parametrize("weighting", ["by_population", "by_country"])
def test_bucket_shares_sum_to_one(weighting):
    for name, group in groups():
        for row in group[weighting]:
            total = sum(row[b] or 0 for b in BANDS)
            assert abs(total - 1) < TOL, f"{name} {row['year']} {weighting} sums to {total}"


def test_spectrum_shares_sum_to_one():
    for name, group in groups():
        for weighting in ("by_population", "by_country"):
            for row in group["spectrum"][weighting]:
                total = sum(row[b] or 0 for b in SPECTRUM)
                assert abs(total - 1) < TOL, f"{name} {row['year']} spectrum sums to {total}"


def test_cross_tab_cells_sum_to_one():
    """The mosaic reads block AREA as a share of the group, so the grid has to
    account for everyone exactly once."""
    for name, group in groups():
        for row in group["cross"]:
            total = sum(v for cell in row["cells"].values() for v in cell.values())
            assert abs(total - 1) < TOL, f"{name} {row['year']} cross sums to {total}"


def test_no_negative_shares():
    for name, group in groups():
        for weighting in ("by_population", "by_country"):
            for row in group[weighting]:
                for b in BANDS:
                    assert (row[b] or 0) >= 0, f"{name} {row['year']} {b} is negative"


# --------------------------------------------------------------------------- means

def test_mean_is_taken_over_coded_countries_only():
    """no_reading and unresolved must not drag the mean toward zero: a country
    with no left-right reading is not a centrist country."""
    for name, group in groups():
        for row, index in zip(group["by_population"], group["index"]):
            coded = sum(row[b] or 0 for b in ("left", "centre", "right"))
            if coded < 0.01 or index["mean_by_population"] is None:
                continue
            expected = ((row["right"] or 0) - (row["left"] or 0)) / coded
            assert abs(expected - index["mean_by_population"]) < 5e-3, \
                f"{name} {row['year']}: mean {index['mean_by_population']} vs {expected}"


def test_mean_stays_in_range():
    for name, group in groups():
        for row in group["index"]:
            for key in ("mean_by_population", "mean_by_country"):
                if row[key] is not None:
                    assert -1 <= row[key] <= 1, f"{name} {row['year']} {key}={row[key]}"


# --------------------------------------------------------------------------- moving average

def test_moving_average_is_trailing_not_centred():
    """The original spreadsheet used a centred mean that peeked at t+1. If that
    ever comes back, this is the test that catches it."""
    from build_index import trailing_ma
    series = [{"year": 2000 + i, "v": float(i)} for i in range(6)]
    trailing_ma(series, "v")
    assert series[0]["v_ma3"] is None
    assert series[1]["v_ma3"] is None
    # trailing: (0+1+2)/3 = 1. Centred would give (0+1+2)/3 at index 1, not 2.
    assert series[2]["v_ma3"] == pytest.approx(1.0)
    assert series[5]["v_ma3"] == pytest.approx(4.0)


def test_moving_average_matches_the_built_series():
    for name, group in groups():
        idx = group["index"]
        for i, row in enumerate(idx):
            if row["mean_by_population_ma3"] is None or i < 2:
                continue
            window = [idx[j]["mean_by_population"] for j in (i - 2, i - 1, i)]
            if any(v is None for v in window):
                continue
            assert abs(sum(window) / 3 - row["mean_by_population_ma3"]) < 5e-3, \
                f"{name} {row['year']} moving average is not the trailing three"


# --------------------------------------------------------------------------- weighting

def test_population_weight_is_per_year_not_fixed():
    """A country that grows should gain weight. If the lookup ever drops the
    year, every year would divide by the same total."""
    totals = {r["year"]: r["pop"] for r in DATA["groups"]["world"]["by_population"]}
    assert totals[1975] < totals[1995] < totals[2015] < totals[2025]
    assert totals[2025] / totals[1975] > 1.9, "world population barely moved: weights look fixed"


def test_world_weight_is_close_to_actual_world_population():
    """A large shortfall means countries are missing from the aggregate
    entirely, which is worse than them showing as unresolved."""
    actual = {}
    with open(ROOT / "data" / "raw" / "pop_proj.csv", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            if row["entity"] == "World":
                value = row["population_historical"] or row["population_projection__projected"]
                if value:
                    actual[int(row["year"])] = float(value)
    weights = {r["year"]: r["pop"] for r in DATA["groups"]["world"]["by_population"]}
    for year in (1975, 1990, 2005, 2020):
        shortfall = 1 - weights[year] / actual[year]
        assert shortfall < 0.03, f"{year}: {shortfall:.1%} of the world is not in the aggregate"


# --------------------------------------------------------------------------- integrity

def test_every_map_code_has_geometry():
    missing = [iso for iso in MAP["paths"] if not MAP["paths"][iso]]
    assert not missing, f"countries with an empty path: {missing}"


def test_map_series_covers_the_same_years_as_the_charts():
    span = DATA["map"]["year1"] - DATA["map"]["year0"] + 1
    for iso, codes in DATA["map"]["codes"].items():
        assert len(codes) == span, f"{iso} has {len(codes)} codes for {span} years"


def test_hand_coded_rows_do_not_contradict_dpi():
    """The seam guard: a hand-coded row must not disagree with DPI about a party
    DPI itself codes and that never left office."""
    import audit_hand_coded
    assert audit_hand_coded.main() == 0


def test_no_duplicate_country_years():
    """Seeding a country that already exists for some years would double-count
    it in every weighted total."""
    import yaml

    import build_index as B
    from resolve import load_dpi
    cmap = yaml.safe_load((ROOT / "config" / "country_map.yaml").read_text(encoding="utf-8"))
    records = B.seed_entities(B.extend_years(load_dpi(cmap)),
                              ROOT / "config" / "seed_entities.yaml")
    seen = set()
    for rec in records:
        key = (rec["entity"], rec["year"])
        assert key not in seen, f"duplicate row for {key}"
        seen.add(key)
