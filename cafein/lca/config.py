"""Packaged assumption datasets (the environment layer of the model).

Loads the CSVs under ``cafein/lca/data/`` (extracted from the ITF workbook by
``scripts/extract_workbook.py``) into plain dictionaries, lazily and once.
"""

import csv
import functools
import pathlib

DATA_DIR = pathlib.Path(__file__).parent / "data"

POWER_SOURCES = ["oil", "natural_gas", "coal", "nuclear", "biomass", "other_renewables"]
MATERIALS = [
    "steel",
    "stainless_steel",
    "cast_iron",
    "wrought_aluminum",
    "cast_aluminum",
    "copper_brass",
    "glass",
    "plastics",
    "carbon_fiber",
    "rubber",
    "others",
]
DELIVERY_LEGS = [
    "air",
    "ship",
    "train_a",
    "train_b",
    "heavy_truck_a",
    "heavy_truck_b",
    "medium_truck_a",
    "medium_truck_b",
    "van_a",
    "van_b",
]

# 0_Total R12 / 1_Manufacturing helper row 37 region labels -> CSV suffix.
PRODUCTION_REGIONS = {
    "With Al smelting mostly form coal": "coal_al",
    "Default": "default",
}


def _read(name):
    with open(DATA_DIR / name, newline="") as f:
        return list(csv.DictReader(f))


def _num(value):
    if value in (None, ""):
        return 0.0
    return float(value)


class _Conf:
    """Namespace of packaged datasets, loaded on first attribute access."""

    @functools.cached_property
    def power_mix_catalog(self):
        return {
            r["region"]: [_num(r[s]) for s in POWER_SOURCES]
            for r in _read("power_gen_mix.csv")
        }

    @functools.cached_property
    def electricity_pathways(self):
        rows = _read("electricity_pathways.csv")
        return {
            "wtt_energy_factor": [_num(r["wtt_energy_factor"]) for r in rows],
            "ghg_g_per_kwh": [_num(r["ghg_g_per_kwh"]) for r in rows],
        }

    @functools.cached_property
    def fuel_wtt_energy(self):
        return {
            r["fuel"]: _num(r["wtt_energy_factor"])
            for r in _read("fuel_wtt_energy.csv")
        }

    @functools.cached_property
    def fuel_ghg(self):
        return {r["fuel"]: _num(r["ghg_wtw_g_per_l"]) for r in _read("fuel_ghg.csv")}

    @functools.cached_property
    def hydrogen_pathways(self):
        rows = _read("hydrogen_pathways.csv")
        named = {
            r["pathway"]: (_num(r["wtt_energy_factor"]), _num(r["ghg_g_per_mj"]))
            for r in rows
        }
        # Rows 2-7 of the workbook table are the per-power-source electrolysis
        # factors, in POWER_SOURCES order (3_Use R29/R33 SUMPRODUCT).
        per_source = rows[1:7]
        return {
            "named": named,
            "electrolysis_energy": [_num(r["wtt_energy_factor"]) for r in per_source],
            "electrolysis_ghg": [_num(r["ghg_g_per_mj"]) for r in per_source],
        }

    @functools.cached_property
    def material_intensities(self):
        return {r["material"]: r for r in _read("material_intensities.csv")}

    @functools.cached_property
    def assembly_disposal(self):
        return {r["step"]: r for r in _read("assembly_disposal_intensities.csv")}

    @functools.cached_property
    def battery_chemistries(self):
        return {r["chemistry"]: r for r in _read("battery_chemistries.csv")}

    @functools.cached_property
    def delivery_legs(self):
        rows = {r["leg"]: r for r in _read("delivery_legs.csv")}
        return {
            "energy_mj_per_tkm": [
                _num(rows[leg]["energy_mj_per_tkm"]) for leg in DELIVERY_LEGS
            ],
            "ghg_g_per_mj": [_num(rows[leg]["ghg_g_per_mj"]) for leg in DELIVERY_LEGS],
        }

    @functools.cached_property
    def service_vehicles(self):
        return {
            r["vehicle"]: {
                "fuel_mj_per_km": _num(r["fuel_mj_per_km"]),
                "electricity_mj_per_km": _num(r["electricity_mj_per_km"]),
                "fuel": r["fuel"],
                "electric_share": _num(r["electric_share"]),
                "low_carbon_electricity": r["low_carbon_electricity"] == "1",
                "energy_mj_per_km_world": _num(r["energy_mj_per_km_world"]),
                "ghg_g_per_km_world": _num(r["ghg_g_per_km_world"]),
            }
            for r in _read("service_vehicles.csv")
        }

    @functools.cached_property
    def fuel_ghg_ttw(self):
        return {r["fuel"]: _num(r["ghg_ttw_g_per_l"]) for r in _read("fuel_ghg.csv")}

    @functools.cached_property
    def infrastructure_types(self):
        return {r["infrastructure"]: r for r in _read("infrastructure_types.csv")}

    @functools.cached_property
    def constants(self):
        return {r["name"]: r["value"] for r in _read("constants.csv")}

    def constant(self, name):
        return float(self.constants[name])

    def material_intensity(self, material, production_region, metric):
        """Energy [MJ/kg] or GHG [g/kg] of material production (1_Mfg R38-51,
        R86-99)."""
        suffix = PRODUCTION_REGIONS[production_region]
        unit = "mj_per_kg" if metric == "energy" else "g_per_kg"
        return _num(self.material_intensities[material][f"{metric}_{unit}_{suffix}"])

    def assembly_disposal_intensity(self, step, production_region, metric):
        """Vehicle assembly/disposal intensity per kg (1_Mfg R55-56/R103-104)."""
        suffix = PRODUCTION_REGIONS[production_region]
        unit = "mj_per_kg" if metric == "energy" else "g_per_kg"
        return _num(self.assembly_disposal[step][f"{metric}_{unit}_{suffix}"])


conf = _Conf()
