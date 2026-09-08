"""Stage 5: infrastructure network burden, amortized per vehicle-km.

Mirrors the ``5_Infrastructure`` sheet; row references in comments. Unlike
stages 1-4 this stage is natively per-vkm (the workbook defines no
per-vehicle infrastructure value).
"""

from ..config import conf


def _imputable_share(infra_type, params, rail_allocation):
    """Share of network energy imputable to this vehicle class (R69/R70)."""
    if not infra_type:
        return 0.0
    lookup = float(conf.infrastructure_types[infra_type]["energy_imputable_share"] or 0)
    if rail_allocation:
        return lookup
    ref_weight = conf.constant("reference_car_weight_kg")
    weight_term = (1 - lookup) * params.vehicle_weight_kg / ref_weight
    denominator = lookup + weight_term
    if denominator == 0:
        return 0.0
    return lookup / denominator


def _per_vkm(materials, lifetime, annual_use, infra_type, params, rail_allocation):
    """Per-vkm burden of one infrastructure type."""
    asphalt, cement, steel = materials
    absolute_use = lifetime * annual_use / 1e3  # R29/R30
    rec = conf.constant("infra_recycled_share_steel")

    energy_per_km = (  # R42/R43
        asphalt * conf.constant("infra_energy_asphalt_mj_per_kg")
        + cement * conf.constant("infra_energy_cement_mj_per_kg")
        + steel * (1 - rec) * conf.constant("infra_energy_virgin_steel_mj_per_kg")
        + steel * rec * conf.constant("infra_energy_recycled_steel_mj_per_kg")
    ) * 1000
    ghg_per_km = (
        (  # R65/R66
            asphalt * conf.constant("infra_ghg_asphalt_g_per_kg")
            + cement * conf.constant("infra_ghg_cement_g_per_kg")
            + steel * (1 - rec) * conf.constant("infra_ghg_virgin_steel_g_per_kg")
            + steel * rec * conf.constant("infra_ghg_recycled_steel_g_per_kg")
        )
        * 1000
        / 1e3
    )

    share = _imputable_share(infra_type, params, rail_allocation)
    # R50/R51 and R73/R74: the workbook DIVIDES by the share of network
    # energy imputable to materials, extrapolating the material burden to the
    # full network burden (reproduced verbatim; see the extraction audit).
    energy_alloc = energy_per_km / share if share else 0.0
    ghg_alloc = ghg_per_km / share if share else 0.0

    if not absolute_use:
        return 0.0, 0.0  # IFERROR -> 0
    return (
        energy_alloc / (absolute_use * 1e6),  # R54/R55
        ghg_alloc * 1000 / (absolute_use * 1e6),
    )  # R77/R78


def run(params, data):
    """Infrastructure energy [MJ/vkm] and GHG [g/vkm] (5_Infra R56/R79)."""
    e1, g1 = _per_vkm(
        data.infra1_materials,
        data.infra1_lifetime_years,
        data.infra1_annual_use_mvkm,
        data.infra1_type,
        params,
        data.infra_rail_allocation,
    )
    e2, g2 = _per_vkm(
        data.infra2_materials,
        data.infra2_lifetime_years,
        data.infra2_annual_use_mvkm,
        data.infra2_type,
        params,
        data.infra_rail_allocation,
    )
    share_1 = data.infra_share_1  # R7; R8 = 1 - R7
    return (
        e1 * share_1 + e2 * (1 - share_1),  # R56
        g1 * share_1 + g2 * (1 - share_1),
    )  # R79
