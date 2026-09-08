# cafein.lca

**Life-cycle assessment of urban passenger transport in Python.**

`cafein.lca` computes life-cycle energy use and greenhouse-gas emissions
of urban transport modes per passenger-km and per vehicle-km, decomposed
into vehicle and battery manufacturing, delivery, use, the servicing of
shared fleets, and infrastructure; the first four are also available per
vehicle. It covers 56 modes, from
private e-scooters to metro trains. The main assumptions behind a result
are named parameters (electricity mix, vehicle lifetime, mileage,
occupancy, battery size, servicing logistics), while the per-mode
technical data and the shared coefficient tables ship as packaged data.

The calculation is a standard attributional life-cycle assessment. The
default coefficient set is extracted from the International Transport
Forum's *Good to Go?* study (see the attribution below) and is held to
that source by the test suite. Regional scenarios replace selected
assumptions, such as occupancy, lifetimes and mileage, with sourced local
values while the remaining defaults stay in force; complete alternative
coefficient sets for other countries are the next step.

`cafein.lca` is part of the [cafein](https://github.com/cafein-py) family
of packages. It installs and runs on its own and does not require the
`cafein` core package.

## Installation

Until the first release is on PyPI, install from the repository:

```
pip install git+https://github.com/cafein-py/cafein.lca.git
```

Once 0.1.0 is released, `pip install cafein.lca` will do the same.

## Example

A session holds the electricity mix, and a calculation returns the
result for one mode. This computes the life-cycle emissions of a
battery-electric car on the EU 28 grid, in g CO₂e per passenger-km:

```python
from cafein.lca import TransportLCA

lca = TransportLCA(power_mix="EU 28")
car = lca.calculate("private_car_bev")
round(car.ghg_per_pkm, 1)
```

The result splits into five life-cycle components, mode parameters such
as occupancy can be overridden per calculation, the electricity mix and
a scenario are chosen when the session is created, and `summary()` gives
one row per mode; the guides below show each of these.

Regional operating conditions come as scenario files with best, central
and worst cases, each value tagged with its evidence and source; an
Indian metropolitan scenario is packaged.

## Documentation

The documentation at https://cafein-lca.readthedocs.io covers:

- [Getting started](https://cafein-lca.readthedocs.io/en/latest/getting_started/installation.html):
  installation and a ten-minute quickstart.
- [User guide](https://cafein-lca.readthedocs.io/en/latest/user_guide/reading_results.html):
  reading results, modes and parameters, the electricity mix, sensitivity
  analysis.
- [Scenarios](https://cafein-lca.readthedocs.io/en/latest/scenarios/scenarios.html):
  reusable, evidence-tagged assumption bundles.
- [The model](https://cafein-lca.readthedocs.io/en/latest/model/model.html):
  scope, stages, normalisation, provenance of the coefficients, and the
  [audit](docs/model/workbook_audit.md) of the source model.
- [API reference](https://cafein-lca.readthedocs.io/en/latest/reference.html).

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
