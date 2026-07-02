# cafein-lca

**The ITF "Good to go?" urban transport life-cycle assessment model, as a
Python library.**

`cafein-lca` is a programmatic, tested reimplementation of the life-cycle
assessment workbook published by the International Transport Forum with
Cazzola & Crist (2020), *"Good to Go? Assessing the Environmental Performance
of New Mobility"*. Given a transport mode and optional overrides of any
scenario input — electricity mix, vehicle lifetime, mileage, occupancy,
battery size, servicing logistics — it returns life-cycle energy use and
greenhouse-gas emissions per passenger-km, vehicle-km and vehicle, decomposed
into five components: vehicle and battery manufacturing, vehicle delivery,
vehicle use (including fuel/electricity production), operational services of
shared fleets, and infrastructure.

> **Validation.** The engine reproduces the published ITF workbook exactly:
> every result of all 128 reproducible workbook columns (56 modes plus their
> sensitivity variants) matches the workbook's own computed values within a
> relative tolerance of 1e-9, enforced by the golden-master test suite. The
> few workbook quirks found during extraction are documented in
> [docs/workbook-audit.md](docs/workbook-audit.md).

## Modes covered

Private and shared e-scooters (first and new generation), bikes and e-bikes,
mopeds (ICE/BEV), private cars and large cars (ICE, HEV, PHEV, BEV, FCEV),
taxis, ridesourcing cars, shared vans and minibuses, urban buses
(ICE/HEV/BEV/FCEV) and metro/urban rail — 56 modes in total.

## Installation

```
pip install cafein-lca
```

(Not yet on PyPI; install from source with `pip install .` until 0.1.0 is
released.)

## Quickstart

```python
import cafein_lca
from cafein_lca import TransportLCA

lca = TransportLCA()                      # ITF 2020 global defaults
result = lca.calculate("private_car_bev")

result.ghg_per_pkm        # 125.4 g CO2-eq per passenger-km
result.per_pkm            # GHG by life-cycle component (pandas Series)
result.energy_per_vkm     # energy by component, per vehicle-km
result.to_frame()         # everything: component x (metric, per)

cafein_lca.list_modes()   # all 56 mode slugs with full names
```

Scenario analysis works through typed, immutable parameter objects (every
field mirrors a user-input cell of the workbook), or directly as keyword
overrides:

```python
scooter = cafein_lca.mode("shared_escooter_first_gen")
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
region preset or a fully custom mix. Modes that pin an explicit region (as
some workbook sensitivity cases do) keep it; everything else follows the
session mix — including the servicing vehicles of shared fleets.

```python
lca = TransportLCA(power_mix="EU 28")     # packaged preset

lca = TransportLCA(power_mix={            # custom: Finland 2020
    "oil": 0.004, "natural_gas": 0.054, "coal": 0.080,
    "nuclear": 0.339, "biomass": 0.160, "other_renewables": 0.363,
})
lca.calculate("private_car_bev").ghg_per_pkm   # 70.3 g CO2-eq/pkm

lca.summary()                             # all modes x components, one frame
```

## Relation to the Excel workbook

This repository also carries the source material: the pristine ITF workbook
(`life-cycle-assessment-calculations-2020_original.xlsx`), a copy customized
with the Finland 2020 electricity mix, the report PDF, and a derived CSV of
GHG per pkm by mode. The packaged datasets under `cafein_lca/data/` are
extracted from the pristine workbook by `scripts/extract_workbook.py` and are
regenerated only by that script. The derived CSV doubles as an acceptance
test: the library reproduces it exactly when given the Finland 2020 mix.

## Related tools

- **[carculator](https://github.com/romainsacchi/carculator)** (Paul Scherrer
  Institut) and its siblings — fully parameterized vehicle LCA with
  ecoinvent-style background databases, many midpoint indicators, prospective
  scenarios and Monte Carlo. Use carculator for multi-indicator prospective
  vehicle LCA; use `cafein-lca` for the ITF urban-mobility model — a
  self-contained factor model (GHG + energy, all coefficients packaged, no
  background database) whose distinguishing coverage is the mobility-services
  layer: servicing-van logistics of shared fleets, deadheading of
  ridesourcing and taxis, and infrastructure amortization for all modes.
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
