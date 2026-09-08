# The model

`cafein.lca` is an attributional life-cycle assessment model for urban
passenger transport: it accounts for the energy and greenhouse-gas
burdens of a vehicle over its whole life and expresses them per
passenger-kilometre. The accounting steps are the ones common in
transport LCA; the five-stage system boundary and the allocation rules
are explicit choices of this model, described below. The library's
contribution is a tested implementation with explicit parameters, a
documented default coefficient set, and regional scenarios.
This page describes the model's scope, its five stages, how results are
normalised, where the default coefficients come from, and the literature
the method rests on.

**How to?**

- [Scope and functional unit](#scope-and-functional-unit)
- [The five stages](#the-five-stages)
- [Normalisation](#normalisation)
- [Session assumptions](#session-assumptions)
- [Provenance of the default coefficients](#provenance-of-the-default-coefficients)
- [What the library adds](#what-the-library-adds)
- [Background reading](#background-reading)
- [Where to next](#where-to-next)

## Scope and functional unit

The model estimates primary energy use, in megajoules, and greenhouse-gas
emissions, in grams of CO₂-equivalent, for one passenger-kilometre of
urban travel by a given mode. It is a factor model: every stage is a
product of an activity quantity (a kilometre, a kilogram, a kilowatt-hour)
and a coefficient. It has no background database; all coefficients are
packaged as data. Besides the vehicle and its energy, the system boundary
includes the servicing logistics of shared fleets, the empty driving of
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
kilowatt-hour; replacements over the vehicle's life multiply the battery
burden. Fluids are a fixed per-vehicle quantity, scaled with vehicle mass
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
computed from the session electricity mix; the burden is the servicing
distance per fleet vehicle divided by the vehicles covered per trip and
scaled to the fleet vehicle's lifetime kilometres. For self-serviced
modes, where the servicing vehicle is the mode itself (taxis,
ridesourcing, buses), the services component is the mode's own use-phase
burden scaled by the ratio of empty to revenue kilometres: the fuel or
electricity of the empty driving. The empty kilometres also enter the
normalisation below.

**Infrastructure.** Each vehicle class runs on one or two infrastructure
types (bike lane, urban road with or without parking, bus lane, light
rail or metro track), with material quantities per kilometre of network,
a lifetime and a yearly use. The material burden per network-kilometre is
scaled up by the share of network energy that materials represent, spread
over the lifetime use, and allocated to the vehicle class by a
weight-based rule against a reference car; rail classes take their
allocation share directly. Infrastructure is defined per vehicle-kilometre
and has no per-vehicle value.

## Normalisation

The first four stages are computed per vehicle over its life. Per
vehicle-kilometre values divide by the lifetime kilometres, which are
lifetime years times annual kilometres plus the empty kilometres of a
self-serviced fleet. Per passenger-kilometre values divide by an
effective occupancy, the mode's occupancy reduced by the share of empty
kilometres. Infrastructure joins at the per-vehicle-kilometre level.
Because infrastructure has no per-vehicle value, the per-vehicle total is
reported as not available.

## Session assumptions

Two assumptions are set for a session rather than per mode. The
electricity mix applies to every mode that does not pin its own region
and to all servicing vehicles. A scenario, described in the
[Scenarios](../scenarios/scenarios) guide, bundles per-mode parameter
overrides with a mix. Everything else is a parameter of the mode, listed
in [Modes and parameters](../user_guide/modes_and_parameters), or packaged
data.

## Provenance of the default coefficients

All coefficients ship as CSV files inside the package: shared environment
tables (generation mixes, electricity and hydrogen pathways, fuel
factors, material and battery intensities, delivery legs, servicing
vehicle types, infrastructure types) and one table of per-mode
specifications. The default set was extracted once, by a script, from
the calculation workbook that the International Transport Forum
published with its study *Good to Go? Assessing the Environmental
Performance of New Mobility* (Cazzola and Crist, 2020); many of its
coefficients originate in Argonne National Laboratory's GREET model. The
tables are the library's source of truth: the workbook is not
distributed and is not read at runtime. This library is an adaptation of
an original work by the OECD/ITF; the opinions expressed and arguments
employed in this adaptation should not be reported as representing the
official views of the OECD or of its Member countries.

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

## What the library adds

On top of the default coefficient set, the library adds a typed parameter
layer with validation, session-level electricity mixes including custom
ones, the propagation of the session mix to servicing vehicles, and
scenario files with provenance and three cases. None of these change a
default result: a session created without arguments reproduces the
default set's central cases exactly.

## Background reading

The method is common ground in transport LCA. These works cover the
choices the model makes:

- Chester and Horvath (2009). Environmental assessment of passenger transportation should include infrastructure and supply chains. *Environmental Research Letters* 4(2), 024008. https://doi.org/10.1088/1748-9326/4/2/024008. The case for the wide system boundary used here.
- Hawkins et al. (2012). Comparative environmental life cycle assessment of conventional and electric vehicles. *Journal of Industrial Ecology* 17(1), 53–64. https://doi.org/10.1111/j.1530-9290.2012.00532.x. The reference comparison of combustion and battery-electric cars, with the role of the electricity mix and of battery production.
- Nordelöf et al. (2014). Environmental impacts of hybrid, plug-in hybrid, and battery electric vehicles: what can we learn from life cycle assessment? *The International Journal of Life Cycle Assessment* 19(11), 1866–1890. https://doi.org/10.1007/s11367-014-0788-0. A review of how such studies are set up and why their results differ.
- Schäfer and Yeh (2020). A holistic analysis of passenger travel energy and greenhouse gas intensities. *Nature Sustainability* 3(6), 459–462. https://doi.org/10.1038/s41893-020-0514-9. Occupancy explains most of the variation in emissions per passenger-kilometre across modes; in this model it scales every per-passenger-kilometre result directly, which is why it is usually the parameter to examine first.
- Hollingsworth, Copeland and Johnson (2019). Are e-scooters polluters? The environmental impacts of shared dockless electric scooters. *Environmental Research Letters* 14(8), 084031. https://doi.org/10.1088/1748-9326/ab2da8. The servicing and lifetime effects that dominate shared micromobility.
- de Bortoli (2021). Environmental performance of shared micromobility and personal alternatives using integrated modal LCA. *Transportation Research Part D: Transport and Environment* 93, 102743. https://doi.org/10.1016/j.trd.2021.102743. Shared and private micromobility on one footing, including the vehicles' infrastructure.
- Cazzola and Crist (2020). *Good to Go? Assessing the Environmental Performance of New Mobility*. International Transport Forum Policy Papers. https://doi.org/10.1787/f5cd236b-en. The study whose workbook provides the default coefficient set.

## Where to next

- [Workbook audit](workbook_audit): the peculiarities of the source that
  the library reproduces, and the two it does not.
- [Citing](citing): how to cite the model and the software, and the data
  licence.
- [Reading results](../user_guide/reading_results): the components and
  views described here, seen from the user's side.
- [Modes and parameters](../user_guide/modes_and_parameters): every
  parameter and what it controls.
