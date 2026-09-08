# cafein.lca

**Life-cycle assessment of urban passenger transport in Python.**

`cafein.lca` answers one question: how much energy and greenhouse gas does
one passenger-kilometre by a given urban transport mode cost over the
vehicle's whole life? It covers 56 modes, from private e-scooters to metro
trains, and splits every result into five life-cycle components: vehicle
and battery manufacturing, delivery, use, the servicing of shared fleets,
and infrastructure. Assumptions such as the electricity mix, vehicle
lifetime, mileage and occupancy are explicit parameters, so a result can
be recomputed for a city, a fleet or a policy case.

The calculation is a standard attributional life-cycle assessment: the
burdens of producing, delivering, running, servicing and providing
infrastructure for a vehicle, spread over its lifetime kilometres and the
passengers it carries. The library ships a default coefficient set whose
values are traceable to their source, and whose computed results the
test suite holds to that source across 128 mode columns, with the
documented exceptions listed in the workbook audit. Regional scenarios replace selected assumptions with sourced local
values while the remaining defaults stay in force.

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} Getting started
:link: getting_started/installation
:link-type: doc

Install the package and compute your first emissions per passenger-km
in ten minutes.
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
*Good to Go?* study, which must be cited when its numbers are used; the
[Citing](model/citing) page gives the citation, the software citation and
the data licence. This library is an adaptation of an original work by
the OECD/ITF; the opinions expressed and arguments employed in this
adaptation should not be reported as representing the official views of
the OECD or of its Member countries.
