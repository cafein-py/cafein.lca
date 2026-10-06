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

## Variant-fixture subtleties (handled in the golden fixtures, not engine issues)

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

## Rail inputs (reproduced as published)

The workbook's only rail mode, column ED ("Metro/urban train"), is built
from the per-carriage data in `Tech_Spec_Rail`. Energy use and empty mass
are the averages of three carriages (rows 9, 10 and 13: Metro Rome Line C,
Bombardier Azur and Metro Oslo) multiplied by six carriages per train,
giving 17.72 kWh per train-km (`3_Use!ED4`) and 186 t (`0_Total!ED10`). The
material shares average eight vehicles (`Tech_Spec_Rail` columns J–Q),
split their metals into steel and aluminium by Metro Oslo's ratio, and add
maintenance materials from two of them (SPACIUM and Regina X55). The
suburban and intercity vehicles on the sheet enter only these material
shares; no mode column is built from them. The mass in `Tech_Spec_Rail!W27`
also averages the empty cell D116, which `AVERAGE` skips, so its value is
unchanged.

9. **`0_Total` row 16 — metro occupancy is 823/1,000 of the sheet's own
   London load.** Column ED sets the average number of passengers to
   `ROUND(Tech_Specs_Infra!C282 * Tech_Specs_Infra!C287, -1)`: 823 places
   per train times
   an "average metro occupancy" that the sheet labels a share of capacity.
   That share (`C287 = C286 / C274`) divides London Underground
   passenger-km (19.38 billion) by train-km (83.6 million), which gives
   passengers per train-km in thousands (0.2318) rather than a share of
   capacity. The result is 823 × 0.2318 ≈ 190. The next row (C288)
   computes the same London figure directly as 231.8 passengers per
   train-km, and taking the share as passenger-km over place-km (C283)
   would also give 232 passengers, or 230 after the same rounding. The six metro variants DX–EC take
   their occupancy from ED16. The engine keeps 190; with 230, every
   per-passenger-km component of the metro would be about 17 % lower.

10. **`Tech_Specs_Infra` rows 175 and 179 — a heavy-rail line in the
    light-rail track average.** The light-rail track intensities (row 15:
    6,700 t of concrete, entered as 837.5 t of cement, and 260 t of steel
    per km of one-way track) average several estimates. Two of them
    (rows 175 and 179) are `AVERAGEIF` means over the sources labelled
    "Light Rail" in rows 147–156, which include SF Caltrain (row 153). The
    same sheet's Chester (2008) table labels Caltrain heavy rail, all at
    surface level (row 165). No workbook column uses light-rail track, so
    the published results are unaffected. The packaged
    `infrastructure_types.csv` keeps the published intensities (837.5 t of
    cement and 260 t of steel per km), so any mode assigned light-rail
    track inherits this average.

11. **`Tech_Specs_Infra` row 230 — light-rail track usage is an
    assumption.** The traffic that light-rail track is spread over, 72,077
    vehicle-km per km of track per year, is the bus-lane figure divided by
    four and multiplied by 1.25 (`B230 = B229 / 4 * 1.25`); the sheet gives
    no source for it. Metro track usage (row 231) comes from London
    Underground train-km and track length (rows 271–281). The packaged
    `infrastructure_types.csv` keeps the published 72,077 vehicle-km, so
    any mode assigned light-rail track has its track footprint spread over
    this assumed traffic.

## External-workbook links

Material compositions, fluids, battery pack characteristics and several
infrastructure intensities reference two external GREET2-derived workbooks
(`[5]`/`[6]`, not distributed with the ITF file). Only their cached values
exist in the workbook; the extractor captures them as per-mode constants,
which is also why they are packaged data rather than computed quantities.
