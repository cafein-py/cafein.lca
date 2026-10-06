"""cafein-ready emission-factor tables built from cafein.lca results.

:func:`transit_factors` and :func:`street_factors` return long-format pandas
frames whose columns match cafein's factor loaders (``load_factors`` and
``load_street_factors``): the key columns cafein resolves a leg on, the four
life-cycle components in g CO2e and their ``total``, an explicit ``basis``, and
provenance columns cafein carries through unchanged. cafein sums the four
components, not ``total``. See the "Exporting factors to cafein" guide.

The two functions are exposed as :meth:`TransportLCA.transit_factors` and
:meth:`TransportLCA.street_factors`, which pass the session so the electricity
mix, scenario and case come from it.
"""

import pandas as pd

from .modes import CANONICAL_MODES

# cafein's factor-table columns (cafein.emissions.KEY_COLUMNS etc.).
TRANSIT_KEY_COLUMNS = ["trip_id", "route_id", "agency_id", "route_type"]
STREET_KEY_COLUMNS = ["street_mode", "vehicle_class", "service_model"]
COMPONENT_COLUMNS = ["vehicle", "fuel", "infrastructure", "operations"]
PROVENANCE_COLUMNS = ["scenario", "scenario_sha256", "case", "cafein_lca_version"]

#: The four components plus their `total`; all numeric. `total` is written for
#: readers of the table — cafein keeps it but sums the components, not `total`.
NUMERIC_COLUMNS = COMPONENT_COLUMNS + ["total"]

#: cafein.lca's five life-cycle components grouped into cafein's four columns.
COMPONENT_MAP = {
    "vehicle": ("manufacturing", "delivery"),
    "fuel": ("use",),
    "infrastructure": ("infrastructure",),
    "operations": ("services",),
}

TRANSIT_COLUMNS = (
    TRANSIT_KEY_COLUMNS
    + ["mode"]
    + COMPONENT_COLUMNS
    + ["total", "basis"]
    + PROVENANCE_COLUMNS
)
STREET_COLUMNS = (
    STREET_KEY_COLUMNS
    + ["mode"]
    + COMPONENT_COLUMNS
    + ["total", "basis"]
    + PROVENANCE_COLUMNS
)

#: Every non-numeric column is a string; blanks are "" rather than NaN.
STRING_COLUMNS = [
    c for c in TRANSIT_COLUMNS + STREET_COLUMNS if c not in NUMERIC_COLUMNS
]
STRING_COLUMNS = list(dict.fromkeys(STRING_COLUMNS))

#: dtype mapping for reloading a saved CSV outside cafein, alongside
#: ``keep_default_na=False`` (CSV carries no type metadata, so numeric-looking
#: or leading-zero identifiers would otherwise be inferred as integers).
READ_CSV_DTYPES = {c: str for c in STRING_COLUMNS}

#: Transit modes; every other canonical mode is a street mode.
TRANSIT_MODES = (
    "bus_ice",
    "bus_hev",
    "bus_bev",
    "bus_bev_two_packs",
    "bus_fcev",
    "tram_light_rail",
    "metro_urban_train",
)
STREET_MODES = tuple(s for s in CANONICAL_MODES if s not in TRANSIT_MODES)

#: Street modes exported per vehicle-km, matching cafein's "car" convention
#: (query-time occupancy division): exactly the private-car slugs.
_STREET_VEHICLE_KM_MODES = frozenset(
    {
        "private_car_ice",
        "private_car_hev",
        "private_car_phev",
        "private_car_bev",
        "private_car_fcev",
        "large_private_car_ice",
        "large_private_car_hev",
        "large_private_car_phev",
        "large_private_car_bev",
        "large_private_car_fcev",
    }
)


def _validate_modes(modes, domain, label):
    if modes is None:
        return list(domain)
    domain = set(domain)
    resolved = []
    for slug in modes:
        if slug not in domain:
            raise ValueError(f"{slug!r} is not a {label} mode")
        resolved.append(slug)
    return resolved


def _check_identities(identities, key_columns):
    allowed = set(key_columns)
    for slug, mapping in identities.items():
        unknown = set(mapping) - allowed
        if unknown:
            raise ValueError(
                f"unknown identity column(s) for {slug!r}: "
                f"{', '.join(sorted(unknown))}"
            )


def _key_sets(slug, mapping):
    """One key mapping per row: a list value gives one row per element."""
    listed = [c for c, v in mapping.items() if isinstance(v, list)]
    if len(listed) > 1:
        raise ValueError(
            f"identities for {slug!r} list values in several columns "
            f"({', '.join(sorted(listed))}); list at most one"
        )
    if not listed:
        return [mapping]
    column = listed[0]
    if not mapping[column]:
        raise ValueError(f"identities for {slug!r} list no {column} values")
    return [{**mapping, column: value} for value in mapping[column]]


def _key_string(value):
    # Same conversion as _frame's fillna("").astype(str), for scalars and not.
    if value is None or (pd.api.types.is_scalar(value) and pd.isna(value)):
        return ""
    return str(value)


def _transit_bucket(row):
    """cafein's resolution rung for a transit row (None for an empty key).

    cafein files a row under its most specific key: trip, route,
    agency + route_type, then route_type.
    """
    if row["trip_id"]:
        return ("trip_id", row["trip_id"])
    if row["route_id"]:
        return ("route_id", row["route_id"])
    if row["route_type"]:
        if row["agency_id"]:
            return ("agency_id, route_type", row["agency_id"], row["route_type"])
        return ("route_type", row["route_type"])
    return None


