"""Stage 1: vehicle + battery manufacturing, assembly, disposal and fluids.

Mirrors the ``1_Manufacturing`` sheet; row references in comments.
"""

from ..config import MATERIALS, conf


def battery_weight_kg(params):
    """Battery weight [kg] = capacity / specific energy (1_Mfg R31)."""
    if not params.battery_capacity_kwh or not params.battery_chemistry:
        return 0.0
    spec = float(conf.battery_chemistries[params.battery_chemistry]
                 ["specific_energy_kwh_per_kg"])
    return params.battery_capacity_kwh / spec


def _materials_burden(params, data, metric):
    """Material production burden of the vehicle body (1_Mfg R67 / R115)."""
    w = params.vehicle_weight_kg
    region = params.production_region
    shares = dict(zip(MATERIALS, data.material_shares))
    recycled = {
        "steel": conf.constant("recycled_share_steel"),
        "wrought_aluminum": conf.constant("recycled_share_wrought_aluminum"),
        "cast_aluminum": conf.constant("recycled_share_cast_aluminum"),
    }
    total = 0.0
    for material, share in shares.items():
        if material in recycled:
            rec = recycled[material]
            virgin = conf.material_intensity(
                f"virgin_{material}", region, metric)
            recyc = conf.material_intensity(
                f"recycled_{material}", region, metric)
            total += w * share * ((1 - rec) * virgin + rec * recyc)
        else:
            total += w * share * conf.material_intensity(
                material, region, metric)
    return total


def _battery_intensity(params, metric):
    """Battery manufacturing + assembly + disposal per kWh (1_Mfg R61-63 /
    R109-111)."""
    chem = params.battery_chemistry
    if not chem:
        return 0.0
    row = conf.battery_chemistries[chem]
    suffix = ("coal_al" if params.production_region ==
              "With Al smelting mostly form coal" else "default")
    if metric == "energy":
        mfg = (float(row[f"mfg_energy_mmbtu_{suffix}"])
               * conf.constant("mj_per_mmbtu")
               / conf.constant("battery_reference_kwh"))
        assembly = conf.constant("battery_assembly_energy_mj_per_kwh")
        spec = float(row["specific_energy_kwh_per_kg"])
        disposal = conf.constant("battery_disposal_energy_mj_per_kg") / spec
    else:
        mfg = (float(row[f"mfg_ghg_g_{suffix}"])
               / conf.constant("battery_reference_kwh"))
        assembly = conf.constant("battery_assembly_ghg_g_per_kwh")
        spec = float(row["specific_energy_kwh_per_kg"])
        disposal = conf.constant("battery_disposal_ghg_g_per_kg") / spec
    return mfg + assembly + disposal


def _fluids(params, data):
    """Fluids burden per vehicle (1_Mfg R135/R137); scales with vehicle weight
    for the modes whose workbook column does."""
    scale = 1.0
    if data.fluids_weight_scaled and data.default_weight_kg:
        scale = params.vehicle_weight_kg / data.default_weight_kg
    return data.fluids_energy_mj * scale, data.fluids_ghg_g * scale


def run(params, data):
    """Per-vehicle manufacturing energy [MJ] and GHG [g] (1_Mfg R140/R142)."""
    w = params.vehicle_weight_kg
    region = params.production_region
    replacements = 1 + data.battery_replacements  # R73-75/R121-123 factor
    cap = params.battery_capacity_kwh
    fluids_energy, fluids_ghg = _fluids(params, data)

    energy = (
        _materials_burden(params, data, "energy")                    # R67
        + conf.assembly_disposal_intensity("assembly", region, "energy") * w
        + conf.assembly_disposal_intensity("disposal", region, "energy") * w
        + _battery_intensity(params, "energy") * cap * replacements  # R76
        + fluids_energy                                              # R140
    )
    ghg = (
        _materials_burden(params, data, "ghg")                       # R115
        + conf.assembly_disposal_intensity("assembly", region, "ghg") * w
        + conf.assembly_disposal_intensity("disposal", region, "ghg") * w
        + _battery_intensity(params, "ghg") * cap * replacements     # R124
        + fluids_ghg                                                 # R142
    )
    return energy, ghg
