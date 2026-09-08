"""Typed mode-parameter objects (the scenario-input layer of the model).

Every field mirrors a shaded user-input cell of the workbook's ``0_Total``
sheet; defaults come from the mode registry (``cafein_lca.modes``). Instances
are immutable — derive scenario variants with :meth:`ModeParameters.replace`.
"""

import dataclasses


@dataclasses.dataclass(frozen=True)
class ModeParameters:
    """Scenario inputs for one transport mode (0_Total rows 4-24)."""

    slug: str
    name: str
    lifetime_years: float  # 0_Total R4
    annual_km: float  # 0_Total R5 (incl. cruising/overheading)
    vehicle_weight_kg: float  # 0_Total R10 (excl. battery)
    occupancy: float  # 0_Total R16 [pkm/vkm]
    electricity_region: str = None  # 0_Total R8; None = inherit session mix
    production_region: str = "Default"  # 0_Total R12
    battery_capacity_kwh: float = 0.0  # 0_Total R11
    battery_chemistry: str = ""  # 0_Total R13
    hydrogen_pathway: str = ""  # 0_Total R14
    fuel_type: str = ""  # 3_Use R14
    fuel_consumption_per_100km: float = 0.0  # 3_Use R3 [Lge/100km]
    electricity_consumption_kwh_per_km: float = 0.0  # 3_Use R4
    hydrogen_consumption_per_100km: float = 0.0  # 3_Use R5 [Lge/100km]
    electric_driving_share: float = 0.0  # 3_Use R6
    service_vehicle: str = "None"  # 0_Total R19
    service_km_per_vehicle_day: float = 0.0  # 0_Total R20
    vehicles_per_service_trip: float = 0.0  # 0_Total R21

    def __post_init__(self):
        for field in (
            "lifetime_years",
            "annual_km",
            "vehicle_weight_kg",
            "occupancy",
            "battery_capacity_kwh",
            "fuel_consumption_per_100km",
            "electricity_consumption_kwh_per_km",
            "hydrogen_consumption_per_100km",
            "service_km_per_vehicle_day",
            "vehicles_per_service_trip",
        ):
            value = getattr(self, field)
            if value < 0:
                raise ValueError(f"{field} must be >= 0, got {value!r}")
        if not 0 <= self.electric_driving_share <= 1:
            raise ValueError(
                "electric_driving_share must be within [0, 1], got "
                f"{self.electric_driving_share!r}"
            )

    def replace(self, **overrides):
        """Return a copy with the given scenario inputs replaced."""
        valid = {f.name for f in dataclasses.fields(self)}
        unknown = set(overrides) - valid
        if unknown:
            raise TypeError(
                f"unknown parameter(s) for mode '{self.slug}': "
                f"{', '.join(sorted(unknown))}. Valid parameters: "
                f"{', '.join(sorted(valid - {'slug', 'name'}))}"
            )
        return dataclasses.replace(self, **overrides)

    @property
    def lifetime_km(self) -> float:
        """Lifetime mileage before deadheading effects (0_Total R7)."""
        return self.lifetime_years * self.annual_km
