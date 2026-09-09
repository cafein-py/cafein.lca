"""Unit tests for the cafein export helpers (cafein.lca.export).

These need no cafein install; they check the schema, the 5->4 component
mapping, the basis rule, provenance, the identities mapping and the CSV
schema round-trip. The end-to-end check that cafein honours the exported
`basis` lives in tests/test_integration.py, under the cafein extra.
"""

import hashlib
import io

import pandas as pd
import pytest

from cafein.lca import Scenario, TransportLCA, __version__
from cafein.lca import scenarios
from cafein.lca.export import (
    READ_CSV_DTYPES,
    STREET_COLUMNS,
    TRANSIT_COLUMNS,
)


@pytest.fixture(scope="module")
def lca():
    return TransportLCA()


def test_column_order_matches_schema(lca):
    assert list(lca.transit_factors().columns) == TRANSIT_COLUMNS
    assert list(lca.street_factors().columns) == STREET_COLUMNS


@pytest.mark.parametrize(
    "helper, slug, per, basis",
    [
        ("transit_factors", "bus_bev", "per_pkm", "passenger_km"),
        ("street_factors", "private_bike", "per_pkm", "passenger_km"),
        ("street_factors", "private_car_bev", "per_vkm", "vehicle_km"),
        ("street_factors", "taxi_ice", "per_pkm", "passenger_km"),
    ],
)
def test_component_mapping_and_basis(lca, helper, slug, per, basis):
    row = getattr(lca, helper)(modes=[slug]).iloc[0]
    series = getattr(lca.calculate(slug), per)
    assert row["basis"] == basis
    assert row["vehicle"] == pytest.approx(series["manufacturing"] + series["delivery"])
    assert row["fuel"] == pytest.approx(series["use"])
    assert row["infrastructure"] == pytest.approx(series["infrastructure"])
    assert row["operations"] == pytest.approx(series["services"])
    components = (
        row["vehicle"] + row["fuel"] + row["infrastructure"] + row["operations"]
    )
    assert row["total"] == pytest.approx(components)


def test_deadheading_uses_raw_engine_components(lca):
    # Self-serviced mode: operations is the engine's servicing (empty-km) and
    # fuel the revenue-km use; no ITF report figure-sheet reallocation.
    row = lca.street_factors(modes=["taxi_ice"]).iloc[0]
    per_pkm = lca.calculate("taxi_ice").per_pkm
    assert row["operations"] == pytest.approx(per_pkm["services"])
    assert row["fuel"] == pytest.approx(per_pkm["use"])


def test_provenance_default_session(lca):
    row = lca.transit_factors(modes=["bus_bev"]).iloc[0]
    assert row["scenario"] == ""
    assert row["scenario_sha256"] == ""
    assert row["case"] == ""
    assert row["cafein_lca_version"] == __version__


def test_provenance_scenario_session():
    scenario = Scenario.load("finland_2020", case="middle")
    session = TransportLCA(scenario=scenario)
    row = session.street_factors(modes=["private_car_bev"]).iloc[0]
    expected_sha = hashlib.sha256(
        scenarios._locate("finland_2020").read_bytes()
    ).hexdigest()
    assert row["scenario"] == scenario.name
    assert row["case"] == "middle"
    assert row["scenario_sha256"] == scenario.sha256 == expected_sha


def test_identities_fill_named_keys_only(lca):
    frame = lca.transit_factors(
        modes=["bus_bev", "bus_ice"],
        identities={"bus_bev": {"route_type": "3", "agency_id": "HSL"}},
    ).set_index("mode")
    assert frame.loc["bus_bev", "route_type"] == "3"
    assert frame.loc["bus_bev", "agency_id"] == "HSL"
    assert frame.loc["bus_ice", "route_type"] == ""
    assert frame.loc["bus_ice", "agency_id"] == ""


def test_identities_unknown_column_raises(lca):
    with pytest.raises(ValueError, match="unknown identity column"):
        lca.street_factors(identities={"private_bike": {"route_type": "3"}})


def test_wrong_domain_slug_raises(lca):
    with pytest.raises(ValueError, match="not a street mode"):
        lca.street_factors(modes=["bus_bev"])
    with pytest.raises(ValueError, match="not a transit mode"):
        lca.transit_factors(modes=["private_bike"])


def test_csv_schema_round_trip(lca):
    frame = lca.transit_factors(
        modes=["bus_bev", "bus_ice"],
        identities={"bus_bev": {"route_type": "0", "agency_id": "001"}},
    )
    reloaded = pd.read_csv(
        io.StringIO(frame.to_csv(index=False)),
        keep_default_na=False,
        dtype=READ_CSV_DTYPES,
    )
    assert list(reloaded.columns) == TRANSIT_COLUMNS
    # Leading-zero / numeric-looking identifiers stay strings, blanks stay "".
    row = reloaded.set_index("mode").loc["bus_bev"]
    assert row["route_type"] == "0"
    assert row["agency_id"] == "001"
    assert reloaded.set_index("mode").loc["bus_ice", "route_type"] == ""
    # Components and the total stay numeric.
    assert reloaded["vehicle"].dtype.kind == "f"
    assert reloaded["total"].dtype.kind == "f"
