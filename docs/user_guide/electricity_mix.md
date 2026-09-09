---
jupytext:
  text_representation:
    format_name: myst
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Electricity mix

The electricity generation mix is the one environment assumption you set
for a whole session. It determines the emissions of every kilowatt-hour
the model consumes, charging electric vehicles, producing hydrogen by
electrolysis, and running the electric servicing vehicles of shared
fleets, except where a mode pins its own electricity region for its own
charging.

**How to?**

- [Use a packaged preset](#use-a-packaged-preset)
- [Supply a custom mix](#supply-a-custom-mix)
- [See which results respond](#see-which-results-respond)
- [Which mix takes precedence](#which-mix-takes-precedence)
- [Compare regions](#compare-regions)
- [Where to next](#where-to-next)

The packaged presets are read from `conf.power_mix_catalog`:

```{code-cell}
import matplotlib.pyplot as plt
import pandas as pd

from cafein.lca import TransportLCA
from cafein.lca.config import conf
```

## Use a packaged preset

The session takes the mix as `power_mix`. A string selects one of the
packaged presets, which are the regions of the source model:

```{code-cell}
sources = ["oil", "natural_gas", "coal", "nuclear", "biomass", "other_renewables"]
rows = []

for region, shares in conf.power_mix_catalog.items():
    row = {"region": region}
    for source, share in zip(sources, shares):
        row[source] = share
    rows.append(row)

presets = pd.DataFrame(rows).set_index("region")
presets.round(3)
```

Each row is the share of generation from six sources, summing to one.
`World` is the default. The five `100%` rows are single-source mixes,
useful as bounds. The spelling of `Unitd Kingdom` is the source model's
and is kept so that every packaged number stays traceable.

A session on the EU 28 preset, and the battery-electric car's emissions
on it, in g CO₂e per passenger-km:

```{code-cell}
eu = TransportLCA(power_mix="EU 28")
eu_car = eu.calculate("private_car_bev")
round(eu_car.ghg_per_pkm, 1)
```

On the EU 28 mix a battery-electric car emits about 100 g CO₂e per
passenger-km, a fifth less than the 125 it emits on the world average
under the same defaults.

## Supply a custom mix

A dictionary of the six sources defines any other mix. Sources you leave
out count as zero, and the shares must sum to one. This is Finland's
generation in 2020:

```{code-cell}
finland_2020 = {
    "oil": 0.004,
    "natural_gas": 0.054,
    "coal": 0.080,
    "nuclear": 0.339,
    "biomass": 0.160,
    "other_renewables": 0.363,
}
finland = TransportLCA(power_mix=finland_2020)
finland_car = finland.calculate("private_car_bev")
round(finland_car.ghg_per_pkm, 1)
```

A battery-electric car emits about 70 g CO₂e per passenger-km on
Finland's grid against 125 on the world average, because more than
two-thirds of Finnish generation is nuclear or renewable.

## See which results respond

Three parts of the model consume electricity. Comparing the world mix
with the Finnish one for four modes, component by component, shows which
of them respond. The values are g CO₂e per passenger-km:

```{code-cell}
world = TransportLCA()
response_modes = [
    "private_car_bev",
    "private_car_fcev",
    "shared_escooter_first_gen",
    "private_car_ice",
]
mix_settings = [
    ("World", world),
    ("Finland 2020", finland),
]
rows = []

for slug in response_modes:
    for label, session in mix_settings:
        components = session.calculate(slug).per_pkm
        rows.append(
            {
                "mode": slug,
                "mix": label,
                "use": components["use"],
                "services": components["services"],
                "total": components["total"],
            }
        )

mix_response = pd.DataFrame(rows).set_index(["mode", "mix"]).round(1)
mix_response
```

- The battery-electric car responds through its **use** component.
- The fuel-cell car does not respond, because its default hydrogen
  pathway is natural-gas reforming; only the grid-electrolysis pathway
  follows the mix.
- The shared e-scooter responds through its own charging in the **use**
  component. Its servicing van is diesel-fuelled in the defaults, so the
  **services** component does not move; a fleet serviced by electric vans
  would respond there as well.
- The combustion car does not respond at all.

Servicing vehicles always use the session mix, even for a mode that pins
its own region, because the source model derives their intensities from
its default region.

## Which mix takes precedence

A mode may carry its own `electricity_region`. When it does, that region
wins over the session mix for the mode's use phase. The packaged defaults
leave it unset for every mode, so the session mix applies everywhere; the
parameter exists for sensitivity cases and for scenarios that pin a mode
to a specific grid:

```{code-cell}
pinned = finland.calculate("private_car_bev", electricity_region="100% coal")
round(pinned.ghg_per_pkm, 1)
```

The car now charges on a coal-only grid although the session is Finnish.
The value must be a preset name; a custom mix can only be set at session
level.

## Compare regions

Running one mode across all presets shows how much the grid matters for
an electric vehicle. Each region gets the five components of the
battery-electric car, in g CO₂e per passenger-km, so the chart can show
which of them moves:

```{code-cell}
component_columns = [
    "manufacturing",
    "delivery",
    "use",
    "services",
    "infrastructure",
]
rows = []

for region in conf.power_mix_catalog:
    session = TransportLCA(power_mix=region)
    components = session.calculate("private_car_bev").per_pkm
    row = {"region": region, "total": components["total"]}
    for name in component_columns:
        row[name] = components[name]
    rows.append(row)

by_region = pd.DataFrame(rows).set_index("region").sort_values("total")
by_region.round(1)
```

The use column is the only one that varies; manufacturing, delivery and
infrastructure are identical in every row, and services is zero for a
private car. The same table as a stacked chart:

```{code-cell}

figure, axis = plt.subplots(figsize=(8, 6))
by_region[component_columns].plot(ax=axis, kind="barh", stacked=True)
axis.set_xlabel("g CO₂e per passenger-km")
axis.set_ylabel("Electricity mix")
axis.set_title("Battery-electric private car by electricity mix")
axis.legend(title="Component", frameon=False)
figure.tight_layout()
```

Across the packaged presets the total varies by a factor of about three
and a half, from the cleanest grid to the most carbon-intensive.

## Where to next

- [Sensitivity analysis](sensitivity_analysis): the other parameters
  that matter, and by how much.
- [Scenarios](../scenarios/scenarios): a mix together with per-mode
  assumptions in one reusable file, with best, central and worst cases.
