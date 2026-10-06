"""Mode registry: canonical slugs -> default parameters and mode data.

``modes.csv`` holds one row per workbook mode column (all 130, including the
sensitivity variants used as golden-test fixtures). The public registry maps
snake_case slugs to the canonical columns; variants stay reachable through
:func:`_mode_by_column` for the test suite.

Mode packs (``data/modes/<pack>/``) add modes from other sources on top of the
coefficient set: a ``manifest.toml``, a ``modes.csv`` with the same columns
(``slug`` in place of ``column``), optional new ``infrastructure_types.csv``
rows, and a ``provenance.csv`` that sources every value of both.
"""

import csv
import dataclasses
import fnmatch
import functools
import re
import sys

from . import config
from .config import COEFFICIENTS_DIR, DEFAULT_COEFFICIENTS, DELIVERY_LEGS, MATERIALS
from .parameters import ModeParameters

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

_MODES_CSV = COEFFICIENTS_DIR / "modes.csv"

#: Columns of a pack's modes.csv that need no provenance row: the slug and
#: the derived (unused) lifetime_km.
_PACK_UNSOURCED_COLUMNS = {"slug", "lifetime_km"}

#: A pack mode's slug: lower-case snake_case, so it cannot collide with the
#: coefficient set's column keys or the ``_column_`` variants.
_PACK_SLUG = re.compile(r"[a-z][a-z0-9_]*")

#: slug -> registry key: the workbook column of the canonical central case
#: for the coefficient set's modes, the slug itself for mode-pack modes.
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
    source: str = DEFAULT_COEFFICIENTS  # coefficient set or mode pack


def _num(value):
    if value in (None, ""):
        return 0.0
    return float(value)


def _slugify_column(column, name):
    for slug, col in CANONICAL_MODES.items():
        if col == column:
            return slug
    return f"_column_{column}"


def _entry(r, key, slug, source):
    """(ModeParameters, ModeData) of one modes.csv row."""
    name = r["name"]
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
        hydrogen_consumption_per_100km=_num(r["hydrogen_consumption_per_100km"]),
        electric_driving_share=_num(r["electric_driving_share"]),
        service_vehicle=r["service_vehicle"] or "None",
        service_km_per_vehicle_day=_num(r["service_km_per_vehicle_day"]),
        vehicles_per_service_trip=_num(r["vehicles_per_service_trip"]),
    )
    data = ModeData(
        column=key,
        name=name,
        default_weight_kg=_num(r["vehicle_weight_kg"]),
        material_shares=tuple(_num(r[f"share_{m}"]) for m in MATERIALS),
        battery_replacements=_num(r["battery_replacements"]),
        fluids_energy_mj=_num(r["fluids_energy_mj"]),
        fluids_ghg_g=_num(r["fluids_ghg_g"]),
        fluids_weight_scaled=r["fluids_weight_scaled"] == "1",
        delivery_weight_computed=r["delivery_weight_computed"] == "1",
        delivery_weight_kg=_num(r["delivery_weight_kg"]),
        delivery_km=tuple(_num(r[f"delivery_km_{leg}"]) for leg in DELIVERY_LEGS),
        services_uses_intensity_table=(r["services_uses_intensity_table"] == "1"),
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
        source=source,
    )
    return params, data


