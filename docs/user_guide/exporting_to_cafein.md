---
jupytext:
  text_representation:
    format_name: myst
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Exporting factors to cafein

The [`cafein`](https://github.com/cafein-py/cafein) routing library attaches
greenhouse-gas emissions to journeys from a table of per-leg factors. Two
methods turn a `cafein.lca` session into that table: `transit_factors()` for
public-transport legs and `street_factors()` for street modes. Each returns a
pandas frame; once you fill in the identity columns cafein matches a leg on,
you hand it to cafein, or save it as CSV, edit it, and load it back.

**How to?**

- [Export a factor table](#export-a-factor-table)
- [What the columns mean](#what-the-columns-mean)
- [Fill in the cafein identities](#fill-in-the-cafein-identities)
- [Key transit modes by GTFS route type](#key-transit-modes-by-gtfs-route-type)
- [Save and reload as CSV](#save-and-reload-as-csv)
- [Load the tables into cafein](#load-the-tables-into-cafein)
- [Where to next](#where-to-next)

```{code-cell}
import pandas as pd

from cafein.lca import TransportLCA

lca = TransportLCA()
```

## Export a factor table

`transit_factors()` returns one row per public-transport mode, and
`street_factors()` one row per street mode. Both read the session's
electricity mix and scenario, so a session built from a scenario exports that
scenario's numbers.

```{code-cell}
transit = lca.transit_factors()
transit
```

`street_factors()` covers the rest; here are three of its rows:

```{code-cell}
street = lca.street_factors(
    modes=["private_car_bev", "private_bike", "taxi_ice"]
)
street
```

## What the columns mean

Each row has three groups of columns.

- The **key columns** are the ones cafein matches a leg on: `trip_id`,
  `route_id`, `agency_id` and `route_type` for transit; `street_mode`,
  `vehicle_class` and `service_model` for street. They are empty on export,
  which makes the frame a template — you fill them for the legs you are
  costing (next section).
- The **components** are the mode's emissions in grams of CO₂-equivalent,
  split into `vehicle` (manufacturing and delivery), `fuel` (the use phase),
  `infrastructure`, and `operations` (the servicing of shared fleets and the
  empty running of taxis and ridesourcing). They sum to `total`.
- The **`total`** column is that sum, written so the table reads on its own.
  cafein keeps the column but does not use it: it adds the four components it
  selects (which lets it report operational-only or full emissions), so
  including `total` in the sum would double-count. cafein 0.25 keeps `total`
  without warning; earlier versions drop it with a warning.
- The **`basis`** column says whether those numbers are per
  passenger-kilometre or per vehicle-kilometre. Transit and most street rows
  are per passenger-km; private-car rows are per vehicle-km, so cafein can
  divide them by an occupancy you choose at routing time. The remaining
  columns — `mode`, `scenario`, `scenario_sha256`, `case` and
  `cafein_lca_version` — record where the numbers came from; cafein keeps
  them but does not compute with them.

## Fill in the cafein identities

cafein resolves a leg's factor from the key columns, not from `mode`, so a
row is usable only once its key columns are set. Pass an `identities` mapping
from mode slug to the columns you want filled:

```{code-cell}
street = lca.street_factors(
    modes=["private_car_bev", "private_bike"],
    identities={
        "private_car_bev": {
            "street_mode": "car",
            "vehicle_class": "BEV",
            "service_model": "private",
        },
        "private_bike": {
            "street_mode": "bicycle",
            "vehicle_class": "conventional",
            "service_model": "private",
        },
    },
)
street[["street_mode", "vehicle_class", "service_model", "mode", "basis"]]
```

For transit the same mapping fills the GTFS keys. cafein resolves the most
specific match, so giving a `bus_bev` row a `route_id` lets the electric
lines you name carry those numbers while every other bus falls back to the
default bus row:

```{code-cell}
transit = lca.transit_factors(
    modes=["bus_bev"], identities={"bus_bev": {"route_id": "550"}}
)
transit[["route_id", "route_type", "mode", "basis"]]
```

One mode can also stand for several route types. Give a list, and the mode
gets one row per value, each with the same numbers:

```{code-cell}
rail = lca.transit_factors(
    modes=["metro_urban_train"],
    identities={"metro_urban_train": {"route_type": ["0", "1", "2"]}},
)
rail[["route_type", "mode", "total"]]
```

The three rows differ only in `route_type`. The basic route types are usually enough: cafein files GTFS's extended codes
under them, `900`–`999` under tram (`0`), `400`–`499` under metro (`1`),
`100`–`199` under rail (`2`) and `700`–`899` under bus (`3`). A code you list
explicitly takes precedence, so a row for `109` gives suburban trains their
own factor while `2` still covers the rest. The fallback also means a row for
`2` reaches long-distance trains (`101`, `102`) unless you give them a row of
their own.

Only one column per mode can hold a list. Two rows that cafein would match on
the same key, such as two modes both given route type `3`, raise a
`ValueError`, because cafein would keep one of them without a warning.

## Key transit modes by GTFS route type

Most transit tables only need one row per kind of vehicle, keyed by the
GTFS `route_type` of each leg. `gtfs_identities()` builds that mapping for
the four basic route types: tram (`0`), metro (`1`), rail (`2`) and bus
(`3`).

```{code-cell}
from cafein.lca import gtfs_identities

ids = gtfs_identities()
ids
```

Each of the four modes gets one route type. Pass the mapping's keys as
`modes`, so that the table holds only the mapped modes:

```{code-cell}
by_type = lca.transit_factors(modes=list(ids), identities=ids)
by_type[["route_type", "mode", "total"]]
```

The table has one row per basic route type, with each mode's total in grams
of CO₂-equivalent per passenger-km. Because cafein files the extended codes
in the ranges listed above under the basic ones, these four rows also cover
a feed that uses codes in those ranges.

To change the map, pass `{route_type: mode}` entries; `None` drops a code.
The next table keeps the suburban-rail factor off long-distance trains:
it drops the basic rail code and lists the extended codes for regional rail
(`106`) and suburban railway (`109`) instead. It also gives buses the
battery-electric bus:

```{code-cell}
ids = gtfs_identities(
    {
        "2": None,
        "106": "suburban_regional_rail",
        "109": "suburban_regional_rail",
        "3": "bus_bev",
    }
)
by_type = lca.transit_factors(modes=list(ids), identities=ids)
by_type[["route_type", "mode", "total"]]
```

The suburban mode now has two rows, `106` and `109`, with the same numbers.
Legs on long-distance routes (`101`, `102`) match none of these rows, so
cafein takes their factor from its shipped defaults; in cafein 0.29 its rail
row carries the metro and urban-train numbers.

## Save and reload as CSV

The frames write to CSV like any other:

```{code-cell}
transit.to_csv("transit_factors.csv", index=False)
```

CSV records no column types, so reading one back needs care: the identity and
provenance columns are strings (a `route_type` of `"0"` or an `agency_id` of
`"001"` must stay text), and blank cells must stay blank rather than becoming
`NaN`. The `export` module gives you the exact dtype mapping for that:

```{code-cell}
from cafein.lca.export import READ_CSV_DTYPES

reloaded = pd.read_csv(
    "transit_factors.csv", keep_default_na=False, dtype=READ_CSV_DTYPES
)
reloaded.columns.tolist()
```

If you edit the file in a spreadsheet, keep the identifier columns formatted
as text, and change identity columns only — a row's `basis` and its component
values belong together, so to change the basis, re-export rather than editing
the label.

```{code-cell}
:tags: [remove-cell]
import pathlib

pathlib.Path("transit_factors.csv").unlink()
```

## Load the tables into cafein

With cafein installed (`pip install "cafein.lca[cafein]"`), its factor
loaders take the exported frames directly. This step runs in a cafein
session, not here:

```python
import cafein.emissions as em

# Layer the exported rows over cafein's shipped defaults.
transit_table = em.load_factors(transit)
street_table = em.load_street_factors(street)

# cafein reads the per-row basis, dividing the per-vehicle-km car rows by the
# occupancy you pass and leaving the per-passenger-km rows as they are.
factor, basis = em.street_factor_with_basis(
    "car", factors=street, vehicle_class="BEV"
)
```

Regenerating the Finland factors that cafein ships from these helpers is a
step on the cafein side, once a release of `cafein.lca` is on PyPI.

## Where to next

- [Scenarios](../scenarios/scenarios): export a regional scenario's factors
  by building the session from a scenario first.
- [Reading results](reading_results): the five components the exported four
  are grouped from.
- [API reference](../reference): `transit_factors`, `street_factors` and
  `gtfs_identities` in full.
