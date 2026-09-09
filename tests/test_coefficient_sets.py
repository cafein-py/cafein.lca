"""Named coefficient sets: the packaged sets and their default."""

from cafein.lca.config import DEFAULT_COEFFICIENTS, available_coefficient_sets


def test_itf_2020_is_the_default_packaged_set():
    assert DEFAULT_COEFFICIENTS == "itf-2020"
    assert available_coefficient_sets() == ["itf-2020"]
