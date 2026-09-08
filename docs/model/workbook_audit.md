# Formula audit of the ITF "Good to go?" workbook

Findings from the column-by-column formula audit performed while extracting
the pristine ITF workbook download for this library. Method: every mode
column's formulas were
normalized to a column-relative form and diffed against the canonical pattern
of its row, for all ~130 columns of the six calculation sheets.

Parity policy (v0.1): the engine reproduces the workbook **as published**,
quirks included, unless a quirk is a cross-column reference error that cannot
be expressed in a per-mode model (item 4). Golden-master tests assert against
the workbook's own cached values.

## Reproduced quirks

1. **`2_Transport` row 106 — delivery leg 9 GHG always zero.** The GHG rows
   98–107 multiply each leg's energy by its emission factor, but row 106
   (medium truck, leg b) computes `=CR94*CR32`, two cells that are empty in
   every mode column, instead of `=CR80*$D$93`. The GHG of delivery leg 9 is
   therefore always 0 even when its energy is nonzero. The engine reproduces
   this (energy of leg 9 counted, GHG dropped).

2. **`5_Infrastructure` rows 50/51 and 73/74 — division by the
   materials-imputable share.** Network burden per km is *divided* by the
   "% of energy imputable to materials" (row 46/47). This extrapolates the
   materials-only burden to the full network burden and appears to be the
   intended semantics of the row label; noted here because a casual reading
   suggests multiplication. Reproduced as published.

3. **`1_Manufacturing` harmless vestiges.** Row 115 (materials GHG) ends with
   `+CR139` where row 139 is empty (adds 0); row 124 sums `R120:R123` where
   row 120 is empty. No numeric effect; the engine ignores both.

## Deviations from the published workbook

4. **`0_Total` columns E, S, T, U — infrastructure pulled from the wrong
   column.** The infrastructure rows (88 and 110) of these four e-scooter
   sensitivity columns reference the wrong `5_Infrastructure` columns
   (E→G, S→P, T→S, U→S) although the two sheets' column layouts are aligned
   (verified by the row-2 mode names). `5_Infrastructure` itself computes the
   correct per-column values; only the `0_Total` cross-references are
   misaligned. The engine computes each mode's own infrastructure burden, so
   for these four *sensitivity variants* the engine matches
   `5_Infrastructure` row 56/79 rather than the misaligned `0_Total` values
   (relative difference ≈ 9e-4 on the infrastructure component only).
   Canonical modes are unaffected.

## Variant-fixture subtleties (handled at M3, not engine issues)

5. **Ridesourcing BEV occupancy variants BL, BM, BN.** Their
   `4_Operational_Services` rows reference the *ICE* central-case column
   (offset `C[-3]` → column BI) for daily mileage and use-phase energy rather
   than their own BEV column BT. Golden fixtures for these columns must
   record the referenced column.

6. **Column AF (Hollingsworth et al. 2019 simulation).** A study-replication
   display column: its `0_Total` result rows are derived by cross-column
   scaling (e.g. `AF91 = AF113/W113*W91`) rather than from its own stage
   sheets, which a per-mode model cannot express. AF is excluded from the
   golden matrix entirely; its *stage sheets* are reproduced by the engine
   (they equal column D's, verified by the per-stage unit tests).

7. **Empty column AR** (header "AVAILABLE") — a placeholder; skipped.

8. **Figure-sheet deadheading split.** The report figures (and the derived
   `gCO2-per-pkm-by-transport-mode.csv`) reallocate the deadheading share of
   the use-phase burden (Tech_Spec_TNC!P14 ≈ 38.6%) from "Fuel" into
   "Operational services" for taxi and ridesourcing modes. This is a
   presentation-layer split on top of `0_Total`; the library reports the
   `0_Total` decomposition, and the Finland acceptance test applies the same
   split when comparing against the CSV.

## External-workbook links

Material compositions, fluids, battery pack characteristics and several
infrastructure intensities reference two external GREET2-derived workbooks
(`[5]`/`[6]`, not distributed with the ITF file). Only their cached values
exist in the workbook; the extractor captures them as per-mode constants,
which is also why they are packaged data rather than computed quantities.