def _street_bucket(row):
    """cafein matches street rows on the whole key triple."""
    key = tuple(row[c] for c in STREET_KEY_COLUMNS)
    if not any(key):
        return None
    return (", ".join(STREET_KEY_COLUMNS),) + key


def _check_unique_buckets(rows, bucket):
    # cafein keeps the later of two rows at the same rung without a warning.
    seen = {}
    for row in rows:
        key = bucket(row)
        if key is None:
            continue
        if key in seen:
            values = ", ".join(repr(v) for v in key[1:])
            raise ValueError(
                f"{seen[key]!r} and {row['mode']!r} both map to {key[0]} "
                f"{values}; cafein would keep only one of them"
            )
        seen[key] = row["mode"]


def _provenance(lca):
    scenario = lca.scenario
    if scenario is None:
        return {"scenario": "", "scenario_sha256": "", "case": ""}
    return {
        "scenario": scenario.name,
        "scenario_sha256": getattr(scenario, "sha256", ""),
        "case": scenario.case,
    }


def _components(series):
    values = {
        column: float(sum(series[c] for c in parts))
        for column, parts in COMPONENT_MAP.items()
    }
    values["total"] = float(sum(values.values()))
    return values


def _frame(rows, columns):
    frame = pd.DataFrame(rows).reindex(columns=columns)
    for column in columns:
        if column in NUMERIC_COLUMNS:
            frame[column] = frame[column].astype(float)
        else:
            frame[column] = frame[column].fillna("").astype(str)
    return frame


def _factor_table(lca, modes, identities, key_columns, columns, per_vkm_modes, bucket):
    identities = identities or {}
    _check_identities(identities, key_columns)
    version = _version()
    provenance = _provenance(lca)
    rows = []
    for slug in modes:
        result = lca.calculate(slug)
        if slug in per_vkm_modes:
            components = _components(result.per_vkm)
            basis = "vehicle_km"
        else:
            components = _components(result.per_pkm)
            basis = "passenger_km"
        for keys in _key_sets(slug, identities.get(slug, {})):
            row = {column: "" for column in key_columns}
            row.update({c: _key_string(v) for c, v in keys.items()})
            row["mode"] = slug
            row.update(components)
            row["basis"] = basis
            row.update(provenance)
            row["cafein_lca_version"] = version
            rows.append(row)
    _check_unique_buckets(rows, bucket)
    return _frame(rows, columns)


def _version():
    from . import __version__

    return __version__


def transit_factors(lca, modes=None, identities=None):
    """cafein-ready transit factor table (g CO2e per passenger-km).

    Parameters
    ----------
    lca : TransportLCA
        The session; its scenario, case and electricity mix drive the rows.
    modes : iterable of str, optional
        Transit mode slugs (default: all bus, tram and metro modes).
        A non-transit slug raises ``ValueError``.
    identities : mapping, optional
        ``{slug: {column: value}}`` filling cafein's transit key columns
        (``trip_id``, ``route_id``, ``agency_id``, ``route_type``) for the
        named rows; other rows keep empty keys. A list value gives the mode
        one row per element (e.g. ``{"route_type": ["0", "900"]}``); at most
        one column per mode may hold a list. An unknown column, an empty
        list, or two rows that cafein would file under the same key (its
        most specific one: ``trip_id``, ``route_id``, ``agency_id`` with
        ``route_type``, or ``route_type``) raise ``ValueError``.

    Returns
    -------
    DataFrame
        One row per mode and identity, with the transit schema; ``basis``
        is always ``passenger_km``. With empty keys the frame is a template
        — populate the identity columns before loading it into cafein.
    """
    modes = _validate_modes(modes, TRANSIT_MODES, "transit")
    return _factor_table(
        lca,
        modes,
        identities,
        TRANSIT_KEY_COLUMNS,
        TRANSIT_COLUMNS,
        frozenset(),
        _transit_bucket,
    )


def street_factors(lca, modes=None, identities=None):
    """cafein-ready street factor table (g CO2e per the row's ``basis``).

    Parameters
    ----------
    lca : TransportLCA
        The session; its scenario, case and electricity mix drive the rows.
    modes : iterable of str, optional
        Street mode slugs (default: every non-transit canonical mode). A
        transit slug raises ``ValueError``.
    identities : mapping, optional
        ``{slug: {column: value}}`` filling cafein's street key columns
        (``street_mode``, ``vehicle_class``, ``service_model``) for the named
        rows; other rows keep empty keys. A list value gives the mode one row
        per element; at most one column per mode may hold a list. An unknown
        column, an empty list, or two rows with the same key triple raise
        ``ValueError``.

    Returns
    -------
    DataFrame
        One row per mode and identity, with the street schema. Private-car
        rows are per vehicle-km (``basis == "vehicle_km"``) so cafein can
        apply a query-time occupancy; every other row is per passenger-km.
        With empty keys the frame is a template — populate the identity
        columns before loading it into cafein.
    """
    modes = _validate_modes(modes, STREET_MODES, "street")
    return _factor_table(
        lca,
        modes,
        identities,
        STREET_KEY_COLUMNS,
        STREET_COLUMNS,
        _STREET_VEHICLE_KM_MODES,
        _street_bucket,
    )
