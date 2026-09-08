---
jupytext:
  text_representation:
    format_name: myst
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Scenarios

The library's defaults are the source model's global central case. A
*scenario* is a file that overrides them: an electricity mix and a set of
per-mode parameter values, each given as three cases, best, central and
worst. A session built from a scenario therefore reports a range across
the cases instead of one figure.

**How to?**

- [Load a packaged scenario](#load-a-packaged-scenario)
- [Compare the three cases](#compare-the-three-cases)
- [Read the provenance of a value](#read-the-provenance-of-a-value)
- [Combine a scenario with overrides](#combine-a-scenario-with-overrides)
- [Write your own scenario](#write-your-own-scenario)
- [Know what the cases mean](#know-what-the-cases-mean)
- [Where to next](#where-to-next)

```{code-cell}
import pandas as pd

import cafein.lca
from cafein.lca import Scenario, TransportLCA, mode
```

## Load a packaged scenario

`list_scenarios()` names the scenarios shipped with the package and
describes each in one line:

```{code-cell}
cafein.lca.list_scenarios()
```

Two are shipped: `finland_2020`, which changes only the electricity mix,
and `india_metropolitan`, a composite of Delhi and Mumbai operating
conditions with three cases, used throughout this page.

`Scenario.load()` takes a packaged name or a path to your own file, and a
`case`, which is `central` unless you say otherwise. Passing the scenario
to a session applies it to every mode:

```{code-cell}
india = Scenario.load("india_metropolitan")
lca = TransportLCA(scenario=india)
india.name, india.case, lca.power_mix
```

The session took the scenario's electricity mix, the packaged `India`
preset. The parameters a mode now runs with are available from the
session; a diesel bus under the central case carries 53 passengers, drives
55,000 km a year and lasts 12 years, against 17, 44,000 and 9 in the
global defaults:

```{code-cell}
default_bus = mode("bus_ice")
scenario_bus = lca.parameters("bus_ice")
parameter_settings = [
    ("occupancy", "passengers"),
    ("annual_km", "km per year"),
    ("lifetime_years", "years"),
]
rows = []

for name, unit in parameter_settings:
    rows.append(
        {
            "parameter": name,
            "unit": unit,
            "global default": getattr(default_bus, name),
            "india_metropolitan, central": getattr(scenario_bus, name),
        }
    )

bus_parameters = pd.DataFrame(rows).set_index("parameter")
bus_parameters
```

The scenario triples the occupancy, adds a quarter to the annual
mileage and a third to the lifetime, all from Indian sources named in
the file. The result for that bus, in g CO₂e per passenger-km:

```{code-cell}
lca.calculate("bus_ice").per_pkm.round(1)
```

The bus emits about 23 g CO₂e per passenger-km against 91 under the
global defaults, and almost all of the change comes from the higher
occupancy spreading the same vehicle over three times as many passengers.

## Compare the three cases

Every scenario carries three cases, named by their effect on emissions
per passenger-km: `best` holds every low-emission value, `worst` every
high-emission one, `central` the best estimate. Loading each case into
its own session and running a few modes gives the envelope:

```{code-cell}
case_settings = ["best", "central", "worst"]
comparison_modes = [
    "private_car_ice",
    "private_car_bev",
    "private_moped_ice",
    "taxi_ice",
    "bus_ice",
    "bus_bev",
    "metro_urban_train",
]
rows = []

for case in case_settings:
    session = TransportLCA(scenario=Scenario.load("india_metropolitan", case=case))
    for slug in comparison_modes:
        rows.append(
            {
                "mode": slug,
                "case": case,
                "g CO₂e per passenger-km": session.calculate(slug).ghg_per_pkm,
            }
        )

case_results = pd.DataFrame(rows)
case_results.head(6).round(1)
```

A wide table puts each mode's best-to-worst range on one row:

```{code-cell}
case_comparison = case_results.pivot(
    index="mode",
    columns="case",
    values="g CO₂e per passenger-km",
)
case_comparison = case_comparison.loc[comparison_modes, case_settings]
case_comparison.round(1)
```

The values are g CO₂e per passenger-km. The spread is wide: a factor of
three to eight between best and worst for every mode shown. Compare modes
*within* one column. The best and worst
columns stack every optimistic or pessimistic assumption at once, so they
are envelopes rather than likely outcomes, and the central column is the
one to quote.

## Read the provenance of a value

Every override in a packaged scenario carries its evidence type,
geography, source, confidence and a note, and `provenance()` returns them
as a table. The evidence vocabulary is `observed`, `model_input`,
`capacity`, `projection`, `derived` and `assumption`. For the bus:

```{code-cell}
units = {
    "occupancy": "passengers per vehicle",
    "annual_km": "km per year",
    "lifetime_years": "years",
    "service_km_per_vehicle_day": "km per vehicle per day",
    "vehicle_weight_kg": "kg",
    "fuel_consumption_per_100km": "litres gasoline-equivalent per 100 km",
}
provenance = india.provenance()
bus_records = provenance[provenance["mode"] == "bus_ice"]
rows = []

for record in bus_records.itertuples():
    rows.append(
        {
            "parameter": record.parameter,
            "value": record.value,
            "unit": units[record.parameter],
            "evidence": record.evidence,
            "geography": record.geography,
            "confidence": record.confidence,
        }
    )

bus_provenance = pd.DataFrame(rows).set_index("parameter")
bus_provenance
```

The bus occupancy is a model input from a Mumbai life-cycle study rather
than a national observation, and the servicing distance is a derived
value of low confidence; report both as assumptions alongside any figure
that rests on them. The `source` and `note` columns name the study and
table behind each value and any caveat. The full occupancy record,
including the `source` and `note` fields left out of the table above,
reads best as a single column:

```{code-cell}
occupancy_record = bus_records[bus_records["parameter"] == "occupancy"]
occupancy_record.iloc[0]
```

The source names the study, its table and the three operating
conditions the cases come from, so the value can be checked against the
paper.

## Combine a scenario with overrides

Keyword overrides on `calculate()` win over the scenario. A bus filled to
its 70-passenger capacity under the otherwise unchanged central case:

```{code-cell}
full_bus = lca.calculate("bus_ice", occupancy=70)
round(full_bus.ghg_per_pkm, 1)
```

The value is in g CO₂e per passenger-km and is lower than the central
case's 23 in proportion to the occupancy, 53 against 70. A parameter
object you build yourself is used exactly as given, so it bypasses the
scenario altogether:

```{code-cell}
default_bus = mode("bus_ice")
default_bus_result = lca.calculate(default_bus)
round(default_bus_result.ghg_per_pkm, 1)
```

This is the global-default bus again, run inside the Indian session; only
the electricity mix differs, which does not touch a diesel bus.

## Write your own scenario

A scenario file is TOML. It has a `name`, an optional `description`, a
`power_mix` (a preset name, a table of the six generation shares, or a
per-case table of either) and `[modes.<slug>]` tables. Keys may be
canonical mode slugs or glob patterns such as `"bus_*"`; exact slugs win
over patterns. A parameter is a scalar, a table with `value` plus
provenance, or a table with the three cases plus provenance; `evidence`,
`geography` and `source` may be given per case:

```toml
name = "my_city"
power_mix = "EU 28"

[modes.bus_bev]
battery_capacity_kwh = 250

[modes."bus_*".occupancy]
best = 60
central = 30
worst = 15
evidence = {best = "assumption", central = "observed", worst = "assumption"}
geography = "my city"
source = "operator report 2024"
confidence = "medium"
```

Loading validates slugs, parameter names and ranges, the evidence and
confidence vocabularies, and the completeness of case tables, so a
mistake surfaces at `Scenario.load()` rather than in a result. The
packaged `india_metropolitan.toml` inside the package is a complete
example with a source on every line.

## Know what the cases mean

The case names describe the emissions outcome, so the *direction* of each
parameter differs. Put the low-emission value under `best` whatever its
magnitude:

| Parameter | `best` | `worst` |
|---|---|---|
| occupancy, annual_km | high | low |
| lifetime_years | long | short |
| vehicle_weight_kg, battery_capacity_kwh | light, small | heavy, large |
| fuel and electricity consumption | low | high |
| service_km_per_vehicle_day | low | high |
| power_mix | clean | carbon-intensive |

A long lifetime lowers manufacturing emissions per kilometre by
allocation only; it does not make the vehicle better. The packaged
scenarios are tested so that emissions per passenger-km come out ordered
best ≤ central ≤ worst for every mode.

Two caveats apply to the packaged Indian scenario. Its metro rows
describe one six-coach Mumbai train, so they must be changed together,
and their ridership is planned rather than measured. The model also has
no CNG fuel type, though CNG powers most Delhi and Mumbai buses, taxis
and auto-rickshaws; those modes run here on diesel or petrol instead.

## Where to next

- [Sensitivity analysis](../user_guide/sensitivity_analysis): one
  parameter at a time, before bundling assumptions into a scenario.
- [Electricity mix](../user_guide/electricity_mix): the presets a
  scenario's `power_mix` can name.
- [The model](../model/model): what the parameters feed into.
