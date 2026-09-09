---
jupytext:
  text_representation:
    format_name: myst
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Sensitivity analysis

Every assumption is a parameter, so a result can be probed by sweeping
one input across a range while the others stay fixed. Repeating that
sweep across a mode's parameters ranks them by how much each moves the
result.

**How to?**

- [Sweep one parameter](#sweep-one-parameter)
- [Find a break-even occupancy](#find-a-break-even-occupancy)
- [Rank parameters with a tornado chart](#rank-parameters-with-a-tornado-chart)
- [Which parameters matter most per mode](#which-parameters-matter-most-per-mode)
- [Where to next](#where-to-next)

One default session runs every sweep below, so only the swept input
changes from cell to cell:

```{code-cell}
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cafein.lca import TransportLCA, mode

lca = TransportLCA()
```

## Sweep one parameter

The lifetime of a shared e-scooter is the classic uncertain input:
early fleets lasted months, current ones years. Sweeping it from half a
year to four years shows how strongly the per-passenger-km result depends
on it:

```{code-cell}
scooter = mode("shared_escooter_first_gen")
lifetimes = [0.5, 1.0, 1.5, 2.0, 3.0, 4.0]
rows = []

for years in lifetimes:
    result = lca.calculate(scooter.replace(lifetime_years=years))
    rows.append(
        {
            "lifetime (years)": years,
            "manufacturing (g CO₂e per passenger-km)": result.per_pkm["manufacturing"],
            "total (g CO₂e per passenger-km)": result.ghg_per_pkm,
        }
    )

lifetime_sweep = pd.DataFrame(rows).set_index("lifetime (years)").round(1)
lifetime_sweep
```

The manufacturing component falls in proportion to the lifetime because
the same vehicle is spread over more kilometres, while use and
infrastructure per kilometre do not change. Doubling the lifetime from
one to two years removes about a quarter of the total.

## Find a break-even occupancy

A bus beats a car per passenger only when enough people are on board.
The comparison point is the combustion car under the global defaults,
1.5 passengers on board, in g CO₂e per passenger-km:

```{code-cell}
car_per_pkm = lca.calculate("private_car_ice").ghg_per_pkm
round(car_per_pkm, 1)
```

Integer occupancies from 1 to 30 bracket the crossing with the car
baseline:

```{code-cell}
occupancies = np.arange(1, 31)
bus_per_pkm = []

for passengers in occupancies:
    bus = lca.calculate("bus_ice", occupancy=passengers)
    bus_per_pkm.append(bus.ghg_per_pkm)

bus_curve = pd.Series(bus_per_pkm, index=occupancies, name="bus g CO₂e per passenger-km")
bus_curve.round(1).head(12)
```

The bus starts far above the car at one passenger and crosses below it
between 9 and 10. Interpolating between the two nearest samples pins the
crossing down; `np.interp` needs increasing x values and the bus curve
decreases with occupancy, so both arrays are reversed first:

```{code-cell}
emissions_ascending = bus_curve.values[::-1]
occupancies_descending = occupancies[::-1]
break_even = float(np.interp(car_per_pkm, emissions_ascending, occupancies_descending))
round(break_even, 1)
```

The break-even is about 9.6 passengers: below that the bus emits more per
passenger than a car carrying 1.5. Plotting the full curve against the
car baseline puts the crossing in context:

```{code-cell}
figure, axis = plt.subplots(figsize=(8, 5))
axis.plot(bus_curve.index, bus_curve.values, label="Diesel bus")
axis.axhline(car_per_pkm, color="grey", linestyle="--", label="Private car, ICE (1.5 passengers)")
axis.axvline(break_even, color="grey", linestyle=":")
axis.set_xlabel("Bus occupancy (passengers)")
axis.set_ylabel("g CO₂e per passenger-km")
axis.set_ylim(0, 400)
axis.set_title("Break-even occupancy of a diesel bus against a private car")
axis.legend(title="Mode", frameon=False)
figure.tight_layout()
```

The curve is a hyperbola, so the first few passengers cut the bus's
per-passenger emissions far more than the last: the improvement from 1 to
5 passengers dwarfs the improvement from 25 to 30.

## Rank parameters with a tornado chart

To see which inputs a result is most sensitive to, change each parameter
by the same relative amount, one at a time, and record the change in the
result. The sweep covers the six parameters of a battery-electric car
that carry a non-zero value and admit a ±20% change; the zero fuel,
hydrogen and servicing fields and the upper-bounded electric-driving
share are left out:

```{code-cell}
car = mode("private_car_bev")
base = lca.calculate(car).ghg_per_pkm
parameters = [
    "occupancy",
    "lifetime_years",
    "annual_km",
    "vehicle_weight_kg",
    "battery_capacity_kwh",
    "electricity_consumption_kwh_per_km",
]
```

Perturbing each parameter against the same baseline isolates its local
effect:

```{code-cell}
rows = []

for name in parameters:
    default = getattr(car, name)
    lowered = car.replace(**{name: default * 0.8})
    raised = car.replace(**{name: default * 1.2})
    rows.append(
        {
            "parameter": name,
            "change at -20%": lca.calculate(lowered).ghg_per_pkm - base,
            "change at +20%": lca.calculate(raised).ghg_per_pkm - base,
        }
    )

changes = pd.DataFrame(rows).set_index("parameter")
changes.round(1)
```

Each value is the change in g CO₂e per passenger-km from the default
result. Sorting the parameters by the width of their two changes ranks
them:

```{code-cell}
tornado = changes.copy()
tornado["span"] = (tornado["change at +20%"] - tornado["change at -20%"]).abs()
tornado = tornado.sort_values("span")
tornado.columns.name = "g CO₂e per passenger-km"
tornado.round(1)
```

Plotting the two signed changes around zero, sorted by span:

```{code-cell}
figure, axis = plt.subplots(figsize=(8, 5))
axis.barh(tornado.index, tornado["change at -20%"], label="parameter −20%")
axis.barh(tornado.index, tornado["change at +20%"], label="parameter +20%")
axis.axvline(0, color="black", linewidth=0.8)
axis.set_xlabel("Change in g CO₂e per passenger-km")
axis.set_ylabel("Parameter")
axis.set_title("Sensitivity of a battery-electric car to ±20% in six parameters")
axis.legend(title="Parameter change", frameon=False)
figure.tight_layout()
```

Occupancy dominates, followed by electricity consumption. Lifetime and
annual mileage act only on the manufacturing and delivery components,
and the battery size and vehicle weight on those two plus, for the
weight, infrastructure, so their bars are shorter. Occupancy is
asymmetric because the result scales with its inverse.

## Which parameters matter most per mode

The pattern above generalises:

- **Occupancy** matters most for every mode and is the only one
  that scales the whole result.
- **Lifetime and annual mileage** matter where manufacturing is large:
  short-lived shared micromobility, and heavy batteries.
- **Consumption and the electricity mix** matter where use is large:
  cars, buses and trains in daily service.
- **Servicing distance** matters for shared fleets and self-serviced
  services, where empty kilometres add both use-phase emissions and
  dilute occupancy.
- **Infrastructure** has a fixed type and material quantities per vehicle
  class; the resulting emissions scale with vehicle weight against a
  reference car for road vehicles, while for rail they are set directly,
  so weight does not move them.

## Where to next

- [Scenarios](../scenarios/scenarios): store a set of assumptions, with
  best, central and worst cases and their provenance, in one reusable
  file.
- [The model](../model/model): the formulas behind each component.
