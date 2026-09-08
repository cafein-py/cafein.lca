"""Golden-master test: reproduce the workbook's cached results.

Covers every workbook mode column: the 56 canonical modes, plus all
sensitivity-variant columns — expressed as `.replace()` overrides of their
central case where the workbook allows it (see tests/data/variants.csv), and
as direct column fixtures otherwise. Expectations the engine intentionally
does not reproduce are overridden by tests/data/golden_adjustments.csv
(see docs/workbook-audit.md items 4 and 6).
"""

import csv
import json
import math
import pathlib

import pytest

import cafein_lca
from cafein_lca.modes import CANONICAL_MODES, _mode_by_column, mode
from cafein_lca.results import COMPONENTS

DATA = pathlib.Path(__file__).parent / "data"
RTOL = 1e-9

NUMERIC_OVERRIDES = {
    "lifetime_years",
    "annual_km",
    "vehicle_weight_kg",
    "battery_capacity_kwh",
    "occupancy",
    "service_km_per_vehicle_day",
    "vehicles_per_service_trip",
    "fuel_consumption_per_100km",
    "electricity_consumption_kwh_per_km",
    "hydrogen_consumption_per_100km",
    "electric_driving_share",
}
SLUG_BY_COLUMN = {col: slug for slug, col in CANONICAL_MODES.items()}


def _golden():
    table = {}
    with open(DATA / "golden.csv", newline="") as f:
        for r in csv.DictReader(f):
            key = (r["metric"], r["per"], r["component"])
            table.setdefault(r["column"], {})[key] = r["value"]
    with open(DATA / "golden_adjustments.csv", newline="") as f:
        for r in csv.DictReader(f):
            key = (r["metric"], r["per"], r["component"])
            table[r["column"]][key] = r["value"]
    return table


def _variants():
    with open(DATA / "variants.csv", newline="") as f:
        return [r for r in csv.DictReader(f) if r["fixture"] != "excluded"]


GOLDEN = _golden()
VARIANTS = _variants()


@pytest.fixture(scope="module")
def lca():
    return cafein_lca.TransportLCA()


def _params_for_variant(variant):
    if variant["fixture"] == "column":
        params, _ = _mode_by_column(variant["column"])
        return params
    central = mode(SLUG_BY_COLUMN[variant["central_column"]])
    overrides = {}
    for field, value in json.loads(variant["overrides"]).items():
        if field in NUMERIC_OVERRIDES:
            overrides[field] = float(value) if value else 0.0
        elif field == "electricity_region":
            overrides[field] = None if value in ("", "World") else value
        else:
            overrides[field] = value
    return central.replace(**overrides)


def _assert_matches(column, frame, label):
    mismatches = []
    for (metric, per, component), expected in GOLDEN[column].items():
        if expected == "skip":
            continue
        row = "total" if component == "total" else component
        actual = frame[(metric, per)][row]
        if expected in ("", "#N/A"):
            if not math.isnan(actual):
                mismatches.append(
                    f"{metric}/{per}/{component}: expected NA, got {actual}"
                )
            continue
        expected = float(expected)
        if expected == 0:
            ok = abs(actual) < 1e-12
        else:
            ok = abs(actual - expected) <= RTOL * abs(expected)
        if not ok:
            mismatches.append(
                f"{metric}/{per}/{component}: expected {expected!r}, " f"got {actual!r}"
            )
    assert (
        not mismatches
    ), f"{label} ({column}) deviates from the workbook:\n  " + "\n  ".join(mismatches)


@pytest.mark.parametrize(
    "column,slug",
    sorted(SLUG_BY_COLUMN.items()),
    ids=lambda v: v if isinstance(v, str) else None,
)
def test_canonical_mode_matches_workbook(lca, column, slug):
    _assert_matches(column, lca.calculate(slug).to_frame(), slug)


@pytest.mark.parametrize("variant", VARIANTS, ids=[v["column"] for v in VARIANTS])
def test_variant_matches_workbook(lca, variant):
    params = _params_for_variant(variant)
    _assert_matches(
        variant["column"],
        lca.calculate(params).to_frame(),
        f"{variant['fixture']}:{variant['name'][:50]}",
    )


def test_replace_fixtures_dominate():
    # Most sensitivity variants must be expressible as parameter overrides;
    # guards against silent leaf-data drift turning them into column
    # fixtures.
    kinds = [v["fixture"] for v in VARIANTS]
    assert kinds.count("replace") >= 45


def test_all_components_present():
    assert set(COMPONENTS) | {"total"} == {key[2] for key in GOLDEN["D"].keys()}
