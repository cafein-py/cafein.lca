# The model

`cafein.lca` implements the life-cycle assessment model that the
International Transport Forum published with the report *Good to Go?
Assessing the Environmental Performance of New Mobility* (Cazzola & Crist,
2020). The report's calculation tool is a spreadsheet; this library is a
reimplementation of its arithmetic on top of the same coefficients. This
page describes the model's scope, its five stages, how results are
normalised, and how the library keeps faith with the source.

## Scope and functional unit

The model estimates primary energy use, in megajoules, and greenhouse-gas
emissions, in grams of CO₂-equivalent, for one passenger-kilometre of
urban travel by a given mode. It is a factor model: every stage is a
product of an activity quantity (a kilometre, a kilogram, a kilowatt-hour)
and a coefficient. It has no background database; all coefficients are
packaged, most of them originating in Argonne National Laboratory's GREET
model. Its distinguishing coverage is the mobility-services layer that
vehicle LCAs usually leave out: the servicing logistics of shared fleets,
the empty driving of taxis and ridesourcing, and infrastructure for every
mode.

The 56 modes are the report's central cases. The source also carries
sensitivity variants of many modes; those are not exposed as modes, but
they are used in the library's tests.

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
scaled to the fleet vehicle's lifetime kilometres. Self-serviced modes,
where the servicing vehicle is the mode itself, instead add empty
kilometres to the vehicle's own use phase.

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

## Coefficients and their provenance

All coefficients ship as CSV files inside the package: shared environment
tables (generation mixes, electricity and hydrogen pathways, fuel
factors, material and battery intensities, delivery legs, servicing
vehicle types, infrastructure types) and one table of per-mode
specifications. They were extracted once from the source spreadsheet by
a script, and they are the library's source of truth: the spreadsheet is
not distributed and is not read at runtime.

The library is held to the source by a golden-master test suite. For all
128 mode columns of the source that a per-mode model can express (the 56
modes plus their sensitivity variants), every energy and emission value
in every view is compared with the value the spreadsheet itself computes,
and must agree within a relative tolerance of 1e-9. Two of the source's
columns are excluded because they are derived across columns rather than
from their own stages. The library deliberately changes nothing in the
arithmetic, so a handful of peculiarities of the source are reproduced as
published; they are listed, with their effect, in the
[workbook audit](workbook_audit).

## What the library adds

On top of the reimplementation, the library adds a typed parameter layer
with validation, session-level electricity mixes including custom ones,
the propagation of the session mix to servicing vehicles, and scenario
files with provenance and three cases. None of these change a default
result: a session created without arguments reproduces the source's
central cases exactly.
