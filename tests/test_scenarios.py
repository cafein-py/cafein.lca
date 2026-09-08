"""Scenario loading, validation and application through TransportLCA."""

import textwrap

import pandas as pd
import pytest

import cafein.lca
from cafein.lca import Scenario, TransportLCA, mode

TOML = textwrap.dedent("""
    name = "test"
    description = "three-case fixture"

    [power_mix]
    best = "100% solar, wind or hydro"
    central = "India"
    worst = {coal = 1.0}

    [modes."bus_*"]
    occupancy = {best = 92, central = 53, worst = 25}

    [modes.bus_ice]
    lifetime_years = 12

    [modes.bus_bev]
    occupancy = 40

    [modes.bus_bev.lifetime_years]
    value = 10
    evidence = "assumption"
    source = {best = "a", central = "b", worst = "c"}
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
        ("central", 53, "India"),
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
        == "abc"[("best", "central", "worst").index(case)]
    )
    assert prov.loc[("bus_bev", "lifetime_years"), "evidence"] == "assumption"
    assert pd.isna(prov.loc[("bus_ice", "occupancy"), "evidence"])
    assert s.parameters("bus_hev").lifetime_years == mode("bus_hev").lifetime_years
    assert s.parameters("private_car_ice") == mode("private_car_ice")


@pytest.mark.parametrize(
    "body,case,error",
    [
        ("[modes.no_such_mode]\noccupancy = 2", "central", KeyError),
        ('[modes."tram_*"]\noccupancy = 2', "central", KeyError),
        ("[modes.bus_ice]\nseats = 2", "central", TypeError),
        ("[modes.bus_ice]\noccupancy = -1", "central", ValueError),
        ("[modes.bus_ice]\noccupancy = {best = 1, central = 2}", "central", ValueError),
        ("[modes.bus_ice]\noccupancy = 2", "typical", ValueError),
        ("modes = 3", "central", AttributeError),
        ("colour = 'red'", "central", ValueError),
        (
            "[modes.bus_ice.occupancy]\nvalue = 2\nevidence = 'guess'",
            "central",
            ValueError,
        ),
        (
            "[modes.bus_ice.occupancy]\nvalue = 2\nconfidence = 'ok'",
            "central",
            ValueError,
        ),
        ("[modes.bus_ice.occupancy]\nvalue = 2\nbest = 3", "central", ValueError),
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
        for case in ("best", "central", "worst")
    }
    # cases are named by their effect on emissions per pkm
    assert (results["best"] <= results["central"] + 1e-9).all()
    assert (results["central"] <= results["worst"] + 1e-9).all()


def test_list_and_locate_packaged_scenarios():
    assert set(cafein.lca.list_scenarios()) == {"india_metropolitan", "finland_2020"}
    finland = Scenario.load("finland_2020")
    assert finland.overrides == {} and finland.power_mix["nuclear"] > 0.3
    india = Scenario.load("india_metropolitan").provenance()
    assert india["evidence"].notna().all() and india["source"].notna().all()
    with pytest.raises(FileNotFoundError):
        Scenario.load("atlantis")
