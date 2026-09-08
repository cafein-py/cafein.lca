"""Per-stage unit tests with hand-checked workbook values.

One representative mode per stage; expected values are the cached results of
the corresponding stage-sheet output cells in the pristine workbook.
"""

import pytest

from cafein_lca.engine import delivery, infrastructure, manufacturing, services, use
from cafein_lca.lca import TransportLCA
from cafein_lca.modes import mode, _data_for


def _approx(value):
    return pytest.approx(value, rel=1e-9)


def test_manufacturing_private_escooter():
    # 1_Manufacturing!D140 / D142
    params = mode("private_escooter")
    energy, ghg = manufacturing.run(params, _data_for(params))
    assert energy == _approx(1888.1334352018316)
    assert ghg == _approx(163256.2238403705)


def test_manufacturing_shared_escooter():
    # 1_Manufacturing!W140 / W142
    params = mode("shared_escooter_first_gen")
    energy, ghg = manufacturing.run(params, _data_for(params))
    assert energy == _approx(1888.1334352018316)
    assert ghg == _approx(163256.2238403705)


def test_delivery_private_escooter():
    # 2_Transport!D82 / D108
    params = mode("private_escooter")
    data = _data_for(params)
    battery = manufacturing.battery_weight_kg(params)
    energy, ghg = delivery.run(params, data, battery)
    assert energy == _approx(105.07187074535572)
    assert ghg == _approx(9428.303541469148)


def test_use_private_escooter():
    # 3_Use!D43 / D45 (World electricity mix)
    params = mode("private_escooter")
    mix = TransportLCA()._mix_for(params)
    energy, ghg = use.run(params, mix)
    assert energy == _approx(640.588583814626)
    assert ghg == _approx(40926.11361427442)


def test_services_shared_escooter():
    # 4_Operational_Services!W15 / W17
    lca = TransportLCA()
    params = mode("shared_escooter_first_gen")
    data = _data_for(params)
    mix = lca._mix_for(params)
    use_energy, use_ghg = use.run(params, mix)
    energy, ghg = services.run(params, data, use_energy, use_ghg, lca._default_mix)
    assert energy == _approx(1211.0365091761366)
    assert ghg == _approx(83924.83008590626)


def test_service_vehicle_intensities_match_workbook():
    # Dynamic computation with the World mix must reproduce the workbook's
    # cached helper-table intensities (4_Op rows 12/15) for every type.
    from cafein_lca.config import conf

    world = conf.power_mix_catalog["World"]
    for vehicle, row in conf.service_vehicles.items():
        energy, ghg = services.service_vehicle_intensity(vehicle, world)
        assert energy == _approx(row["energy_mj_per_km_world"]) or (
            energy == 0 and row["energy_mj_per_km_world"] == 0
        )
        assert ghg == _approx(row["ghg_g_per_km_world"]) or (
            ghg == 0 and row["ghg_g_per_km_world"] == 0
        )


def test_services_zero_for_private_modes():
    params = mode("private_car_ice")
    energy, ghg = services.run(
        params, _data_for(params), 1e6, 1e6, TransportLCA()._default_mix
    )
    assert energy == 0 and ghg == 0


def test_infrastructure_metro():
    # 5_Infrastructure!ED56 / ED79 (per vkm)
    params = mode("metro_urban_train")
    energy_vkm, ghg_vkm = infrastructure.run(params, _data_for(params))
    assert energy_vkm == _approx(11.484770345320273)
    assert ghg_vkm == _approx(2090.6468081882867)
