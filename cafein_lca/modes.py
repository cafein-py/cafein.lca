"""Mode registry: canonical slugs -> default parameters and mode data.

``modes.csv`` holds one row per workbook mode column (all 130, including the
sensitivity variants used as golden-test fixtures). The public registry maps
snake_case slugs to the canonical columns; variants stay reachable through
:func:`_mode_by_column` for the test suite.
"""

import csv
import dataclasses
import functools
import pathlib

from .config import DELIVERY_LEGS, MATERIALS
from .parameters import ModeParameters

_MODES_CSV = pathlib.Path(__file__).parent / "data" / "modes.csv"

#: slug -> workbook column of the canonical central case.
CANONICAL_MODES = {
    "private_escooter": "D",
    "shared_escooter_first_gen": "W",
    "shared_escooter_new_gen": "AE",
    "private_bike": "AG",
    "private_ebike": "AH",
    "shared_bike": "AI",
    "shared_ebike": "AJ",
    "private_moped_ice": "AK",
    "private_moped_bev": "AL",
    "shared_moped_ice": "AM",
    "shared_moped_bev": "AN",
    "private_car_ice": "AO",
    "private_car_hev": "AP",
    "private_car_phev": "AQ",
    "private_car_bev": "AX",
    "private_car_fcev": "BB",
    "ridesourcing_car_ice": "BI",
    "ridesourcing_car_hev": "BJ",
    "ridesourcing_car_phev": "BK",
    "ridesourcing_car_bev": "BT",
    "ridesourcing_car_bev_two_packs": "CC",
    "ridesourcing_car_fcev": "CG",
    "taxi_ice": "CH",
    "taxi_hev": "CI",
    "taxi_phev": "CJ",
    "taxi_bev": "CK",
    "taxi_bev_two_packs": "CL",
    "taxi_fcev": "CM",
    "large_private_car_ice": "CN",
    "large_private_car_hev": "CO",
    "large_private_car_phev": "CP",
    "large_private_car_bev": "CQ",
    "large_private_car_fcev": "CR",
    "ridesourcing_large_car_ice": "CS",
    "ridesourcing_large_car_hev": "CT",
    "ridesourcing_large_car_phev": "CU",
    "ridesourcing_large_car_bev": "CV",
    "ridesourcing_large_car_bev_two_packs": "CW",
    "ridesourcing_large_car_fcev": "CX",
    "ridesourcing_shared_van_ice": "CY",
    "ridesourcing_shared_van_hev": "CZ",
    "ridesourcing_shared_van_phev": "DA",
    "ridesourcing_shared_van_bev": "DB",
    "ridesourcing_shared_van_bev_two_packs": "DC",
    "ridesourcing_shared_van_fcev": "DD",
    "ridesourcing_shared_minibus_ice": "DE",
    "ridesourcing_shared_minibus_hev": "DF",
    "ridesourcing_shared_minibus_bev": "DH",
    "ridesourcing_shared_minibus_bev_two_packs": "DI",
    "ridesourcing_shared_minibus_fcev": "DJ",
    "bus_ice": "DQ",
    "bus_hev": "DR",
    "bus_bev": "DU",
    "bus_bev_two_packs": "DT",
    "bus_fcev": "DW",
    "metro_urban_train": "ED",
}

#: The workbook's session-default electricity region; modes assigned to it
#: inherit the TransportLCA power mix (plan section 7 precedence rule).
DEFAULT_REGION = "World"


@dataclasses.dataclass(frozen=True)
class ModeData:
    """Per-mode leaf data extracted from the workbook (not user parameters)."""

    column: str
    name: str
    default_weight_kg: float
    material_shares: tuple  # 1_Manufacturing R8-R18
    battery_replacements: float  # 1_Manufacturing R34
    fluids_energy_mj: float  # 1_Manufacturing R135
    fluids_ghg_g: float  # 1_Manufacturing R137
    fluids_weight_scaled: bool
    delivery_weight_computed: bool  # 2_Transport R3 canonical formula?
    delivery_weight_kg: float
    delivery_km: tuple  # 2_Transport R7-R16 (10 legs)
    services_uses_intensity_table: bool  # 4_Op R15 branch
    services_ref_column: str  # 4_Op R15 use-phase source (audit #5)
    infra_category: str  # 5_Infrastructure R3
    infra1_type: str
    infra2_type: str
    infra1_materials: tuple  # (asphalt, cement, steel) t/km
    infra2_materials: tuple
    infra1_lifetime_years: float
    infra2_lifetime_years: float
    infra1_annual_use_mvkm: float
    infra2_annual_use_mvkm: float
    infra_share_1: float  # 5_Infrastructure R7
    infra_rail_allocation: bool  # rail block: plain VLOOKUP share


