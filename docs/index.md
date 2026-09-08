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

The calculation model and its default coefficients are adapted from the
life-cycle assessment model published by the International Transport Forum
with Cazzola & Crist (2020). The library reproduces that model's own
results to within a relative tolerance of 1e-9, and every coefficient it
ships can be traced to the source.

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
files, with an Indian metropolitan case study.
:::

:::{grid-item-card} API reference
:link: reference
:link-type: doc

Every public class and function, generated from the package.
:::

::::

## How the pieces fit

```text
ITF "Good to go?" workbook          the published model and its coefficients
        │
        ▼
packaged coefficients  ◄──── golden tests: every packaged number is held
(cafein/lca/data/)              to the workbook's own computed results
        │
        ▼
TransportLCA(...)                   session assumptions: electricity mix, scenario
        │
        ▼
per vehicle → per vehicle-km → per passenger-km, in five components
        │
        ▼
emission factors for cafein         journeys and matrices with CO₂e per leg
```

The `cafein` routing library uses factors computed this way for its
shipped defaults; a guide on exporting your own factors to it is planned.

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

## Citation

Cite the underlying model when using the numbers:

> Cazzola, P. and P. Crist (2020), *Good to Go? Assessing the Environmental
> Performance of New Mobility*, International Transport Forum, Paris.

This library is an adaptation of an original work by the OECD/ITF. The
opinions expressed and arguments employed in this adaptation should not be
reported as representing the official views of the OECD or of its Member
countries. See [Citing](model/citing) for the software citation and the
data licence.
