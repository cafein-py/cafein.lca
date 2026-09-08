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

The model covers 56 urban transport modes, each defined by a set of named
parameters with default values. This guide lists the modes, explains what
every parameter controls, and shows the three ways to change one.

**How to?**

- [List the modes](#list-the-modes)
- [Inspect a mode's parameters](#inspect-a-modes-parameters)
- [Understand each parameter](#understand-each-parameter)
- [Change parameters](#change-parameters)
- [Read validation errors](#read-validation-errors)
- [Know what is not a parameter](#know-what-is-not-a-parameter)
- [Where to next](#where-to-next)

```{code-cell}
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
  mopeds, plus private cars in two sizes and five powertrains (ICE, HEV,
  PHEV, BEV, FCEV);
- **taxi** and **ridesourcing** are cars operated as services, including
  shared vans and minibuses, with empty driving between rides;
- **bus** is an urban bus in five powertrains, and **metro** a metro or
  urban train.

## Inspect a mode's parameters

`mode()` returns the default parameters of one mode as an immutable
object. Every field is a number or a name you could change:

```{code-cell}
bus = mode("bus_ice")
bus
```

The same object is reachable from a session with
`TransportLCA.parameters()`, which also applies the session's scenario if
one is set; without a scenario the two are identical.

## Understand each parameter

The table below explains every field. "Controls" names the component the
parameter acts on; occupancy and the lifetime fields act on all of them
through the per-vehicle-km and per-passenger-km divisions described in
[Reading results](reading_results).

| Parameter | Unit | Controls | Meaning |
|---|---|---|---|
| `lifetime_years` | years | all, via lifetime km | Years the vehicle stays in service. |
| `annual_km` | km per year | all, via lifetime km | Kilometres driven per year in revenue service, including cruising for shared modes. |
| `vehicle_weight_kg` | kg | manufacturing, delivery, infrastructure | Vehicle mass without the battery; materials scale with it, and the infrastructure allocation compares it with a reference car. |
| `occupancy` | passengers per vehicle-km | all, via per-pkm division | Average passengers on board. |
| `electricity_region` | preset name or `None` | use, services | A pinned electricity mix for this mode; `None` inherits the session mix. |
| `production_region` | name | manufacturing | Which set of material and battery production intensities applies. |
| `battery_capacity_kwh` | kWh | manufacturing, delivery | Battery size; drives battery production and the vehicle's delivered mass. |
| `battery_chemistry` | name | manufacturing | Battery chemistry, which sets specific energy and production intensity. |
| `hydrogen_pathway` | name | use | How hydrogen is produced, for fuel-cell modes. |
| `fuel_type` | name | use | The liquid fuel and its well-to-wheel factors. |
| `fuel_consumption_per_100km` | litres gasoline-equivalent per 100 km | use | Fuel used in combustion driving. |
| `electricity_consumption_kwh_per_km` | kWh per km | use | Electricity used in electric driving. |
| `hydrogen_consumption_per_100km` | litres gasoline-equivalent per 100 km | use | Hydrogen used, for fuel-cell modes. |
| `electric_driving_share` | 0 to 1 | use | Share of kilometres driven electrically; 1 for BEVs, fractional for PHEVs. |
| `service_vehicle` | mode name or `"None"` | services | Which vehicle services the fleet. When it is the mode's own name, the fleet services itself and the service kilometres are empty driving. |
| `service_km_per_vehicle_day` | km per vehicle per day | services | Servicing distance per fleet vehicle. |
| `vehicles_per_service_trip` | count | services | How many fleet vehicles one servicing trip covers. |

A derived quantity, `lifetime_km`, is the product of lifetime years and
annual kilometres and is available as a property of the parameter object.

## Change parameters

There are three ways to change a parameter, and they compose. For a
single calculation, pass keyword overrides to `calculate()`:

```{code-cell}
lca = TransportLCA()
fuller_bus = lca.calculate("bus_ice", occupancy=40)
round(fuller_bus.ghg_per_pkm, 1)
```

To reuse a variant, derive a new parameter object with `replace()`. The
original is unchanged, and the variant can be passed to `calculate()` in
place of the name:

```{code-cell}
long_lived_bus = bus.replace(lifetime_years=15, annual_km=60000)
long_lived_bus.lifetime_km
```

```{code-cell}
round(lca.calculate(long_lived_bus).ghg_per_pkm, 1)
```

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

A value outside its range names the field and the value:

```{code-cell}
try:
    bus.replace(occupancy=-1)
except ValueError as error:
    print(error)
```

## Know what is not a parameter

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