def _num(value):
    if value in (None, ""):
        return 0.0
    return float(value)


def _slugify_column(column, name):
    for slug, col in CANONICAL_MODES.items():
        if col == column:
            return slug
    return f"_column_{column}"


@functools.lru_cache(maxsize=1)
def _registry():
    registry = {}
    with open(_MODES_CSV, newline="") as f:
        for r in csv.DictReader(f):
            column, name = r["column"], r["name"]
            slug = _slugify_column(column, name)
            region = r["electricity_region"]
            params = ModeParameters(
                slug=slug,
                name=name,
                lifetime_years=_num(r["lifetime_years"]),
                annual_km=_num(r["annual_km"]),
                vehicle_weight_kg=_num(r["vehicle_weight_kg"]),
                occupancy=_num(r["occupancy"]),
                electricity_region=None if region == DEFAULT_REGION else region,
                production_region=r["production_region"] or "Default",
                battery_capacity_kwh=_num(r["battery_capacity_kwh"]),
                battery_chemistry=r["battery_chemistry"],
                hydrogen_pathway=r["hydrogen_pathway"],
                fuel_type=r["fuel_type"],
                fuel_consumption_per_100km=_num(r["fuel_consumption_per_100km"]),
                electricity_consumption_kwh_per_km=_num(
                    r["electricity_consumption_kwh_per_km"]
                ),
                hydrogen_consumption_per_100km=_num(
                    r["hydrogen_consumption_per_100km"]
                ),
                electric_driving_share=_num(r["electric_driving_share"]),
                service_vehicle=r["service_vehicle"] or "None",
                service_km_per_vehicle_day=_num(r["service_km_per_vehicle_day"]),
                vehicles_per_service_trip=_num(r["vehicles_per_service_trip"]),
            )
            data = ModeData(
                column=column,
                name=name,
                default_weight_kg=_num(r["vehicle_weight_kg"]),
                material_shares=tuple(_num(r[f"share_{m}"]) for m in MATERIALS),
                battery_replacements=_num(r["battery_replacements"]),
                fluids_energy_mj=_num(r["fluids_energy_mj"]),
                fluids_ghg_g=_num(r["fluids_ghg_g"]),
                fluids_weight_scaled=r["fluids_weight_scaled"] == "1",
                delivery_weight_computed=r["delivery_weight_computed"] == "1",
                delivery_weight_kg=_num(r["delivery_weight_kg"]),
                delivery_km=tuple(
                    _num(r[f"delivery_km_{leg}"]) for leg in DELIVERY_LEGS
                ),
                services_uses_intensity_table=(
                    r["services_uses_intensity_table"] == "1"
                ),
                services_ref_column=r["services_ref_column"],
                infra_category=r["infra_category"],
                infra1_type=r["infra1_type"],
                infra2_type=r["infra2_type"],
                infra1_materials=(
                    _num(r["infra1_asphalt_t_per_km"]),
                    _num(r["infra1_cement_t_per_km"]),
                    _num(r["infra1_steel_t_per_km"]),
                ),
                infra2_materials=(
                    _num(r["infra2_asphalt_t_per_km"]),
                    _num(r["infra2_cement_t_per_km"]),
                    _num(r["infra2_steel_t_per_km"]),
                ),
                infra1_lifetime_years=_num(r["infra1_lifetime_years"]),
                infra2_lifetime_years=_num(r["infra2_lifetime_years"]),
                infra1_annual_use_mvkm=_num(r["infra1_annual_use_mvkm"]),
                infra2_annual_use_mvkm=_num(r["infra2_annual_use_mvkm"]),
                infra_share_1=_num(r["infra_share_1"]),
                infra_rail_allocation=r["infra_rail_allocation"] == "1",
            )
            registry[column] = (params, data)
    return registry


def mode(slug):
    """Return the default :class:`ModeParameters` for a canonical mode."""
    if slug not in CANONICAL_MODES:
        raise KeyError(
            f"unknown mode '{slug}'. See cafein_lca.list_modes() for the "
            "available modes."
        )
    return _registry()[CANONICAL_MODES[slug]][0]


def list_modes():
    """Return {slug: full mode name} for all canonical modes."""
    reg = _registry()
    return {slug: reg[col][0].name for slug, col in CANONICAL_MODES.items()}


def _mode_by_column(column):
    """Parameters + data for any workbook column (incl. sensitivity variants)."""
    return _registry()[column]


def _data_for(params):
    """ModeData backing a parameter object (matched via its slug)."""
    if params.slug.startswith("_column_"):
        return _registry()[params.slug.removeprefix("_column_")][1]
    return _registry()[CANONICAL_MODES[params.slug]][1]
