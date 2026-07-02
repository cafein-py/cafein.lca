"""Stage 4: operational services (servicing-vehicle burden of shared fleets).

Mirrors the ``4_Operational_Services`` sheet; row references in comments.
Service-vehicle WTW intensities are computed from the session electricity mix
(helper table rows 10-15), exactly as the workbook derives them from its
default-region mix, so a custom power mix propagates to servicing EVs.
"""

from ..config import conf
from .use import electricity_factors


def service_vehicle_intensity(vehicle, session_mix):
    """WTW energy [MJ/km] and GHG [g/km] of a servicing vehicle type
    (helper rows 12 and 15)."""
    row = conf.service_vehicles[vehicle]
    fuel_mj = row["fuel_mj_per_km"]
    elec_mj = row["electricity_mj_per_km"]
    share = row["electric_share"]
    if not fuel_mj and not elec_mj:
        return 0.0, 0.0

    fuel_wtt = fuel_ghg_mj = 0.0
    if row["fuel"] in conf.fuel_ghg:  # BEVs list 'Electricity'; no fuel row
        wtw = conf.fuel_ghg[row["fuel"]]
        ttw = conf.fuel_ghg_ttw[row["fuel"]]
        fuel_wtt = wtw / ttw - 1                       # helper R10
        fuel_ghg_mj = (wtw / conf.constant("mj_per_l_gasoline_x100")
                       * 1000)                          # helper R13
    if row["low_carbon_electricity"]:
        # 'Van - BEV (low carbon)' pins renewables (EX12/EX14).
        paths = conf.electricity_pathways
        elec_wtt = paths["wtt_energy_factor"][-1] - 1
        elec_ghg_kwh = paths["ghg_g_per_kwh"][-1]
    else:
        elec_wtt, elec_ghg_kwh = electricity_factors(session_mix)  # EX11/EX13
    elec_ghg_mj = elec_ghg_kwh / conf.constant("mj_per_kwh")  # helper R14

    energy = (fuel_mj * (1 - share) * (1 + fuel_wtt)
              + share * elec_mj * (1 + elec_wtt))       # helper R12
    if share == 1:
        ghg = elec_mj * elec_ghg_mj                     # helper R15
    else:
        ghg = (fuel_mj * fuel_ghg_mj * (1 - share)
               + elec_mj * elec_ghg_mj * share)
    return energy, ghg


def run(params, data, use_energy, use_ghg, session_mix,
        ref_use_energy=None, ref_annual_km=None):
    """Per-vehicle servicing energy [MJ] and GHG [g] (4_Op R15/R17).

    ``ref_use_energy``/``ref_annual_km`` support the workbook columns whose
    servicing burden is taken from another mode column's use phase
    (audit item 5).
    """
    if params.service_km_per_vehicle_day == 0:
        return 0.0, 0.0
    annual_km = ref_annual_km if ref_annual_km is not None else params.annual_km
    daily_km = annual_km / 365  # R5 (3_Use R11)
    # R10: service-vehicle km per serviced-vehicle km.
    ratio = (params.service_km_per_vehicle_day
             / params.vehicles_per_service_trip / daily_km)
    lifetime_km = params.lifetime_km  # R6 (3_Use R12)

    if data.services_uses_intensity_table:
        # Micromobility branch: intensity of the servicing vehicle type.
        energy_per_km, ghg_per_km = service_vehicle_intensity(
            params.service_vehicle, session_mix)
        return (energy_per_km * ratio * lifetime_km,
                ghg_per_km * ratio * lifetime_km)
    # Canonical branch: use-phase burden scaled by the ratio.
    energy_base = ref_use_energy if ref_use_energy is not None else use_energy
    return energy_base * ratio, use_ghg * ratio
