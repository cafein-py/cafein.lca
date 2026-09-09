---
jupytext:
  text_representation:
    format_name: myst
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Modes and parameters

The model covers 56 urban transport modes, each with its own default
parameters. A mode is chosen by its slug and its defaults come back as a
`ModeParameters` object, which is where every changeable assumption
lives.

**How to?**

- [List the modes](#list-the-modes)
- [Inspect a mode's parameters](#inspect-a-modes-parameters)
- [What each parameter controls](#what-each-parameter-controls)
- [Change parameters](#change-parameters)
- [Read validation errors](#read-validation-errors)
- [Inputs fixed per mode](#inputs-fixed-per-mode)
- [Where to next](#where-to-next)

```{code-cell}
import dataclasses

import pandas as pd

import cafein.lca
from cafein.lca import TransportLCA, mode
```

## List the modes

`list_modes()` maps every mode's short name to its full name. The short
names are what you pass to `calculate()`:

```{code-cell}
modes = pd.Series(cafein.lca.list_modes(), name="full name")
modes.head(12)
```

The names follow one pattern: ownership or service model, vehicle, and
powertrain. Grouping them by their first word shows the families:

```{code-cell}
family = modes.index.str.split("_").str[0]
modes.groupby(family).size().rename("modes")
```

- **private** and **shared** cover e-scooters, bicycles, e-bikes and
  mopeds, plus private cars in five powertrains (ICE, HEV, PHEV, BEV,
  FCEV); **large** is the large private car in the same five powertrains;
- **taxi** and **ridesourcing** are cars operated as services, including
  shared vans and minibuses, with empty driving between rides;
- **bus** is an urban bus in five powertrains, and **metro** a metro or
  urban train.

## Inspect a mode's parameters

`mode()` returns the default parameters of one mode as an immutable
object. Every field is a number or a name you could change:

```{code-cell}
units = {
    "lifetime_years": "years",
    "annual_km": "km per year",
    "vehicle_weight_kg": "kg",
    "occupancy": "passengers per vehicle",
    "battery_capacity_kwh": "kWh",
    "fuel_consumption_per_100km": "litres gasoline-equivalent per 100 km",
    "electricity_consumption_kwh_per_km": "kWh per km",
    "hydrogen_consumption_per_100km": "litres gasoline-equivalent per 100 km",
    "electric_driving_share": "share, 0 to 1",
    "service_km_per_vehicle_day": "km per vehicle per day",
    "vehicles_per_service_trip": "vehicles",
}
bus = mode("bus_ice")
rows = []

for name, value in dataclasses.asdict(bus).items():
    if isinstance(value, float):
        value = round(value, 2)
    rows.append({"parameter": name, "value": value, "unit": units.get(name, "")})

bus_parameters = pd.DataFrame(rows).set_index("parameter")
bus_parameters
```

Names such as the fuel type and the production region select a row of a
packaged table and have no unit. The bus is serviced by itself, which is
how the model represents the empty kilometres a bus drives to and from
the depot.

The same object is reachable from a session with
`TransportLCA.parameters()`, which also applies the session's scenario if
one is set; without a scenario the two are identical.

## What each parameter controls

The table below explains every field. "Controls" names the components
whose per-kilometre value changes when the parameter changes; the
per-vehicle-km and per-passenger-km divisions themselves are described
in [Reading results](reading_results). "Source row" is the cell of the
source model's input sheet that the parameter mirrors, for readers who
want to trace a value back.

| Parameter | Unit | Controls | Meaning | Source row |
|---|---|---|---|---|
| `lifetime_years` | years | manufacturing, delivery | Years the vehicle stays in service. Per-vehicle footprints are spread over more kilometres; use and services per kilometre are unchanged. | 0_Total row 4 |
| `annual_km` | km per year | manufacturing, delivery, services | Kilometres driven per year, excluding the empty servicing kilometres that `service_km_per_vehicle_day` adds for self-serviced modes. Also sets the ratio of servicing to driving kilometres. | 0_Total row 5 |
| `vehicle_weight_kg` | kg | manufacturing, delivery, infrastructure | Vehicle mass without the battery; materials scale with it, and for road vehicles the infrastructure calculation compares it with a reference car (rail infrastructure is set directly). | 0_Total row 10 |
| `occupancy` | passengers per vehicle | all, per passenger-km only | Average number of passengers on board; divides every per-vehicle-km value. | 0_Total row 16 |
| `electricity_region` | preset name or `None` | use | A pinned electricity mix for this mode's own electricity; `None` inherits the session mix. Servicing vehicles always use the session mix. | 0_Total row 8 |
| `production_region` | name | manufacturing | Which set of material and battery production intensities applies. | 0_Total row 12 |
| `battery_capacity_kwh` | kWh | manufacturing, delivery | Battery size; drives battery production and the vehicle's delivered mass. | 0_Total row 11 |
| `battery_chemistry` | name | manufacturing | Battery chemistry, which sets specific energy and production intensity. | 0_Total row 13 |
| `hydrogen_pathway` | name | use | How hydrogen is produced, for fuel-cell modes. | 0_Total row 14 |
| `fuel_type` | name | use | The liquid fuel and its well-to-wheel factors. | 3_Use row 14 |
| `fuel_consumption_per_100km` | litres gasoline-equivalent per 100 km | use | Fuel used in combustion driving. | 3_Use row 3 |
| `electricity_consumption_kwh_per_km` | kWh per km | use | Electricity used in electric driving. | 3_Use row 4 |
| `hydrogen_consumption_per_100km` | litres gasoline-equivalent per 100 km | use | Hydrogen used, for fuel-cell modes. The source model expresses hydrogen by its energy content in gasoline-equivalent litres, not in kilograms. | 3_Use row 5 |
| `electric_driving_share` | 0 to 1 | use | Share of kilometres driven electrically; 1 for BEVs, fractional for PHEVs. | 3_Use row 6 |
| `service_vehicle` | mode name or `"None"` | services | Which vehicle services the fleet. When it is the mode's own name, the fleet services itself and the service kilometres are empty driving. | 0_Total row 19 |
| `service_km_per_vehicle_day` | km per vehicle per day | services | Servicing distance per fleet vehicle. | 0_Total row 20 |
| `vehicles_per_service_trip` | count | services | How many fleet vehicles one servicing trip covers. | 0_Total row 21 |

A derived quantity, `lifetime_km`, is the product of lifetime years and
annual kilometres and is available as a property of the parameter object.

## Change parameters

For a single calculation, pass keyword overrides to `calculate()`. The
default bus carries 17 passengers and emits 91.4 g CO₂e per
passenger-km; here it carries 40:

```{code-cell}
lca = TransportLCA()
fuller_bus = lca.calculate("bus_ice", occupancy=40)
round(fuller_bus.ghg_per_pkm, 1)
```

The result, in g CO₂e per passenger-km, falls in proportion to the
occupancy. To reuse a variant, derive a new parameter object with
`replace()`. The original is unchanged; here the bus lifetime rises from
9 to 15 years, and the derived object reports its lifetime kilometres:

```{code-cell}
long_lived_bus = bus.replace(lifetime_years=15)
long_lived_bus.lifetime_km
```

That is 660,000 km over the vehicle's life instead of 396,000. The
variant can be passed to `calculate()` in place of the name:

```{code-cell}
round(lca.calculate(long_lived_bus).ghg_per_pkm, 1)
```

The result is only slightly below the default 91.4 g CO₂e per
passenger-km, because a bus's manufacturing is a small share of its
total; the lifetime matters far more for a short-lived e-scooter.

For a coherent set of changes across many modes, use a scenario file,
described in [Scenarios](../scenarios/scenarios). Keyword overrides win
over a scenario, and a parameter object you built yourself is used
exactly as given.

## Read validation errors

Parameter objects validate their values, so a mistake fails at the point
where it is made rather than in a result. An unknown parameter name lists
the valid ones:

```{code-cell}
try:
    bus.replace(seats=50)
except TypeError as error:
    print(error)
```

The message names the offending keyword, `seats`, and lists every name
that would have been accepted; the bus's seating is not a model input,
and the nearest valid parameter is `occupancy`. A value outside its range
names the field and the value:

```{code-cell}
try:
    bus.replace(occupancy=-1)
except ValueError as error:
    print(error)
```

Quantities must be zero or positive, and `electric_driving_share` must
lie between 0 and 1; the message states the rule the value broke.

## Inputs fixed per mode

Some inputs of the model are fixed per mode and are not exposed as
parameters: the material composition of the vehicle body, the number of
battery replacements over its life, the fluids it uses, the delivery
distances by leg, and the infrastructure type and its material
quantities. They come from the source model's technical specifications
and are packaged as data. Changing them means changing the packaged
tables, which the [model page](../model/model) describes.

The shared environment tables are not parameters either: material and
battery production intensities, fuel and electricity pathway factors, and
the infrastructure material intensities. The electricity mix is the one
environment assumption you set at session level, and it has its own
[guide](electricity_mix).

## Where to next

- [Electricity mix](electricity_mix): presets, custom mixes, and the
  precedence rule for modes that pin a region.
- [Sensitivity analysis](sensitivity_analysis): sweeping a parameter and
  ranking their influence.
- [Scenarios](../scenarios/scenarios): many parameters, many modes, one
  file.
