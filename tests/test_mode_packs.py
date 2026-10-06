"""Mode packs: modes from other sources layered on the coefficient set.

The fixture pack in tests/data/mode_packs/demo copies the metro mode (column
ED) at half its occupancy and puts it on its own track type with the metro
track's values, so its per-pkm result is exactly twice the metro's.
"""

import pathlib
import shutil

import pytest

from cafein.lca import TransportLCA, config, mode, mode_provenance
from cafein.lca import modes as modes_module
from cafein.lca.engine import delivery
from cafein.lca.export import STREET_MODES, TRANSIT_MODES

PACKS = pathlib.Path(__file__).parent / "data" / "mode_packs"


@pytest.fixture
def use_packs(monkeypatch):
    def use(directory):
        monkeypatch.setattr(config, "MODE_PACKS_DIR", directory)
        modes_module._reload_packs()

    yield use
    monkeypatch.undo()
    modes_module._reload_packs()


def test_pack_mode_joins_registry(use_packs):
    use_packs(PACKS)
    assert mode("demo_rail").occupancy == 95
    lca = TransportLCA()
    demo = lca.calculate("demo_rail")
    metro = lca.calculate("metro_urban_train")
    assert (demo.mode_source, metro.mode_source) == ("demo", "itf-2020")
    assert demo.per_pkm["total"] == pytest.approx(2 * metro.per_pkm["total"])
    provenance = mode_provenance("demo_rail")
    assert provenance["parameter"].tolist() == ["*", "occupancy", "Demo track: *"]
    assert provenance["year"].tolist()[0] == 2020


def test_packaged_tram_mode():
    row = TransportLCA().transit_factors(modes=["tram_light_rail"]).iloc[0]
    assert row["total"] > 0
    assert "tram_light_rail" in TRANSIT_MODES
    assert "tram_light_rail" not in STREET_MODES
    assert TransportLCA().calculate("tram_light_rail").mode_source == "rail-2026"
    sources = mode_provenance("tram_light_rail").set_index("parameter")["source"]
    assert sources["occupancy"].startswith("Siemens Mobility, Avenio EPD S-P-03441")
    # Delivery: 44 t over 500 km by combustion heavy truck (leg heavy_truck_a).
    params = mode("tram_light_rail")
    energy, _ = delivery.run(params, modes_module._data_for(params), 0.0)
    leg = config.DELIVERY_LEGS.index("heavy_truck_a")
    intensity = config.conf.delivery_legs["energy_mj_per_tkm"][leg]
    assert energy == pytest.approx(44.0 * 500 * intensity)


# (pack directory, file, old text, new text, when it fails, message)
REFUSALS = [
    ("demo", "manifest.toml", '"itf-2020"', '"other-set"', "load", "builds on"),
    ("demo", "manifest.toml", '"demo"', '"other"', "load", "differs from its"),
    ("itf-2020", "manifest.toml", '"demo"', '"itf-2020"', "load", "coefficient set"),
    ("demo", "modes.csv", "fluids_ghg_g,", "occupancy,", "load", "once each"),
    ("demo", "modes.csv", "Demo rail,", "Demo rail,x,", "load", "number of fields"),
    ("demo", "modes.csv", "demo_rail,", "metro_urban_train,", "import", "reuses"),
    ("demo", "modes.csv", "demo_rail,", "ED,", "import", "snake_case"),
    ("demo", "provenance.csv", ",note", ",comment", "load", "once each"),
    ("demo", "provenance.csv", "demo_rail,*", "other,*", "load", "unknown item"),
    ("demo", "provenance.csv", ",*,", ",fluids,", "load", "matches no column"),
    ("demo", "provenance.csv", "model_input", "guess", "load", "evidence must"),
    ("demo", "provenance.csv", "medium", "certain", "load", "confidence must"),
    ("demo", "provenance.csv", "itf-2020 column ED", " ", "load", "source is empty"),
    ("demo", "provenance.csv", ",2020,", ",c. 2020,", "load", "whole number"),
    (
        "demo",
        "infrastructure_types.csv",
        "Demo track,",
        "Demo track,0,",
        "load",
        "fields",
    ),
    ("demo", "provenance.csv", ",*,", ",occupancy,", "load", "no provenance"),
    ("demo", "modes.csv", ",Demo track,", ",Other track,", "load", "defined neither"),
    ("demo", "modes.csv", ",Demo track,", ",demo_rail,", "load", "defined neither"),
    ("demo", "infrastructure_types.csv", "Demo track,", "demo_rail,", "load", "both a"),
    (
        "demo",
        "provenance.csv",
        "Demo track,*",
        "Demo track,steel*",
        "load",
        "Demo track",
    ),
    (
        "demo",
        "infrastructure_types.csv",
        "Demo track",
        "Metro track",
        "load",
        "redefines infrastructure type",
    ),
]


@pytest.mark.parametrize("directory, file, old, new, when, match", REFUSALS)
def test_pack_refusals(use_packs, tmp_path, directory, file, old, new, when, match):
    shutil.copytree(PACKS / "demo", tmp_path / directory)
    path = tmp_path / directory / file
    path.write_text(path.read_text().replace(old, new, 1))
    if when == "import":
        with pytest.raises(ValueError, match=match):
            use_packs(tmp_path)
        return
    use_packs(tmp_path)
    with pytest.raises(ValueError, match=match):
        modes_module._registry()
