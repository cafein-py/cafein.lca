"""Stage 3: well-to-wheel fuel, electricity and hydrogen use.

Mirrors the ``3_Use`` sheet; row references in comments.
"""

from ..config import conf

# The workbook's sentinel for grid-mix electrolysis, typo included
# (WTW_Fuel_properties!C64).
_ELECTROLYSIS = "Electroysis (Global power mix)"


def electricity_factors(mix_shares):
    """WTT energy factor (R28) and GHG intensity g/kWh (R32) for a mix."""
    paths = conf.electricity_pathways
    wtt = sum(s * f for s, f in zip(mix_shares, paths["wtt_energy_factor"])) - 1
    ghg = sum(s * g for s, g in zip(mix_shares, paths["ghg_g_per_kwh"]))
    return wtt, ghg


def _hydrogen_factors(pathway, mix_shares):
    """WTT energy factor (R29) and GHG g/MJ (R33) of hydrogen production."""
    h2 = conf.hydrogen_pathways
    if pathway == _ELECTROLYSIS:
        energy = sum(s * f for s, f in zip(mix_shares, h2["electrolysis_energy"]))
        ghg = sum(s * g for s, g in zip(mix_shares, h2["electrolysis_ghg"]))
        return energy, ghg
    return h2["named"][pathway]


def run(params, mix_shares):
    """Per-vehicle use-phase energy [MJ] and GHG [g] (3_Use R43/R45)."""
    mj_per_l = conf.constant("mj_per_l_gasoline_x100")
    mj_per_kwh = conf.constant("mj_per_kwh")

    # TTW energy intensities per km (R35-37).
    fuel_mj = params.fuel_consumption_per_100km * mj_per_l / 100
    elec_mj = params.electricity_consumption_kwh_per_km * mj_per_kwh
    h2_mj = params.hydrogen_consumption_per_100km * mj_per_l / 100
    share = params.electric_driving_share  # R6

    elec_wtt, elec_ghg_kwh = electricity_factors(mix_shares)  # R28/R32
    fuel_wtt = conf.fuel_wtt_energy.get(params.fuel_type, 0.0)  # R27
    fuel_ghg_l = conf.fuel_ghg.get(params.fuel_type, 0.0)  # R31
    h2_wtt = h2_ghg = 0.0
    if params.hydrogen_pathway:
        h2_wtt, h2_ghg = _hydrogen_factors(
            params.hydrogen_pathway, mix_shares
        )  # R29/R33

    fuel_ghg_mj = fuel_ghg_l / mj_per_l * 1000  # R40
    elec_ghg_mj = elec_ghg_kwh / mj_per_kwh  # R41
    km = params.lifetime_km  # R12

    energy = km * (  # R43
        (0.0 if fuel_mj == 0 else (1 + fuel_wtt) * fuel_mj * (1 - share))
        + (0.0 if h2_mj == 0 else (1 + h2_wtt) * h2_mj * (1 - share))
        + (1 + elec_wtt) * elec_mj * share
    )
    ghg = km * (  # R45
        (0.0 if fuel_mj == 0 else fuel_ghg_mj * fuel_mj * (1 - share))
        + (0.0 if h2_mj == 0 else h2_ghg * h2_mj * (1 - share))
        + elec_mj * elec_ghg_mj * share
    )
    return energy, ghg
