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
india = Scenario.load("india_metropolitan")            # case="central"
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
    case: [TransportLCA(scenario=Scenario.load("india_metropolitan", case=case))
           .calculate(m).ghg_per_pkm for m in modes]
    for case in ("best", "central", "worst")
}, index=modes).round(1)
```

Every override carries its provenance: evidence type (`observed`,
`model_input`, `capacity`, `projection`, `derived` or `assumption`),
geography, source, confidence and a note. Print it before trusting a case:

```{code-cell}
india.provenance().query("mode == 'bus_ice'").set_index("parameter")[
    ["value", "evidence", "geography", "confidence"]]
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
patterns such as `"bus_*"`; exact slugs take precedence. A parameter is a
scalar, a table with `value` plus provenance, or a table with the three
cases plus provenance; `evidence`, `geography` and `source` may be per
case:

```toml
name = "my_city"
power_mix = "EU 28"

[modes.bus_bev]
battery_capacity_kwh = 250

[modes."bus_*".occupancy]
best = 60
central = 30
worst = 15
evidence = {best = "assumption", central = "observed", worst = "assumption"}
geography = "my city"
source = "operator report 2024"
confidence = "medium"
```

Loading validates slugs, parameter names and ranges, the evidence and
confidence vocabularies, and the completeness of case tables, so mistakes
surface at `Scenario.load()` rather than in results.

The case names describe the emissions outcome, so the *direction* of each
parameter differs. Put the low-emission value under `best` whatever its
magnitude:

| Parameter | `best` | `worst` |
|---|---|---|
| occupancy, annual_km | high | low |
| lifetime_years | long | short |
| vehicle_weight_kg, battery_capacity_kwh | light, small | heavy, large |
| fuel and electricity consumption | low | high |
| service_km_per_vehicle_day | low | high |
| power_mix | clean | carbon-intensive |

A long lifetime lowers manufacturing emissions per km by allocation only;
it does not make the vehicle better. The packaged-scenario tests check that
emissions per pkm come out ordered best ≤ central ≤ worst for every mode.

## Notes on the `india_metropolitan` scenario

The values are a composite of Delhi and Mumbai surveys and Indian LCA
studies, not national observations; the geography of every value is in
its provenance. Points to keep in mind:

- **Occupancy** is the strongest lever: 53 passengers per bus against the
  global 17 more than halves bus emissions per pkm, while 1.25 per car
  raises car results by a fifth.
- **Metro** rows describe a six-coach Mumbai train (weight, electricity
  per train-km, occupancy) and must be changed together. Its ridership
  figures are planned, not measured; the worst case takes a quarter of the
  plan.
- **Rated versus measured** consumption differs by 30 to 40 %; measured
  fleet values are used where they exist. Electric-vehicle consumption is
  derived from rated range and the hot- and cold-weather penalties
  reported by Peshin et al. (2022); no measured Indian value exists in the
  sources, so its confidence is low.
- **Bus occupancy 53 against the global 17** is the single largest change
  and comes from a Mumbai LCA's operating assumptions (Shinde et al.
  2019); the central bus result of about 23 g CO2-eq/pkm compares with
  the 17 g that study reports under its own system boundary.
- **CNG**, which fuels most Delhi and Mumbai buses, taxis and
  auto-rickshaws, is not yet a fuel type in the model; ICE modes run on
  gasoline or diesel.
