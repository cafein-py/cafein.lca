# Changelog

## 0.1.0 (unreleased)

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
  0.24.0, for use alongside the cafein routing package; the core install
  stays dependency-light.

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
