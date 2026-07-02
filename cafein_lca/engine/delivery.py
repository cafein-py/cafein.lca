"""Stage 2: vehicle delivery from factory to point of purchase.

Mirrors the ``2_Transport`` sheet; row references in comments.
"""

from ..config import conf


def run(params, data, battery_weight):
    """Per-vehicle delivery energy [MJ] and GHG [g] (2_Transport R82/R108)."""
    if data.delivery_weight_computed:
        weight = params.vehicle_weight_kg + battery_weight  # R3 canonical
    else:
        weight = data.delivery_weight_kg  # bespoke micromobility columns

    legs = conf.delivery_legs
    # R20-29: tkm per leg; R72-81: energy per leg.
    leg_energy = [
        weight / 1e3 * km * intensity
        for km, intensity in zip(data.delivery_km, legs["energy_mj_per_tkm"])
    ]
    energy = sum(leg_energy)

    # R98-107: GHG per leg. The workbook drops leg 9 (medium truck b): its
    # row multiplies two empty cells, so the contribution is always 0
    # (reproduced verbatim; see the extraction audit).
    ghg_factors = legs["ghg_g_per_mj"]
    ghg = sum(leg_energy[i] * ghg_factors[i] for i in range(8))
    ghg += leg_energy[9] * ghg_factors[9]
    return energy, ghg
