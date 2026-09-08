---
jupytext:
  text_representation:
    format_name: myst
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Quickstart

This guide computes the life-cycle emissions of one transport mode,
shows what the number is made of, compares a few modes, and changes one
assumption. It takes about ten minutes.

**How to?**

- [Compute a first result](#compute-a-first-result)
- [See what the result is made of](#see-what-the-result-is-made-of)
- [Compare modes](#compare-modes)
- [Change an assumption](#change-an-assumption)
- [Where to next](#where-to-next)

The first cell loads the two things the page uses: pandas for tables and
the session class of the library.

```{code-cell}
import pandas as pd

from cafein.lca import TransportLCA
```

## Compute a first result

A calculation session is a `TransportLCA` object. Created without
arguments, it uses the model's global default assumptions, including the
world average electricity mix. Each mode is identified by a short name;
here it is a battery-electric private car:

```{code-cell}
lca = TransportLCA()
car = lca.calculate("private_car_bev")
car
```

The summary line gives the two headline numbers: greenhouse-gas emissions
in grams of CO₂-equivalent per passenger-kilometre, and energy use in
megajoules per passenger-kilometre. Both are available as plain floats,
shown here with their units:

```{code-cell}
headline = pd.Series(
    {
        "g CO₂e per passenger-km": car.ghg_per_pkm,
        "MJ per passenger-km": car.energy_per_pkm_total,
    }
)
headline.round(2)
```

Every passenger-kilometre by this car costs about 125 g of CO₂e and
1.7 MJ of primary energy over the vehicle's whole life, under the global
default assumptions.

## See what the result is made of

The headline number is the sum of five life-cycle components. `per_pkm`
returns them as a pandas Series in g CO₂e per passenger-km:

```{code-cell}
car.per_pkm.round(1)
```

Each component covers one stage of the vehicle's life:

- **manufacturing**: producing the vehicle body and its battery, assembly,
  disposal and fluids, spread over the vehicle's lifetime mileage;
- **delivery**: moving the finished vehicle from the factory to the point
  of sale;
- **use**: the electricity or fuel consumed while driving, including its
  production upstream of the vehicle;
- **services**: the vans or other vehicles that service a shared fleet,
  zero for a private car;
- **infrastructure**: the share of the road network's construction and
  maintenance attributed to each kilometre driven.

For this car, use dominates and manufacturing is the second largest
component.

## Compare modes

`summary()` computes the same breakdown for every mode and returns one
row per mode. Selecting a few rows makes a comparison:

```{code-cell}
comparison_modes = [
    "private_car_ice",
    "private_car_bev",
    "bus_ice",
    "bus_bev",
    "metro_urban_train",
]

all_modes = lca.summary()
all_modes.loc[comparison_modes].round(1)
```

Under the global defaults, a diesel bus emits a little more than half as
much per passenger-kilometre as a combustion car, and the metro less
again. The differences come mostly from occupancy. The assumed passengers
per vehicle are part of each mode's parameters, which the session can
show:

```{code-cell}
rows = []

for slug in comparison_modes:
    parameters = lca.parameters(slug)
    rows.append({"mode": slug, "passengers per vehicle": parameters.occupancy})

occupancies = pd.DataFrame(rows).set_index("mode")
occupancies
```

A car carries 1.5 people, a bus 17 and a metro train 190, so the same
vehicle emissions are shared by many more passengers.

## Change an assumption

The main assumptions behind a mode, such as occupancy, lifetime, mileage
and energy consumption, are named parameters that can be overridden for a
single calculation; the fixed per-mode data behind them is described in
the modes guide. Raising the car's occupancy from
1.5 to 3 passengers spreads the same vehicle emissions over twice as many
passenger-kilometres:

```{code-cell}
occupancy_settings = [
    ("default", 1.5),
    ("car-pooling", 3.0),
]
rows = []

for label, occupancy in occupancy_settings:
    result = lca.calculate("private_car_bev", occupancy=occupancy)
    rows.append(
        {
            "setting": label,
            "passengers": occupancy,
            "g CO₂e per passenger-km": result.ghg_per_pkm,
        }
    )

occupancy_comparison = pd.DataFrame(rows).round(1)
occupancy_comparison
```

The per-passenger result halves, as expected for a quantity that scales
with occupancy alone. Other parameters, such as the vehicle's lifetime or
its electricity consumption, act on individual components rather than
scaling every component equally; the user guide explains which parameter
drives which component.

## Where to next

- [Reading results](../user_guide/reading_results): the components in
  detail, and the per-vehicle and per-vehicle-km views.
- [Modes and parameters](../user_guide/modes_and_parameters): all 56
  modes and every parameter you can change.
- [Electricity mix](../user_guide/electricity_mix): running the model for
  a country or a custom grid.
- [Sensitivity analysis](../user_guide/sensitivity_analysis): sweeping
  one parameter over a range and ranking which ones matter.
- [Scenarios](../scenarios/scenarios): bundling regional assumptions into
  a reusable file with best, central and worst cases.
