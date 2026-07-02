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

`cafein-lca` computes life-cycle energy use and greenhouse-gas emissions for
urban transport modes, using the ITF "Good to go?" model. A calculation
session is a {class}`~cafein_lca.TransportLCA` object; with no arguments it
uses the ITF 2020 global defaults.

```{code-cell}
from cafein_lca import TransportLCA

lca = TransportLCA()
result = lca.calculate("private_car_bev")
result
```

Results decompose into the model's five life-cycle components, per
passenger-km, vehicle-km or vehicle:

```{code-cell}
result.per_pkm  # g CO2-eq per passenger-km
```

```{code-cell}
result.to_frame()
```

## Discovering modes

```{code-cell}
import cafein_lca

list(cafein_lca.list_modes())[:10]
```

## Changing scenario inputs

Every user input of the original workbook is a typed parameter. Fetch a
mode's defaults, derive variants with `.replace()` — or pass keyword
overrides directly to `calculate()`:

```{code-cell}
scooter = cafein_lca.mode("shared_escooter_first_gen")
scooter
```

```{code-cell}
short_lived = scooter.replace(lifetime_years=0.5)
lca.calculate(short_lived).ghg_per_pkm
```

```{code-cell}
# sensitivity sweep over e-scooter lifetime
{y: round(lca.calculate(scooter.replace(lifetime_years=y)).ghg_per_pkm, 1)
 for y in (0.5, 1.0, 2.0, 3.0)}
```

## Comparing all modes

```{code-cell}
lca.summary().round(1).head(12)
```
