"""Consolidated regression tests. One test per fixed bug; add new ones here."""

from cafein_lca.config import conf


def test_battery_reference_scalar_extracted():
    # The battery-manufacturing reference capacity lives in 1_Manufacturing
    # column BT, not column D; extraction from D yielded an empty value and
    # broke every battery-equipped mode.
    assert conf.constant("battery_reference_kwh") > 0
