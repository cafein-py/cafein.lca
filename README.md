# cafein.lca

**Life-cycle assessment of urban passenger transport in Python.**

`cafein.lca` computes life-cycle energy use and greenhouse-gas emissions of
urban transport modes per passenger-km, vehicle-km and vehicle, decomposed
into five components: vehicle and battery manufacturing, vehicle delivery,
vehicle use (including fuel and electricity production), operational services
of shared fleets, and infrastructure. Given a mode and optional overrides of
any scenario input — electricity mix, vehicle lifetime, mileage, occupancy,
battery size, servicing logistics — it returns the results as pandas objects.

The calculation model and its default coefficients are adapted from the
life-cycle assessment model published by the International Transport Forum
with Cazzola & Crist (2020), *Good to Go? Assessing the Environmental
Performance of New Mobility*. `cafein.lca` is an independent reimplementation
of that model, not an ITF or OECD product; see the attribution note at the
end.

`cafein.lca` is part of the [cafein](https://github.com/cafein-py) family of
packages. It installs and runs on its own and does not require the `cafein`
core package.

> **Validation.** The engine is tested against the values computed by the
> source workbook: for all 128 reproducible mode columns (56 modes plus their
> sensitivity variants) every result agrees within a relative tolerance of
> 1e-9. Quirks of the source model found during extraction are documented in
> [docs/workbook-audit.md](docs/workbook-audit.md).

## Modes covered

Private and shared e-scooters (first and new generation), bikes and e-bikes,
mopeds (ICE/BEV), private cars and large cars (ICE, HEV, PHEV, BEV, FCEV),
taxis, ridesourcing cars, shared vans and minibuses, urban buses
(ICE/HEV/BEV/FCEV) and metro/urban rail — 56 modes in total.

## Installation

```
pip install cafein.lca
```

(Not yet on PyPI; install from source with `pip install .` until 0.1.0 is
released.)

## Quickstart

```python
import cafein.lca
from cafein.lca import TransportLCA

lca = TransportLCA()                      # packaged global defaults
result = lca.calculate("private_car_bev")

result.ghg_per_pkm        # 125.4 g CO2-eq per passenger-km
result.per_pkm            # GHG by life-cycle component (pandas Series)
result.energy_per_vkm     # energy by component, per vehicle-km
result.to_frame()         # everything: component x (metric, per)

cafein.lca.list_modes()   # all 56 mode slugs with full names
```

Scenario analysis works through typed, immutable parameter objects (every
field mirrors a user input of the source model), or directly as keyword
overrides:

```python
scooter = cafein.lca.mode("shared_escooter_first_gen")
scooter = scooter.replace(lifetime_years=2.0, battery_capacity_kwh=0.25)
lca.calculate(scooter)

# equivalent sugar:
lca.calculate("shared_escooter_first_gen", lifetime_years=2.0,
              battery_capacity_kwh=0.25)

# sensitivity sweeps fall out naturally:
[lca.calculate(scooter.replace(lifetime_years=y)).ghg_per_pkm
 for y in (0.5, 1.0, 2.0, 3.0)]
```

The electricity generation mix is a session-level assumption: pass a packaged
region preset or a fully custom mix. Modes that pin an explicit region keep
it; everything else follows the session mix — including the servicing
vehicles of shared fleets.

```python
lca = TransportLCA(power_mix="EU 28")     # packaged preset

lca = TransportLCA(power_mix={            # custom: Finland 2020
    "oil": 0.004, "natural_gas": 0.054, "coal": 0.080,
    "nuclear": 0.339, "biomass": 0.160, "other_renewables": 0.363,
})
lca.calculate("private_car_bev").ghg_per_pkm   # 70.3 g CO2-eq/pkm

lca.summary()                             # all modes x components, one frame
```

## Provenance of the coefficients

The packaged datasets under `cafein/lca/data/` and the golden fixtures under
`tests/data/` were extracted from the source workbook and are the library's
source of truth. The golden-master suite pins every packaged number to the
workbook's own computed results, and an acceptance test reproduces a
GHG-per-pkm table produced from the workbook with the Finland 2020
electricity mix.

## Related tools

- **[carculator](https://github.com/romainsacchi/carculator)** (Paul Scherrer
  Institut) and its siblings — fully parameterized vehicle LCA with
  ecoinvent-style background databases, many midpoint indicators, prospective
  scenarios and Monte Carlo. Use carculator for multi-indicator prospective
  vehicle LCA; use `cafein.lca` for a self-contained factor model (GHG and
  energy, all coefficients packaged, no background database) whose
  distinguishing coverage is the mobility-services layer: servicing-van
  logistics of shared fleets, deadheading of ridesourcing and taxis, and
  infrastructure amortization for all modes.
- **Brightway2 / lca_algebraic** — general LCA frameworks; this library
  deliberately stays a lightweight domain model on plain pandas.

## Data attribution and license

The Python code is MIT-licensed. The packaged datasets are extracted from the
ITF workbook © OECD/ITF 2020, used and adapted with citation under the OECD
terms and conditions; several coefficients within it derive from Argonne
National Laboratory's [GREET](https://greet.anl.gov/) model. Cite the
original work when using the numbers:

> Cazzola, P. and P. Crist (2020), *Good to Go? Assessing the Environmental
> Performance of New Mobility*, International Transport Forum, Paris.
> https://www.itf-oecd.org/good-go-assessing-environmental-performance-new-mobility

This library is an adaptation of an original work by the OECD/ITF. The
opinions expressed and arguments employed in this adaptation should not be
reported as representing the official views of the OECD or of its Member
countries.
