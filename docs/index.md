# cafein.lca

**Life-cycle assessment of urban passenger transport in Python.**

`cafein.lca` estimates the energy use and greenhouse-gas emissions of one
passenger-kilometre by an urban transport mode, counting the vehicle's
whole life from manufacturing to the road it runs on. It covers 56 modes,
from private e-scooters to metro trains, and reports every result in five
life-cycle components: vehicle and battery manufacturing, delivery, use,
the servicing of shared fleets, and infrastructure. The electricity mix,
vehicle lifetime, mileage, occupancy and the rest are explicit parameters,
so you can recompute a result for a particular city, fleet or policy case
rather than take a global average.

The default coefficients are extracted from a published source workbook,
and the test suite holds the computed results to that workbook across 128
mode columns, with the exceptions listed in the workbook audit. Regional
scenarios replace selected assumptions with sourced local
values while the remaining defaults stay in force.

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} Getting started
:link: getting_started/installation
:link-type: doc

Install the package and compute your first emissions per
passenger-km.
:::

:::{grid-item-card} User guide
:link: user_guide/reading_results
:link-type: doc

What a result is made of, the modes and their parameters, the electricity
mix, and sensitivity analysis.
:::

:::{grid-item-card} Scenarios and case studies
:link: scenarios/scenarios
:link-type: doc

Regional operating conditions as reusable, evidence-tagged scenario
files; an Indian metropolitan scenario is packaged.
:::

:::{grid-item-card} API reference
:link: reference
:link-type: doc

Every public class and function, generated from the package.
:::

::::

## How the pieces fit

```text
default coefficient set             extracted from its source workbook
(cafein/lca/data/)     ◄──── golden tests: computed results match the
        │                       source's own, 128 columns, exceptions audited
        │
        ▼
TransportLCA(...)                   session assumptions: electricity mix, scenario
        │
        ▼
manufacturing, delivery, use, services per vehicle
        │  ÷ lifetime km, + infrastructure per vehicle-km
        ▼
five components per vehicle-km  →  ÷ effective occupancy  →  per passenger-km
                                   (occupancy reduced by empty kilometres)
        │
        ▼
emission factors for cafein         journeys and matrices with CO₂e per leg
```

The `cafein` routing library's current Finland 2020 emission factors are
based on results reported by the source study. A guide on exporting your
own factors to `cafein`, and the regeneration of those defaults directly
from this package, are planned for a later release.

```{toctree}
:hidden:
:caption: Getting started
:maxdepth: 1

getting_started/installation
getting_started/quickstart
```

```{toctree}
:hidden:
:caption: User guide
:maxdepth: 1

user_guide/reading_results
user_guide/modes_and_parameters
user_guide/electricity_mix
user_guide/sensitivity_analysis
```

```{toctree}
:hidden:
:caption: Scenarios and case studies
:maxdepth: 1

scenarios/scenarios
```

```{toctree}
:hidden:
:caption: Model and data
:maxdepth: 1

model/model
model/workbook_audit
model/citing
```

```{toctree}
:hidden:
:caption: Reference
:maxdepth: 1

reference
changelog
```

## Citation and data attribution

The default coefficients originate in the International Transport Forum's
*Good to Go?* study, which must be cited when its numbers are used. The
[Citing](model/citing) page gives the citation, the software citation and
the data licence.
