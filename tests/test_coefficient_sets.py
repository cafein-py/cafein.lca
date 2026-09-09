"""Named coefficient sets: the packaged sets, their default, and selection."""

import pytest

from cafein.lca import Scenario, TransportLCA, available_coefficient_sets
from cafein.lca.config import DEFAULT_COEFFICIENTS


def test_itf_2020_is_the_default_packaged_set():
    assert DEFAULT_COEFFICIENTS == "itf-2020"
    assert available_coefficient_sets() == ["itf-2020"]


def test_default_session_uses_itf_2020():
    lca = TransportLCA()
    assert lca.coefficients == "itf-2020"
    assert lca.calculate("private_car_bev").coefficient_set == "itf-2020"


def test_unknown_coefficient_set_raises():
    with pytest.raises(KeyError, match="itf-2020"):
        TransportLCA(coefficients="does-not-exist")


def test_scenario_coefficients_key_used_when_argument_omitted():
    # Only itf-2020 ships, so a deliberately invalid name in the scenario is
    # what proves the omitted-argument path resolved the scenario's key.
    scenario = Scenario(name="t", coefficients="from-scenario")
    with pytest.raises(KeyError, match="from-scenario"):
        TransportLCA(scenario=scenario)


def test_explicit_coefficients_override_scenario_key():
    scenario = Scenario(name="t", coefficients="from-scenario")
    assert TransportLCA(scenario=scenario, coefficients="itf-2020").coefficients == (
        "itf-2020"
    )


def test_scenario_file_coefficients_key_is_parsed(tmp_path):
    path = tmp_path / "s.toml"
    path.write_text('name = "s"\ncoefficients = "itf-2020"\n', encoding="utf-8")
    assert Scenario.load(path).coefficients == "itf-2020"