@functools.lru_cache(maxsize=1)
def _registry():
    registry = {}
    with open(_MODES_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            column = r["column"]
            slug = _slugify_column(column, r["name"])
            registry[column] = _entry(r, column, slug, DEFAULT_COEFFICIENTS)
    for pack in _packs():
        for r in pack["modes"]:
            registry[r["slug"]] = _entry(r, r["slug"], r["slug"], pack["name"])
    return registry


def mode(slug):
    """Return the default :class:`ModeParameters` for a canonical mode."""
    if slug not in CANONICAL_MODES:
        raise KeyError(
            f"unknown mode '{slug}'. See cafein.lca.list_modes() for the "
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


def mode_provenance(slug):
    """Sources of a mode's default values.

    A DataFrame shaped like :meth:`Scenario.provenance`: one row per
    provenance entry, whose ``parameter`` may be a pattern such as
    ``share_*``. A mode of the coefficient set has one row citing the set;
    a mode-pack mode lists the pack's sources value by value, including those
    of any infrastructure type the pack adds for it (as ``"type: field"``).
    """
    import pandas as pd

    from .scenarios import PROVENANCE_KEYS

    data = _data_for(mode(slug))
    columns = ["mode", "parameter", *PROVENANCE_KEYS]
    if data.source == DEFAULT_COEFFICIENTS:
        with open(COEFFICIENTS_DIR / "manifest.toml", "rb") as f:
            manifest = tomllib.load(f)
        row = {
            "mode": slug,
            "parameter": "*",
            "evidence": "model_input",
            "source": manifest["source"],
            "note": f"default of the {DEFAULT_COEFFICIENTS} coefficient set",
        }
        return pd.DataFrame([row], columns=columns)
    pack = next(p for p in _packs() if p["name"] == data.source)
    rows = []
    for r in pack["provenance"]:
        if r["item"] == slug:
            parameter = r["field"]
        elif r["item"] in (data.infra1_type, data.infra2_type):
            parameter = f"{r['item']}: {r['field']}"
        else:
            continue
        row = {"mode": slug, "parameter": parameter}
        row.update({k: r[k] or None for k in PROVENANCE_KEYS})
        if row["year"]:
            row["year"] = int(row["year"])
        rows.append(row)
    return pd.DataFrame(rows, columns=columns)


@functools.lru_cache(maxsize=1)
def _packs():
    """The packaged mode packs, read and validated."""
    config.conf.infrastructure_types  # merges and checks the packs' own types
    return tuple(_load_pack(d) for d in config.mode_pack_dirs())


def _load_pack(directory):
    """Read one mode pack and check its columns and provenance."""
    from .scenarios import CONFIDENCE, EVIDENCE, PROVENANCE_KEYS

    with open(directory / "manifest.toml", "rb") as f:
        manifest = tomllib.load(f)
    name = directory.name
    where = f"mode pack '{name}'"
    if manifest.get("name", name) != name:
        raise ValueError(f"{where}: manifest name differs from its directory")
    if name in config.available_coefficient_sets():
        raise ValueError(f"{where}: name is taken by a coefficient set")
    if manifest.get("builds_on") != DEFAULT_COEFFICIENTS:
        raise ValueError(
            f"{where} builds on {manifest.get('builds_on')!r}, "
            f"not {DEFAULT_COEFFICIENTS!r}"
        )
    columns = ["slug" if c == "column" else c for c in config._header(_MODES_CSV)]
    modes = config._read_checked(directory / "modes.csv", columns, where)
    # Provenance items: the pack's modes and the infrastructure types it adds,
    # each with the columns whose values need a source.
    items = {
        r["slug"]: (r, [c for c in columns if c not in _PACK_UNSOURCED_COLUMNS])
        for r in modes
    }
    pack_types = set()
    infra_path = directory / "infrastructure_types.csv"
    if infra_path.is_file():
        infra_columns = config._header(COEFFICIENTS_DIR / "infrastructure_types.csv")
        for r in config._read_checked(infra_path, infra_columns, where):
            if r["infrastructure"] in items:
                raise ValueError(
                    f"{where}: {r['infrastructure']!r} names both a mode and an "
                    "infrastructure type"
                )
            sourced = [c for c in infra_columns if c != "infrastructure"]
            items[r["infrastructure"]] = (r, sourced)
            pack_types.add(r["infrastructure"])
    # A pack mode runs on the set's infrastructure types or its own pack's.
    usable = {
        r["infrastructure"]
        for r in config._read_csv(COEFFICIENTS_DIR / "infrastructure_types.csv")
    } | pack_types
    for r in modes:
        for column in ("infra1_type", "infra2_type"):
            if r[column] and r[column] not in usable:
                raise ValueError(
                    f"{where}: {r['slug']} uses infrastructure type "
                    f"{r[column]!r}, defined neither by the set nor the pack"
                )
    provenance = config._read_checked(
        directory / "provenance.csv", ["item", "field", *PROVENANCE_KEYS], where
    )
    for i, r in enumerate(provenance, start=2):
        line = f"{where} provenance.csv line {i}"
        if r["item"] not in items:
            raise ValueError(f"{line}: unknown item {r['item']!r}")
        if not any(fnmatch.fnmatchcase(c, r["field"]) for c in items[r["item"]][1]):
            raise ValueError(f"{line}: field {r['field']!r} matches no column")
        if r["evidence"] not in EVIDENCE:
            raise ValueError(f"{line}: evidence must be one of {', '.join(EVIDENCE)}")
        if r["confidence"] not in CONFIDENCE:
            raise ValueError(
                f"{line}: confidence must be one of {', '.join(CONFIDENCE)}"
            )
        if not r["source"].strip():
            raise ValueError(f"{line}: source is empty")
        if r["year"] and not re.fullmatch(r"[0-9]+", r["year"]):
            raise ValueError(f"{line}: year must be a whole number")
    # Every value a pack sets needs a source.
    for item, (row, sourced) in items.items():
        patterns = [p["field"] for p in provenance if p["item"] == item]
        unsourced = [
            c
            for c in sourced
            if row[c] != "" and not any(fnmatch.fnmatchcase(c, p) for p in patterns)
        ]
        if unsourced:
            raise ValueError(
                f"{where}: no provenance for {item}: {', '.join(unsourced)}"
            )
    return {
        "name": name,
        "manifest": manifest,
        "modes": modes,
        "provenance": provenance,
    }


def _register_pack_slugs():
    """Add the mode packs' slugs to CANONICAL_MODES (keyed by the slug)."""
    for directory in config.mode_pack_dirs():
        for r in config._read_csv(directory / "modes.csv"):
            if not _PACK_SLUG.fullmatch(r["slug"] or ""):
                raise ValueError(
                    f"mode pack '{directory.name}': mode name {r['slug']!r} "
                    "must be lower-case snake_case"
                )
            if r["slug"] in CANONICAL_MODES:
                raise ValueError(
                    f"mode pack '{directory.name}' reuses the mode name "
                    f"{r['slug']!r}"
                )
            CANONICAL_MODES[r["slug"]] = r["slug"]


def _reload_packs():
    """Re-read the mode packs (the test suite swaps MODE_PACKS_DIR)."""
    for slug in [s for s, key in CANONICAL_MODES.items() if s == key]:
        del CANONICAL_MODES[slug]
    _register_pack_slugs()
    _packs.cache_clear()
    _registry.cache_clear()
    config.conf.__dict__.pop("infrastructure_types", None)


_register_pack_slugs()
