"""Integration checks for cafein.lca alongside the cafein routing package.

cafein.lca ships only the ``cafein/lca/`` subtree as a pkgutil-style namespace
portion; the ``cafein`` package ships ``cafein/__init__.py`` and extends the
namespace. These tests confirm the two coexist in one environment. They run
only when ``cafein`` is installed, which the CI integration job arranges by
installing ``cafein.lca[cafein]``; the regular test suite skips them.
"""

import pytest

import cafein

# ``import cafein`` alone always succeeds once cafein.lca is importable, because
# cafein/ is an implicit namespace directory. The routing package is the one
# that ships cafein/__init__.py, so a set __file__ is what distinguishes "cafein
# routing is installed" from "only the cafein.lca namespace is present".
if getattr(cafein, "__file__", None) is None:
    pytest.skip(
        "cafein routing package not installed; only the cafein.lca namespace",
        allow_module_level=True,
    )


def test_namespace_coexistence():
    import cafein.lca

    assert cafein.lca.__name__ == "cafein.lca"
    assert hasattr(cafein.lca, "TransportLCA")
    # cafein routing owns the top-level package and extends the namespace, so
    # cafein.lca resolves to the cafein/lca/ subtree without a collision.
    assert any("lca" in str(path) for path in cafein.lca.__path__)


def test_transport_lca_smoke():
    from cafein.lca import TransportLCA

    result = TransportLCA().calculate("private_car_bev")
    assert result.ghg_per_pkm > 0
    assert result.energy_per_pkm_total > 0


def test_cafein_consumes_exported_factors():
    # End-to-end: cafein loads the exported schema and honours the exported
    # basis. Runs against the real cafein factor loaders (cafein.emissions).
    import cafein.emissions as em
    from cafein.lca import TransportLCA
    from cafein.lca.export import COMPONENT_COLUMNS

    lca = TransportLCA()
    transit = lca.transit_factors(
        modes=["bus_bev"], identities={"bus_bev": {"route_type": "3"}}
    )
    street = lca.street_factors(
        modes=["private_car_bev", "private_bike"],
        identities={
            "private_car_bev": {
                "street_mode": "car",
                "vehicle_class": "BEV",
                "service_model": "private",
            },
            "private_bike": {
                "street_mode": "bicycle",
                "vehicle_class": "conventional",
                "service_model": "private",
            },
        },
    )

    # cafein 0.24.0 accepts and keeps the export/provenance columns.
    loaded_transit = em.load_factors(transit)
    loaded_street = em.load_street_factors(street)
    for frame in (loaded_transit, loaded_street):
        for column in ("mode", "basis", "scenario_sha256", "cafein_lca_version"):
            assert column in frame.columns

    # cafein honours the exported basis: the private-car row resolves as
    # vehicle-km (occupancy applied by the query surface), the bicycle row as
    # passenger-km, and the resolved factor is the row's component sum.
    car_factor, car_basis = em.street_factor_with_basis(
        "car", factors=street, vehicle_class="BEV"
    )
    assert car_basis == "vehicle_km"
    car_row = street.set_index("mode").loc["private_car_bev"]
    assert car_factor == pytest.approx(sum(car_row[c] for c in COMPONENT_COLUMNS))

    _, bike_basis = em.street_factor_with_basis("bicycle", factors=street)
    assert bike_basis == "passenger_km"
