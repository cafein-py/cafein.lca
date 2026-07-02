"""Stage 4: operational services (servicing-vehicle burden of shared fleets).

Mirrors the ``4_Operational_Services`` sheet; row references in comments.
"""

from ..config import conf


def run(params, data, use_energy, use_ghg):
    """Per-vehicle servicing energy [MJ] and GHG [g] (4_Op R15/R17)."""
    if params.service_km_per_vehicle_day == 0:
        return 0.0, 0.0
    daily_km = params.annual_km / 365  # R5 (3_Use R11)
    # R10: service-vehicle km per serviced-vehicle km.
    ratio = (params.service_km_per_vehicle_day
             / params.vehicles_per_service_trip / daily_km)
    lifetime_km = params.lifetime_km  # R6 (3_Use R12)

    if data.services_uses_intensity_table:
        # Micromobility branch: intensity of the servicing vehicle type
        # (helper table EI3:EV15 rows 12/15).
        energy_per_km, ghg_per_km = conf.service_vehicles[
            params.service_vehicle]
        return (energy_per_km * ratio * lifetime_km,
                ghg_per_km * ratio * lifetime_km)
    # Canonical branch: the mode's own use-phase burden scaled by the ratio.
    return use_energy * ratio, use_ghg * ratio
