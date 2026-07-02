"""Golden-master test: reproduce the workbook's cached results.

M2 scope: every canonical (central-case) mode column. The remaining
sensitivity-variant columns join at M3 via `.replace()`-based fixtures.
"""

import csv
import math
import pathlib

import pytest

import cafein_lca
from cafein_lca.modes import CANONICAL_MODES
from cafein_lca.results import COMPONENTS

GOLDEN_CSV = pathlib.Path(__file__).parent / "data" / "golden.csv"
RTOL = 1e-9

CANONICAL_COLUMNS = {col: slug for slug, col in CANONICAL_MODES.items()}


def _golden():
    """{column: {(metric, per, component): value}}"""
    table = {}
    with open(GOLDEN_CSV, newline="") as f:
        for r in csv.DictReader(f):
            key = (r["metric"], r["per"], r["component"])
            table.setdefault(r["column"], {})[key] = r["value"]
    return table


GOLDEN = _golden()


@pytest.fixture(scope="module")
def lca():
    return cafein_lca.TransportLCA()


@pytest.mark.parametrize(
    "column,slug",
    sorted(CANONICAL_COLUMNS.items()),
    ids=lambda v: v if isinstance(v, str) else None,
)
def test_canonical_mode_matches_workbook(lca, column, slug):
    result = lca.calculate(slug)
    frame = result.to_frame()
    mismatches = []
    for (metric, per, component), expected in GOLDEN[column].items():
        row = "total" if component == "total" else component
        actual = frame[(metric, per)][row]
        if expected in ("", "#N/A"):
            if not math.isnan(actual):
                mismatches.append(
                    f"{metric}/{per}/{component}: expected NA, got {actual}")
            continue
        expected = float(expected)
        if expected == 0:
            ok = abs(actual) < 1e-12
        else:
            ok = abs(actual - expected) <= RTOL * abs(expected)
        if not ok:
            mismatches.append(
                f"{metric}/{per}/{component}: expected {expected!r}, "
                f"got {actual!r} (rel err "
                f"{abs(actual - expected) / max(abs(expected), 1e-300):.2e})")
    assert not mismatches, (
        f"{slug} ({column}) deviates from the workbook:\n  "
        + "\n  ".join(mismatches))


def test_all_components_present():
    assert set(COMPONENTS) | {"total"} == {
        key[2] for key in GOLDEN["D"].keys()}
