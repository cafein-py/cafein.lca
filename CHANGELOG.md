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
- Packaged scenarios `india` (Delhi/Mumbai operating conditions, sourced
  per value) and `finland_2020` (electricity mix), listed by
  `list_scenarios()`; tutorial page.
- Results per pkm/vkm/vehicle decomposed into the five life-cycle
  components, as pandas objects; `TransportLCA.summary()` for all modes.

TESTS

- Golden-master suite: all 128 reproducible workbook columns match the
  published workbook within 1e-9 relative tolerance (56 canonical modes,
  48 sensitivity variants expressed as parameter overrides, 24 as column
  fixtures).
- Acceptance test reproducing the repository's Finland-2020 GHG/pkm table.
- Formula-deviation audit of the workbook documented in
  docs/workbook-audit.md.
