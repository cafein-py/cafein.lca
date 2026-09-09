"""Scenario loading, validation and application through TransportLCA."""

import textwrap

import pandas as pd
import pytest

import cafein.lca
from cafein.lca import Scenario, TransportLCA, mode

from scenario_helpers import assert_provenance_complete

TOML = textwrap.dedent("""
    name = "test"
    description = "three-case fixture"

    [power_mix]
    best = "100% solar, wind or hydro"
    middle = "India"
    worst = {coal = 1.0}

    [modes."bus_*"]
    occupancy = {best = 92, middle = 53, worst = 25}

    [modes.bus_ice]
    lifetime_years = 12

    [modes.bus_bev]
    occupancy = 40

    [modes.bus_bev.lifetime_years]
    value = 10
    evidence = "assumption"
    source = {best = "a", middle = "b", worst = "c"}
    year = {best = 2019, middle = 2020, worst = 2021}
    confidence = "low"
    """)


@pytest.fixture(scope="module")
def toml_path(tmp_path_factory):
    path = tmp_path_factory.mktemp("scenario") / "test.toml"
    path.write_text(TOML)
    return path


@pytest.mark.parametrize(
    "case,occupancy,power_mix",
    [
        ("best", 92, "100% solar, wind or hydro"),
        ("middle", 53, "India"),
        ("worst", 25, {"coal": 1.0}),
    ],
)
def test_load_resolves_cases_patterns_and_precedence(
    toml_path, case, occupancy, power_mix
):
    s = Scenario.load(toml_path, case=case)
    assert (s.name, s.case, s.power_mix) == ("test", case, power_mix)
    bus = s.parameters("bus_ice")
    assert (bus.occupancy, bus.lifetime_years) == (occupancy, 12)
    assert s.parameters("bus_bev").occupancy == 40  # exact slug wins over glob
    assert s.parameters("bus_bev").lifetime_years == 10
    prov = s.provenance().set_index(["mode", "parameter"])
    assert (
        prov.loc[("bus_bev", "lifetime_years"), "source"]
        == "abc"[("best", "middle", "worst").index(case)]
    )
    assert (
        prov.loc[("bus_bev", "lifetime_years"), "year"]
        == (2019, 2020, 2021)[("best", "middle", "worst").index(case)]
    )
    assert prov.loc[("bus_bev", "lifetime_years"), "evidence"] == "assumption"
    assert pd.isna(prov.loc[("bus_ice", "occupancy"), "evidence"])
    assert s.parameters("bus_hev").lifetime_years == mode("bus_hev").lifetime_years
    assert s.parameters("private_car_ice") == mode("private_car_ice")


@pytest.mark.parametrize(
    "body,case,error",
    [
        ("[modes.no_such_mode]\noccupancy = 2", "middle", KeyError),
        ('[modes."tram_*"]\noccupancy = 2', "middle", KeyError),
        ("[modes.bus_ice]\nseats = 2", "middle", TypeError),
        ("[modes.bus_ice]\noccupancy = -1", "middle", ValueError),
        ("[modes.bus_ice]\noccupancy = {best = 1, middle = 2}", "middle", ValueError),
        ("[modes.bus_ice]\noccupancy = 2", "typical", ValueError),
        ("modes = 3", "middle", AttributeError),
        ("colour = 'red'", "middle", ValueError),
        (
            "[modes.bus_ice.occupancy]\nvalue = 2\nevidence = 'guess'",
            "middle",
            ValueError,
        ),
        (
            "[modes.bus_ice.occupancy]\nvalue = 2\nconfidence = 'ok'",
            "middle",
            ValueError,
        ),
        ("[modes.bus_ice.occupancy]\nvalue = 2\nbest = 3", "middle", ValueError),
    ],
)
def test_load_rejects_invalid_scenarios(tmp_path, body, case, error):
    path = tmp_path / "bad.toml"
    path.write_text(body + "\n")
    with pytest.raises(error):
        Scenario.load(path, case=case)


def test_session_applies_scenario_before_keyword_overrides(toml_path):
    scenario = Scenario.load(toml_path)
    lca = TransportLCA(scenario=scenario)
    reference = TransportLCA(power_mix="India")
    expected = reference.calculate("bus_ice", occupancy=53, lifetime_years=12)
    assert lca.power_mix == "India"
    assert lca.parameters("bus_ice") == expected.parameters
    assert lca.calculate("bus_ice").ghg_per_pkm == expected.ghg_per_pkm
    assert lca.summary().loc["bus_ice", "total"] == expected.ghg_per_pkm
    # keyword overrides win over the scenario
    assert lca.calculate("bus_ice", occupancy=10).parameters.occupancy == 10
    # a ModeParameters object is used as given
    assert lca.calculate(mode("bus_ice")).parameters == mode("bus_ice")
    # an explicit power mix wins over the scenario's
    assert TransportLCA(power_mix="EU 28", scenario=scenario).power_mix == "EU 28"


@pytest.mark.parametrize("name", ["india_metropolitan", "finland_2020"])
def test_packaged_scenarios_load_and_order_cases(name):
    results = {
        case: TransportLCA(scenario=Scenario.load(name, case=case)).summary()["total"]
        for case in ("best", "middle", "worst")
    }
    # cases are named by their effect on emissions per pkm
    assert (results["best"] <= results["middle"] + 1e-9).all()
    assert (results["middle"] <= results["worst"] + 1e-9).all()


def test_list_and_locate_packaged_scenarios():
    assert set(cafein.lca.list_scenarios()) == {"india_metropolitan", "finland_2020"}
    finland = Scenario.load("finland_2020")
    assert finland.overrides == {} and finland.power_mix["nuclear"] > 0.3
    india = Scenario.load("india_metropolitan").provenance()
    assert india["evidence"].notna().all() and india["source"].notna().all()
    with pytest.raises(FileNotFoundError):
        Scenario.load("atlantis")


_COMPLETE_OVERRIDE = """
    [modes.bus_ice.occupancy]
    value = 40
    evidence = "observed"
    geography = "test city"
    source = "operator report"
    year = 2010
    confidence = "high"
    note = "boundary year is allowed"
"""


@pytest.mark.parametrize(
    "override,complete",
    [
        (_COMPLETE_OVERRIDE, True),
        (_COMPLETE_OVERRIDE.replace("year = 2010", "year = 2009"), False),
        (_COMPLETE_OVERRIDE.replace("    year = 2010\n", ""), False),
        (_COMPLETE_OVERRIDE.replace("year = 2010", 'year = "2010"'), False),
        (_COMPLETE_OVERRIDE.replace("year = 2010", "year = inf"), False),
        (
            _COMPLETE_OVERRIDE.replace('source = "operator report"', 'source = ""'),
            False,
        ),
        (
            _COMPLETE_OVERRIDE.replace('    note = "boundary year is allowed"\n', ""),
            False,
        ),
        ("[modes.bus_ice]\noccupancy = 40\n", False),
    ],
)
def test_provenance_completeness_helper(tmp_path, override, complete):
    path = tmp_path / "s.toml"
    path.write_text('name = "s"\n' + textwrap.dedent(override))
    scenario = Scenario.load(path)
    if complete:
        assert_provenance_complete(scenario)
    else:
        with pytest.raises(AssertionError):
            assert_provenance_complete(scenario)
