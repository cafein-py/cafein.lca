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
megajoules per passenger-kilometre. Both are available as plain floats:

```{code-cell}
round(car.ghg_per_pkm, 1)
```

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
component; the battery is a large part of it.

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

Under the global defaults, a full bus emits about half as much per
passenger-kilometre as a private car, and the metro less again. The
differences come mostly from occupancy: the model assumes 1.5 passengers
in a car, 17 in a bus and 190 in a metro train.

## Change an assumption

Every assumption behind a mode is a named parameter, and any of them can
be overridden for a single calculation. Raising the car's occupancy from
1.5 to 3 passengers spreads the same vehicle emissions over twice as many
passenger-kilometres:

```{code-cell}
occupancy_settings = [
    ("default (1.5)", None),
    ("car-pooling (3.0)", 3.0),
]
rows = []

for label, occupancy in occupancy_settings:
    if occupancy is None:
        result = lca.calculate("private_car_bev")
    else:
        result = lca.calculate("private_car_bev", occupancy=occupancy)

    rows.append({"setting": label, "g CO₂e per passenger-km": result.ghg_per_pkm})

occupancy_comparison = pd.DataFrame(rows).round(1)
occupancy_comparison
```

The per-passenger result halves, as expected for a quantity that scales
with occupancy alone. Other parameters, such as the vehicle's lifetime or
its electricity consumption, act on individual components rather than on
the total; the user guide explains which parameter drives which component.

## Where to next

- [Reading results](../user_guide/reading_results): the components in
  detail, and the per-vehicle and per-vehicle-km views.
- [Modes and parameters](../user_guide/modes_and_parameters): all 56
  modes and every parameter you can change.
- [Electricity mix](../user_guide/electricity_mix): running the model for
  a country or a custom grid.
- [Scenarios](../scenarios/scenarios): bundling regional assumptions into
  a reusable file with best, central and worst cases.
