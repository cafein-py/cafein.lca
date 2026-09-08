"""Scenario loading, validation and application through TransportLCA."""

import textwrap

import pytest

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
