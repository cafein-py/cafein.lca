---
jupytext:
  text_representation:
    format_name: myst
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Custom electricity mix: Finland 2020

The electricity generation mix is a session-level assumption. The packaged
presets are the regions of the workbook's `Power_Gen_Mix` sheet; any custom
mix is a mapping of the six generation sources to shares summing to 1.

```{code-cell}
from cafein_lca import TransportLCA

finland_2020 = {
    "oil": 0.004, "natural_gas": 0.054, "coal": 0.080,
    "nuclear": 0.339, "biomass": 0.160, "other_renewables": 0.363,
}
world = TransportLCA()                    # workbook default ("World")
finland = TransportLCA(power_mix=finland_2020)
```

The mix drives the use phase of electric modes, hydrogen produced by
electrolysis, and the servicing vehicles of shared fleets:

```{code-cell}
for slug in ("private_car_bev", "metro_urban_train", "shared_escooter_first_gen"):
    print(f"{slug:30s} World: {world.calculate(slug).ghg_per_pkm:6.1f}"
          f"   Finland: {finland.calculate(slug).ghg_per_pkm:6.1f} g/pkm")
```

(Hydrogen modes respond to the mix only when their production pathway is
electrolysis from the grid; the default FCEV pathway is natural-gas
reforming, which is mix-independent.)

Region presets work the same way:

```{code-cell}
TransportLCA(power_mix="EU 28").calculate("private_car_bev").ghg_per_pkm
```

Modes that pin an explicit `electricity_region` (as some workbook
sensitivity cases do) keep it regardless of the session mix — set the
parameter to pin one yourself:

```{code-cell}
finland.calculate("private_car_bev",
                  electricity_region="100% coal").ghg_per_pkm
```
