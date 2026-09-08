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

Because every assumption is a parameter and a calculation is cheap, the
model lends itself to sweeps: change one input over a range and watch the
result. This guide sweeps a lifetime and an occupancy, finds a
break-even, and ranks the influence of a mode's parameters.

**How to?**

- [Sweep one parameter](#sweep-one-parameter)
- [Find a break-even occupancy](#find-a-break-even-occupancy)
- [Rank parameters with a tornado chart](#rank-parameters-with-a-tornado-chart)
- [Know which parameters matter for which modes](#know-which-parameters-matter-for-which-modes)
- [Where to next](#where-to-next)

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
            "manufacturing": result.per_pkm["manufacturing"],
            "total": result.ghg_per_pkm,
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
Sweeping the bus occupancy and interpolating where its emissions cross
the car's gives the break-even:

```{code-cell}
car_per_pkm = lca.calculate("private_car_ice").ghg_per_pkm
occupancies = np.arange(1, 31)
bus_per_pkm = []

for passengers in occupancies:
    bus = lca.calculate("bus_ice", occupancy=passengers)
    bus_per_pkm.append(bus.ghg_per_pkm)

bus_curve = pd.Series(bus_per_pkm, index=occupancies, name="bus g CO₂e per passenger-km")
break_even = np.interp(car_per_pkm, bus_curve.values[::-1], occupancies[::-1])
round(break_even, 1)
```

```{code-cell}
figure, axis = plt.subplots(figsize=(8, 5))
axis.plot(bus_curve.index, bus_curve.values, label="Diesel bus")
axis.axhline(car_per_pkm, color="grey", linestyle="--", label="Private car, ICE (1.5 passengers)")
axis.axvline(break_even, color="grey", linestyle=":")
axis.set_xlabel("Bus occupancy (passengers)")
axis.set_ylabel("g CO₂e per passenger-km")
axis.set_title("Break-even occupancy of a diesel bus against a private car")
axis.legend(frameon=False)
figure.tight_layout()
```

Under the global defaults a diesel bus needs roughly ten passengers to
match a car carrying 1.5 people. The curve is a hyperbola, so the first
few passengers matter far more than the last few.

## Rank parameters with a tornado chart

To see which inputs a result is most sensitive to, change each parameter
by the same relative amount, one at a time, and record the change in the
result. Here every numeric parameter of a battery-electric car moves by
20% in each direction:

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
rows = []

for name in parameters:
    default = getattr(car, name)
    low = lca.calculate(car.replace(**{name: default * 0.8})).ghg_per_pkm
    high = lca.calculate(car.replace(**{name: default * 1.2})).ghg_per_pkm
    rows.append(
        {
            "parameter": name,
            "-20%": low - base,
            "+20%": high - base,
        }
    )

tornado = pd.DataFrame(rows).set_index("parameter")
tornado["span"] = (tornado["+20%"] - tornado["-20%"]).abs()
tornado = tornado.sort_values("span")
tornado.round(1)
```

```{code-cell}
figure, axis = plt.subplots(figsize=(8, 5))
axis.barh(tornado.index, tornado["-20%"], label="parameter −20%")
axis.barh(tornado.index, tornado["+20%"], label="parameter +20%")
axis.axvline(0, color="black", linewidth=0.8)
axis.set_xlabel("Change in g CO₂e per passenger-km")
axis.set_title("Sensitivity of a battery-electric car to ±20% in each parameter")
axis.legend(frameon=False)
figure.tight_layout()
```

Occupancy dominates, followed by electricity consumption. Lifetime and
annual mileage act only on the manufacturing and delivery components,
and the battery size and vehicle weight on those two plus, for the
weight, infrastructure, so their bars are shorter. Occupancy is
asymmetric because the result scales with its inverse.

## Know which parameters matter for which modes

The pattern above generalises:

- **Occupancy** is the strongest lever for every mode and the only one
  that scales the whole result.
- **Lifetime and annual mileage** matter where manufacturing is large:
  short-lived shared micromobility, and heavy batteries.
- **Consumption and the electricity mix** matter where use is large:
  cars, buses and trains in daily service.
- **Servicing distance** matters for shared fleets and self-serviced
  services, where empty kilometres add both use-phase emissions and
  dilute occupancy.
- **Infrastructure** is fixed per vehicle class and moves only with
  vehicle weight, through the allocation rule.

## Where to next

- [Scenarios](../scenarios/scenarios): turn a set of assumptions into a
  named, reusable file with best, central and worst cases, so that
  sensitivity becomes part of the result rather than an afterthought.
- [The model](../model/model): the formulas behind each component.
