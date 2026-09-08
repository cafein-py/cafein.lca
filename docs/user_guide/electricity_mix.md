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
the model consumes: charging electric vehicles, producing hydrogen by
electrolysis, and running the electric servicing vehicles of shared
fleets. This guide shows the packaged presets, how to supply your own
mix, and which results respond.

**How to?**

- [Use a packaged preset](#use-a-packaged-preset)
- [Supply a custom mix](#supply-a-custom-mix)
- [See which results respond](#see-which-results-respond)
- [Understand the precedence rule](#understand-the-precedence-rule)
- [Compare regions](#compare-regions)
- [Where to next](#where-to-next)

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
presets = pd.DataFrame.from_dict(
    conf.power_mix_catalog,
    orient="index",
    columns=["oil", "natural_gas", "coal", "nuclear", "biomass", "other_renewables"],
)
presets.round(3)
```

Each row is the share of generation from six sources, summing to one.
`World` is the default. The five `100%` rows are single-source mixes,
useful as bounds. The spelling of `Unitd Kingdom` is the source model's
and is kept so that every packaged number stays traceable.

```{code-cell}
eu = TransportLCA(power_mix="EU 28")
round(eu.calculate("private_car_bev").ghg_per_pkm, 1)
```

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
round(finland.calculate("private_car_bev").ghg_per_pkm, 1)
```

A battery-electric car emits about 70 g CO₂e per passenger-km on
Finland's grid against 125 on the world average, because more than
two-thirds of Finnish generation is nuclear or renewable.

## See which results respond

Three parts of the model consume electricity. Comparing the world mix
with the Finnish one for three modes shows all three:

```{code-cell}
world = TransportLCA()
response_modes = [
    "private_car_bev",
    "private_car_fcev",
    "shared_escooter_first_gen",
    "private_car_ice",
]
rows = []

for slug in response_modes:
    rows.append(
        {
            "mode": slug,
            "World": world.calculate(slug).ghg_per_pkm,
            "Finland 2020": finland.calculate(slug).ghg_per_pkm,
        }
    )

mix_response = pd.DataFrame(rows).set_index("mode").round(1)
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

## Understand the precedence rule

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
an electric vehicle. The world and single-source rows are kept for
orientation:

```{code-cell}
rows = []

for region in conf.power_mix_catalog:
    session = TransportLCA(power_mix=region)
    rows.append(
        {
            "region": region,
            "g CO₂e per passenger-km": session.calculate("private_car_bev").ghg_per_pkm,
        }
    )

by_region = pd.DataFrame(rows).set_index("region").sort_values("g CO₂e per passenger-km")

figure, axis = plt.subplots(figsize=(8, 6))
axis.barh(by_region.index, by_region["g CO₂e per passenger-km"])
axis.set_xlabel("g CO₂e per passenger-km")
axis.set_title("Battery-electric private car by electricity mix")
figure.tight_layout()
```

The spread between the cleanest and the most carbon-intensive grid is a
factor of about three and a half, and only the use component moves; manufacturing,
delivery and infrastructure are the same bar segment in every region.

## Where to next

- [Sensitivity analysis](sensitivity_analysis): the other parameters
  that matter, and by how much.
- [Scenarios](../scenarios/scenarios): a mix together with per-mode
  assumptions in one reusable file, with best, central and worst cases.
