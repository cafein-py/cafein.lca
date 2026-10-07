# Changelog

## 0.2.0 (unreleased)

CHANGED

- Renamed the middle scenario case from `central` to `middle`. Scenario
  files, `Scenario.load(case=...)` and `Scenario.case` now use
  `best`/`middle`/`worst`.
- `transit_factors()` and `street_factors()` raise `ValueError` when two
  rows would be matched by cafein on the same key (for transit its most
  specific one: `trip_id`, `route_id`, `agency_id` with `route_type`, or
  `route_type`), since cafein keeps only one of them.
- `transit_factors()` exports the two new rail modes by default, so its
  default table has eight rows instead of six.

NEW

- An `identities` value may be a list, giving the mode one row per element,
  e.g. `{"metro_urban_train": {"route_type": ["0", "1", "2"]}}`.

- Scenario provenance gained an optional `year` field, the data year of a
  value's source, resolvable per case and returned by
  `Scenario.provenance()`.
- The workbook audit documents how the metro mode's rail inputs are
  derived and three rail-related quirks: the metro occupancy, the
  light-rail track materials and the light-rail track usage.
- Mode packs add modes from other sources on top of the coefficient set,
  under `cafein/lca/data/modes/`, with a source for every value.
  `Result.mode_source` names where a result's mode data came from, and
  `mode_provenance(slug)` lists the sources of a mode's default values.
- The `rail-2026` pack adds two transit modes: `tram_light_rail` (Siemens
  Avenio tram, from its EPD) and `suburban_regional_rail` (Alstom RER NG
  train, from its EPD), the latter on a new heavy-rail track type built
  from German network data.
- A packaged `germany` scenario: German operating conditions for cars,
  mopeds, buses, trams, U-Bahn and suburban trains, with the 2025
  electricity mix, in three cases.
- `gtfs_identities()` maps the GTFS basic route types to transit modes
  (tram, metro, suburban/regional rail, bus) for `transit_factors()`, with
  overrides for extended route types.

## 0.1.0 (2026-09-09)

NEW

- Initial release: the ITF "Good to go?" (Cazzola & Crist 2020) urban
  transport LCA model as a Python library.
- 56 transport modes with typed, immutable scenario parameters
  (`cafein.lca.mode()` + `.replace()`, or keyword overrides on
  `TransportLCA.calculate()`).
- Session-level electricity generation mix: packaged region presets from the
  workbook plus fully custom mixes; propagates to use phase, hydrogen
  electrolysis and shared-fleet servicing vehicles.
- Scenario bundles: `Scenario.load()` reads a TOML file of per-mode
  parameter overrides plus an electricity mix, with `best`/`central`/`worst`
  cases, and `TransportLCA(scenario=...)` applies it to every mode.
- Scenario values carry provenance (evidence type, geography, source,
  confidence, note), validated on load and exposed by
  `Scenario.provenance()`.
- Packaged scenarios `india_metropolitan` (Delhi/Mumbai operating
  conditions, provenance per value) and `finland_2020` (electricity mix),
  listed by `list_scenarios()`; tutorial page.
- Results per pkm/vkm/vehicle decomposed into the five life-cycle
  components, as pandas objects; `TransportLCA.summary()` for all modes.
- Optional `cafein` extra (`pip install cafein.lca[cafein]`) pinning cafein
  0.25.0, for use alongside the cafein routing package; the core install
  stays dependency-light.
- Export helpers `TransportLCA.transit_factors()` and `.street_factors()`
  return cafein-ready factor tables: the mode's four life-cycle components
  (vehicle, fuel, infrastructure, operations), their `total`, an explicit
  per-passenger-km or per-vehicle-km `basis`, and scenario provenance, for
  use with the `cafein` routing package through `factors=`. `Scenario`
  records its `name` and file `sha256` for that provenance. cafein 0.25.0
  keeps the `total` column without warning and computes from the components.
- Named coefficient sets: the packaged tables are the set `itf-2020` under
  `cafein/lca/data/itf-2020/` with a `manifest.toml`.
  `TransportLCA(coefficients=...)` selects a set (default `itf-2020`, else a
  scenario file's `coefficients` key), `available_coefficient_sets()` lists
  the packaged sets, and `Result.coefficient_set` records which set produced
  a result. 0.1.0 ships one set.

TESTS

- Golden-master suite: all 128 reproducible workbook columns match the
  published workbook within 1e-9 relative tolerance (56 canonical modes,
  48 sensitivity variants expressed as parameter overrides, 24 as column
  fixtures).
- Acceptance test reproducing the repository's Finland-2020 GHG/pkm table.
- Formula-deviation audit of the workbook documented in
  docs/workbook-audit.md.
- Integration job installing `cafein.lca[cafein]` and checking that
  cafein.lca coexists with the cafein routing package under the shared
  namespace; skipped when cafein is not installed.
- Export-helper tests: `tests/test_export.py` covers the schema, the 5->4
  component mapping, the basis rule and provenance; the cafein round-trip in
  `tests/test_integration.py` checks cafein loads the exported tables and
  honours their `basis`.
