# The model

`cafein.lca` is an attributional life-cycle assessment model for urban
passenger transport: it accounts for the energy use and greenhouse-gas
emissions of a vehicle over its whole life and expresses them per
passenger-kilometre. It covers five stages:
manufacturing, delivery, use, operational services, and infrastructure.

**How to?**

- [Scope and functional unit](#scope-and-functional-unit)
- [The five stages](#the-five-stages)
- [Normalisation](#normalisation)
- [Session assumptions](#session-assumptions)
- [Provenance of the default coefficients](#provenance-of-the-default-coefficients)
- [Coefficient sets](#coefficient-sets)
- [What the library adds](#what-the-library-adds)
- [Background reading](#background-reading)
- [Where to next](#where-to-next)

## Scope and functional unit

The model estimates primary energy use, in megajoules, and greenhouse-gas
emissions, in grams of CO₂-equivalent, for one passenger-kilometre of
urban travel by a given mode. It is a factor model: every stage is a
product of an activity quantity (a kilometre, a kilogram, a kilowatt-hour)
and a coefficient. It has no background database; all coefficients are
packaged as data. Besides the vehicle and its energy, the model also
counts the servicing logistics of shared fleets, the empty driving of
taxis and ridesourcing, and the infrastructure of every mode, items that
narrower vehicle assessments often omit, following the argument of
Chester and Horvath (2009) that passenger-transport assessments should
include infrastructure and supply chains.

The 56 modes are the central cases of the default coefficient set. Its
source also carries sensitivity variants of many modes; those are not
exposed as modes, but they are used in the library's tests.

## The five stages

**Manufacturing.** The vehicle body is split into eleven material classes
with per-mode mass shares. Each class has a production energy and
emission intensity per kilogram, with separate virgin and recycled
intensities for steel and aluminium combined through fixed recycled
shares, and a choice between two production regions that differ in
aluminium smelting. Assembly and disposal add a per-kilogram intensity
each. The battery is sized by capacity and chemistry: chemistry gives the
specific energy, hence the battery mass, and production intensities per
kilowatt-hour; replacements over the vehicle's life multiply the battery's
footprint. Fluids are a fixed per-vehicle quantity, scaled with vehicle mass
for some modes.

**Delivery.** The finished vehicle, body plus battery, travels from
factory to point of sale over up to ten legs (air, ship, two rail, two
heavy-truck, two medium-truck, two van legs), each with a per-mode
distance and an energy intensity per tonne-kilometre and an emission
factor per megajoule.

**Use.** Fuel, electricity and hydrogen consumption per kilometre are
converted to energy and multiplied by well-to-wheel factors: a fuel's
well-to-tank energy overhead and its greenhouse-gas intensity, the
electricity mix's primary-energy factor and grid intensity, and the
hydrogen pathway's factors, which for grid electrolysis follow the mix.
Plug-in hybrids split kilometres between fuel and electricity by the
electric driving share. The stage is computed over the vehicle's lifetime
kilometres.

**Operational services.** Shared micromobility is serviced by a van or
car of a given type, whose well-to-wheel intensity per kilometre is
computed from the session electricity mix; its footprint is the servicing
distance per fleet vehicle divided by the vehicles covered per trip and
scaled to the fleet vehicle's lifetime kilometres. For self-serviced
modes, where the servicing vehicle is the mode itself (taxis,
ridesourcing, buses), the services component is the mode's own use-phase
footprint scaled by the ratio of empty to revenue kilometres: the fuel or
electricity of the empty driving. The empty kilometres also enter the
normalisation below.

**Infrastructure.** Each vehicle class runs on one or two infrastructure
types (bike lane, urban road with or without parking, bus lane, light
rail or metro track), with material quantities per kilometre of network,
a lifetime and a yearly use. The materials' energy and emissions per
network-kilometre are scaled up by the share of network energy that
materials represent, spread over the lifetime use, and allocated to each
vehicle class — that is, charged to the class according to its weight
relative to a reference car; rail classes take their allocation share
directly. Infrastructure is defined per
vehicle-kilometre and has no per-vehicle value.

## Normalisation

Normalisation puts the stages on a common per-passenger-kilometre basis by
dividing through the activity they are spread over. The first four stages
are computed per vehicle over its life. Per vehicle-kilometre values divide
by the lifetime kilometres, which are
lifetime years times annual kilometres plus the empty kilometres of a
self-serviced fleet. Per passenger-kilometre values divide by an
effective occupancy, the mode's occupancy reduced by the share of empty
kilometres. Infrastructure joins at the per-vehicle-kilometre level.
Because infrastructure has no per-vehicle value, the per-vehicle total is
reported as not available.

## Session assumptions

A few assumptions are set for a session rather than per mode. The
electricity mix applies to every mode that does not pin its own region
and to all servicing vehicles. A scenario, described in the
[Scenarios](../scenarios/scenarios) guide, bundles per-mode parameter
overrides with a mix. The coefficient set (below) is likewise chosen for
the session. Everything else is a parameter of the mode, listed in
[Modes and parameters](../user_guide/modes_and_parameters), or packaged
data.

## Provenance of the default coefficients

All coefficients ship as CSV files inside the package: shared environment
tables (generation mixes, electricity and hydrogen pathways, fuel
factors, material and battery intensities, delivery legs, servicing
vehicle types, infrastructure types) and one table of per-mode
specifications. The default set, `itf-2020`, was extracted once, by a
script, from the calculation workbook that the International Transport Forum
published with its study *Good to Go? Assessing the Environmental
Performance of New Mobility* (Cazzola and Crist, 2020); many of its
coefficients originate in Argonne National Laboratory's GREET model. The
tables are the library's source of truth: the workbook is not
distributed and is not read at runtime.

The default set is held to its source by a golden-master test suite. For
128 mode columns of the workbook (the 56 modes plus their sensitivity
variants), every energy and emission value in every view is compared
with the value the workbook itself computes and must agree within a
relative tolerance of 1e-9. The scope has two documented exceptions. One
column is excluded because the source derives its results by scaling
another column rather than from its own stages, and an empty placeholder
column is skipped. And four e-scooter sensitivity columns whose
infrastructure rows in the source point at the wrong column are compared
with the source's own per-column infrastructure sheet instead, which
differs from the misaligned totals by about 0.1 % on that component
alone. Apart from that documented correction, the default set changes
nothing in the source's arithmetic, so a handful of peculiarities of the
source are reproduced as published; they are listed, with their effect, in
the [workbook audit](workbook_audit). Regional scenarios and future
coefficient sets replace these defaults value by value, each with its own
provenance.

## Coefficient sets

The packaged tables are a named coefficient set. The default is `itf-2020`
— the tables above — under `cafein/lca/data/itf-2020/`, with a
`manifest.toml` that records its source, version, extraction date and
licence. `available_coefficient_sets()` lists the sets a build ships, and
`TransportLCA(coefficients="itf-2020")` selects one: the argument, else a
scenario file's `coefficients` key, else the default. `Result.coefficient_set`
records which set produced a result. This release ships a single set, so a
process uses `itf-2020` throughout; naming it explicitly lets later sets,
sourced from other data, coexist with their own manifest and their own
tests, and lets the golden-master and acceptance suites guard the `itf-2020`
baseline by name.

## What the library adds

The library wraps the default coefficient set in a few behaviours the
workbook does not have. Parameters are validated as they are set. The
electricity mix is chosen per session, custom mixes included, and it
also drives the servicing vehicles of shared fleets. Scenario files
supply per-mode overrides with their provenance and three cases. None of
this changes a default result: a session created without arguments
reproduces the
default set's central cases exactly.

## Background reading

The wide scope follows Chester and Horvath (2009), who argued
that passenger-transport assessments should count infrastructure and
supply chains, not the vehicle alone. For the road vehicles themselves,
Hawkins et al. (2012) is the reference comparison of combustion and
battery-electric cars and shows how much the result turns on the
electricity mix and on battery production, while Nordelöf et al. (2014)
review why studies of the same vehicles reach such different numbers.
Two findings shape which parameters matter most here: Schäfer and Yeh
(2020) show that occupancy explains most of the variation in emissions
per passenger-kilometre across modes, and Hollingsworth et al. (2019)
and de Bortoli (2021) trace the servicing and lifetime effects that
dominate shared micromobility. The default coefficients come from the
workbook of Cazzola and Crist (2020).

- Cazzola, P. and Crist, P. (2020). *Good to Go? Assessing the Environmental Performance of New Mobility*. International Transport Forum Policy Papers. https://doi.org/10.1787/f5cd236b-en
- Chester, M. and Horvath, A. (2009). Environmental assessment of passenger transportation should include infrastructure and supply chains. *Environmental Research Letters* 4(2), 024008. https://doi.org/10.1088/1748-9326/4/2/024008
- de Bortoli, A. (2021). Environmental performance of shared micromobility and personal alternatives using integrated modal LCA. *Transportation Research Part D: Transport and Environment* 93, 102743. https://doi.org/10.1016/j.trd.2021.102743
- Hawkins, T. R. et al. (2012). Comparative environmental life cycle assessment of conventional and electric vehicles. *Journal of Industrial Ecology* 17(1), 53–64. https://doi.org/10.1111/j.1530-9290.2012.00532.x
- Hollingsworth, J., Copeland, B. and Johnson, J. X. (2019). Are e-scooters polluters? The environmental impacts of shared dockless electric scooters. *Environmental Research Letters* 14(8), 084031. https://doi.org/10.1088/1748-9326/ab2da8
- Nordelöf, A. et al. (2014). Environmental impacts of hybrid, plug-in hybrid, and battery electric vehicles: what can we learn from life cycle assessment? *The International Journal of Life Cycle Assessment* 19(11), 1866–1890. https://doi.org/10.1007/s11367-014-0788-0
- Schäfer, A. W. and Yeh, S. (2020). A holistic analysis of passenger travel energy and greenhouse gas intensities. *Nature Sustainability* 3(6), 459–462. https://doi.org/10.1038/s41893-020-0514-9

## Where to next

- [Workbook audit](workbook_audit): the peculiarities of the source that
  the library reproduces, and the two it does not.
- [Citing](citing): how to cite the model and the software, and the data
  licence.
- [Reading results](../user_guide/reading_results): the components and
  views described here, seen from the user's side.
- [Modes and parameters](../user_guide/modes_and_parameters): every
  parameter and what it controls.
