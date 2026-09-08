---
jupytext:
  text_representation:
    format_name: myst
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Reading results

A calculation returns a `Result` with energy use and greenhouse-gas
emissions in three views (per vehicle, per vehicle-kilometre, per
passenger-kilometre) and five life-cycle components. This guide explains
what each component contains, how the three views derive from one
another, and how to get the numbers out as tables and charts.

**How to?**

- [Know the five components](#know-the-five-components)
- [Move between per vehicle, per vehicle-km and per passenger-km](#move-between-per-vehicle-per-vehicle-km-and-per-passenger-km)
- [Read energy as well as emissions](#read-energy-as-well-as-emissions)
- [Get everything as one table](#get-everything-as-one-table)
- [Summarise all modes](#summarise-all-modes)
- [Plot the components](#plot-the-components)
- [Where to next](#where-to-next)

The first cell loads matplotlib for charts, pandas for tables and the
session class, and opens a session with the global defaults.

```{code-cell}
import dataclasses

import matplotlib.pyplot as plt
import pandas as pd

from cafein.lca import TransportLCA

lca = TransportLCA()
```

## Know the five components

Take a shared e-scooter of the first generation, a mode where every
component is non-zero. `per_pkm` gives the components in g CO₂e per
passenger-km:

```{code-cell}
scooter = lca.calculate("shared_escooter_first_gen")
scooter.per_pkm.round(1)
```

The components, in the order the model computes them:

- **manufacturing**: the materials of the vehicle body by material class
  (steel, aluminium, plastics and so on, each with its production energy),
  vehicle assembly and disposal, the battery including any replacements
  over the vehicle's life, and fluids. Everything here is a per-vehicle
  quantity.
- **delivery**: transporting the finished vehicle from the factory to the
  point of sale over up to ten legs (air, ship, train, trucks, vans), each
  with a distance and an energy intensity per tonne-kilometre.
- **use**: the fuel, electricity or hydrogen consumed while driving, from
  well to wheel, so the production and transport of the energy carrier are
  included. For electricity this depends on the generation mix.
- **services**: for shared fleets, the servicing vehicles that collect,
  charge, rebalance or refuel the fleet. For a self-serviced fleet such as
  taxis and ridesourcing, this is the empty driving between rides.
- **infrastructure**: the construction and maintenance materials of the
  network the mode runs on (bike lane, road, bus lane, track), amortised
  over the network's lifetime and yearly use and allocated to the vehicle
  class.

For this scooter, manufacturing is the largest component because a short
lifetime spreads the vehicle's production over few kilometres, and
services is second because the fleet is collected by van every day.

## Move between per vehicle, per vehicle-km and per passenger-km

The model computes the first four components per vehicle over its whole
life, then divides. `per_vkm` holds the per-vehicle-kilometre view and
`per_pkm` the per-passenger-kilometre view; the per-vehicle view is in
`to_frame()`, shown below. The chain is:

1. per vehicle-km = per vehicle ÷ lifetime kilometres, where lifetime
   kilometres are lifetime years × annual kilometres, plus the empty
   kilometres of a self-serviced fleet;
2. per passenger-km = per vehicle-km ÷ effective occupancy, where the
   effective occupancy is the mode's occupancy scaled down by the share of
   empty kilometres.

Infrastructure is the exception: the model defines it per vehicle-km
directly, so it has no per-vehicle value, and the per-vehicle total is
reported as not available (NaN) rather than as a misleading sum.

A taxi shows both steps. Its occupancy is 0.73 passengers on average, and
it drives about 23 empty kilometres per day between rides:

```{code-cell}
taxi = lca.calculate("taxi_ice")
taxi_views = pd.DataFrame(
    {
        "g CO₂e per vehicle-km": taxi.per_vkm,
        "g CO₂e per passenger-km": taxi.per_pkm,
    }
)
taxi_views.round(1)
```

The per-passenger-km values are larger than the per-vehicle-km values
because fewer than one passenger is on board on average, and the ratio is
higher than 1 / 0.73 because the empty kilometres carry nobody at all.

## Read energy as well as emissions

Every view exists for energy use too, in megajoules. `energy_per_pkm` and
`energy_per_vkm` mirror the emission properties, and
`energy_per_pkm_total` is the headline energy figure:

```{code-cell}
energy_and_ghg = pd.DataFrame(
    {
        "MJ per passenger-km": taxi.energy_per_pkm,
        "g CO₂e per passenger-km": taxi.per_pkm,
    }
)
energy_and_ghg.round(2)
```

Energy and emissions do not move together in every component. Use-phase
energy depends on the vehicle's consumption, while its emissions also
depend on how the energy was produced, which is why the electricity mix
changes emissions far more than it changes energy.

## Get everything as one table

`to_frame()` returns all views and both metrics at once, with the
components as rows and a two-level column index of metric and view:

```{code-cell}
taxi.to_frame().round(2)
```

The NaN in the per-vehicle total is the infrastructure convention
described above. The `parameters` attribute of a result holds the mode
parameters that produced it. To reproduce a reported number you also
need the session's electricity mix, the scenario file and case if one
was used, and the `cafein.lca` version; keep all four next to the
result. The mode parameters that matter most for the taxi, with their
units:

```{code-cell}
parameter_settings = [
    ("occupancy", "passengers per vehicle"),
    ("lifetime_years", "years"),
    ("annual_km", "km per year"),
    ("service_km_per_vehicle_day", "empty km per day"),
    ("fuel_consumption_per_100km", "litres gasoline-equivalent per 100 km"),
]
rows = []

for name, unit in parameter_settings:
    rows.append(
        {
            "parameter": name,
            "value": round(getattr(taxi.parameters, name), 2),
            "unit": unit,
        }
    )

taxi_parameters = pd.DataFrame(rows).set_index("parameter")
taxi_parameters
```

The low occupancy and the empty kilometres between rides are what make
the taxi's per-passenger result so much higher than a private car's with
the same fuel consumption. `dataclasses.asdict(taxi.parameters)` returns
all seventeen fields when you need the complete record.

## Summarise all modes

`summary()` runs every mode and returns one row per mode, by default the
greenhouse-gas components per passenger-km. The `per` and `metric`
arguments select the other views:

```{code-cell}
energy_per_vkm = lca.summary(per="vkm", metric="energy")
energy_per_vkm.head(8).round(2)
```

The frame is indexed by mode name, so ordinary pandas selection and
sorting apply. The ten modes with the lowest emissions per passenger-km
under the global defaults:

```{code-cell}
ghg_per_pkm = lca.summary()
ghg_per_pkm.sort_values("total").head(10).round(1)
```

Private bicycles lead because the model counts no fuel for them; the
model does not include the rider's food energy. The shared modes follow
their private counterparts at some distance because of their servicing
component and shorter lifetimes.

## Plot the components

A stacked bar chart shows which component drives each mode. Here a
handful of modes are compared under the global defaults:

```{code-cell}
plot_modes = [
    "private_bike",
    "shared_escooter_first_gen",
    "private_car_ice",
    "private_car_bev",
    "bus_ice",
    "metro_urban_train",
]
component_columns = [
    "manufacturing",
    "delivery",
    "use",
    "services",
    "infrastructure",
]

components = ghg_per_pkm.loc[plot_modes, component_columns]

figure, axis = plt.subplots(figsize=(9, 5))
components.plot(ax=axis, kind="bar", stacked=True)
axis.set_xlabel("Mode")
axis.set_ylabel("g CO₂e per passenger-km")
axis.set_title("Life-cycle components under the global defaults")
axis.tick_params(axis="x", rotation=30)
axis.legend(title="Component", frameon=False)
figure.tight_layout()
```

The car bars are dominated by use, the scooter bar by manufacturing and
services, and the metro bar carries a visible infrastructure share
because track is heavy per kilometre even when spread over many trains.

## Where to next

- [Modes and parameters](modes_and_parameters): the 56 modes and every
  parameter behind these numbers.
- [Electricity mix](electricity_mix): the assumption that moves the use
  component of electric modes.
- [Sensitivity analysis](sensitivity_analysis): which parameters matter,
  and by how much.
