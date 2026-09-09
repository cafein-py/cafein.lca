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
