---
jupytext:
  text_representation:
    format_name: myst
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Scenarios: regional operating conditions

The library's defaults are the source model's global central case. A
*scenario* replaces them with a coherent set of per-mode overrides plus an
electricity mix, defined once in a TOML file. Two scenarios are packaged:

```{code-cell}
import cafein.lca
from cafein.lca import Scenario, TransportLCA

cafein.lca.list_scenarios()
```

Every scenario carries three cases named by their effect on emissions per
passenger-km: `best`, `central` and `worst`. Load one by name (or by path
to your own file) and pass it to the session:

```{code-cell}
india = Scenario.load("india")            # case="central"
lca = TransportLCA(scenario=india)
lca.parameters("bus_ice")
```

```{code-cell}
lca.calculate("bus_ice").per_pkm.round(1)
```

The cases bracket each mode. Compare modes *within* one case; the best
and worst cases stack every optimistic or pessimistic assumption at once,
so they are envelopes rather than likely outcomes:

```{code-cell}
import pandas as pd

modes = ["private_car_ice", "private_car_bev", "private_moped_ice",
         "taxi_ice", "bus_ice", "bus_bev", "metro_urban_train"]
pd.DataFrame({
    case: [TransportLCA(scenario=Scenario.load("india", case=case))
           .calculate(m).ghg_per_pkm for m in modes]
    for case in ("best", "central", "worst")
}, index=modes).round(1)
```

Keyword overrides still win over the scenario, and a parameter object
built by hand is used as given:

```{code-cell}
lca.calculate("bus_ice", occupancy=70).ghg_per_pkm
```

## Writing your own

A scenario file has a `name`, an optional `description`, a `power_mix`
(preset name, table of the six generation shares, or a per-case table of
either) and `[modes.<slug>]` tables. Keys may be canonical slugs or glob
patterns such as `"bus_*"`; exact slugs take precedence. Any value may be
a scalar or a `{best, central, worst}` table:

```toml
name = "my_city"
power_mix = "EU 28"

[modes."bus_*"]
occupancy = {best = 60, central = 30, worst = 15}

[modes.bus_bev]
battery_capacity_kwh = 250
```

Loading validates slugs, parameter names and ranges, so mistakes surface
at `Scenario.load()` rather than in results.

## Notes on the India scenario

The values come from Delhi and Mumbai surveys and Indian LCA studies
(sources are cited in the packaged file). Points to keep in mind:

- **Occupancy** is the strongest lever: 53 passengers per bus against the
  global 17 more than halves bus emissions per pkm, while 1.25 per car
  raises car results by a fifth.
- **Metro** rows describe a six-coach Mumbai train (weight, electricity
  per train-km, occupancy) and must be changed together. Its ridership
  figures are planned, not measured; the worst case takes a quarter of the
  plan.
- **Rated versus measured** consumption differs by 30 to 40 %; measured
  fleet values are used where they exist and rated electric-vehicle
  figures are treated as the best case.
- **CNG**, which fuels most Delhi and Mumbai buses, taxis and
  auto-rickshaws, is not yet a fuel type in the model; ICE modes run on
  gasoline or diesel.
