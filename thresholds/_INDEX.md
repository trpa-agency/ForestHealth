# Threshold Indicator Page Copy — Status

Draft copy for the five new Forest Health threshold indicator pages on
`thresholds.laketahoeinfo.org`. All five pages are currently live but empty.

Each file mirrors the field order of a populated LT Info indicator page (modeled on
[indicator 1](https://thresholds.laketahoeinfo.org/threshold/indicators/1)) so copy can
be pasted field-by-field into the CMS. See `_TEMPLATE.md` for the structure.

The Forest Health Threshold Standards report
([Box](https://trpa.app.box.com/s/9wksrvupifkzhrvtc6tlbltonnjijyfc)) is the authoritative
source for every published number. Where this repo and the report disagree, the report
wins and the repo is treated as needing reconciliation.

| # | Indicator | Reporting category | File | Ready to publish |
|---|---|---|---|---|
| 189 | Stand Density | Forest Structure | [189-stand-density.md](189-stand-density.md) | No — pending rerun |
| 190 | Seral Stage & Canopy Cover | Forest Structure | [190-seral-stage-canopy-cover.md](190-seral-stage-canopy-cover.md) | No — pending rerun |
| 191 | Subalpine Conifer | Sensitive Plants | [191-subalpine-conifer.md](191-subalpine-conifer.md) | No — not covered by this repo |
| 192 | Landscape Fire Dynamics | Fire Dynamics | [192-landscape-fire-dynamics.md](192-landscape-fire-dynamics.md) | No — results not preserved |
| 193 | WUI Defense Zone Fire Dynamics | Fire Dynamics | [193-wui-defense-zone-fire-dynamics.md](193-wui-defense-zone-fire-dynamics.md) | No — results not committed |

## Resolved

1. **189 — direction of the density test.** Settled: the threshold values are
   **maximums**. The code flags `>= target` as 1 (overstocked, out of attainment) and the
   summarization cell counts `Value == 0` as attaining, so the pipeline was always
   internally consistent. Only the narrative in markdown cell 9 was wrong; it has been
   rewritten. The report confirms the direction: "72 percent of the assessed forest
   exceeds the proposed stand density targets."

2. **189 — three competing result sets.** Settled:
   `stand_density_forest_type_attainment_new.csv` is authoritative. It is the only table
   written by current notebook code, and at 28.5 percent it agrees with the 28 percent
   published in the report. `..._hugh.csv` (73.8 percent) and the un-suffixed table (59.4
   percent) were produced by code no longer in the repository and have been moved to
   `archive/superseded_outputs/`. The earlier draft's 74 percent came from reading the
   `_hugh` counts as attainment when they are the overstocked population.

3. **190 — two different basin-wide figures.** Superseded by the canopy class bug below.
   The report's figure, 61 percent of 115,396 acres, is the one to publish.

4. **Assessed acreage gap.** Settled: the repo's `veg_map` omitted Lodgepole Pine.
   Recomputing the report's Table 1 crosswalk directly from `veg_type_nonurban` gives
   Sierran Mixed Conifer 71,033 acres, Red Fir 23,079, and Jeffrey Pine 21,488, totaling
   115,600 against the report's 115,396 — within 0.2 percent. `"LPN": 2` has been added to
   the crosswalk in both notebooks.

## Open blockers, in the order they should be cleared

1. **190 — canopy classes are transposed.** In `classify_seral_stage` and
   `classify_seral_stage_single_raster`, the `combined_class_r` codes for mid and late
   seral disagreed with both `seral_stage_map` and the keys of `desired_conditions`, so
   each mid and late class was compared against the wrong target range. The code is fixed;
   **the outputs are not**. `output/seral_stage_with_classification.csv`,
   `DataVisualizations/CompositionAge_Chart.html`,
   `DataVisualizations/CompositionAge_Table_Updated.html`, and
   `DataVisualizations/Composition_Action_Table.html` all still carry the swap. The chart
   is embedded live in the public StoryMap. Rerun and regenerate before publishing 190.

2. **All indicators — rerun required.** The canopy fix and the Lodgepole addition both
   change results. Nothing derived from `output/` should be published until the analysis
   notebook is rerun against `F:\` and the outputs are recommitted with cell outputs
   intact.

3. **193 — results exist but are not committed.** The raster
   `functionalfire_dominant_severity_tahoe_nonurban_wuidefensezone` in the project
   geodatabase holds the Defense Zone assessment: 28,095 acres surface fire, 5,036
   moderate, and 11,869 high hazard, totaling roughly 45,000 acres. These match the
   report's 28,045 / 11,848 / 44,920 closely. No committed notebook cell creates this
   raster. Recover the method, add it to the analysis notebook, and write a summary CSV to
   `output/`.

4. **192 — results are not preserved.** The notebook cells that compute fire severity
   acreage have empty outputs, and `fire_severity_results.csv` writes to
   `F:\...\ForestHealth_ThresholdUpdate.gdb\fire_severity_results.csv`, a `.csv` inside a
   `.gdb` path, which is malformed. Fix the destination, rerun, and commit the summary.

5. **192 — patch size criterion.** The adopted standard is high-severity patches of **200
   acres or greater** on less than five percent of the assessed area. The notebook's patch
   analysis uses a **40-acre** threshold, which comes from the Lake Tahoe West Landscape
   Resilience Assessment and is explicitly distinguished from the adopted standard in the
   report. Align the analysis with the 200-acre criterion.

6. **191 — content gap.** Subalpine conifer is not analyzed in this repository. The
   standard is assessed through existing regulation rather than a spatial model, so this
   may be correct as-is; confirm no analysis is expected.

## Cross-cutting items

- **Standard codes are unassigned** on all five indicators. The proposed standard language
  in each file is drafted from the report and needs Working Group adoption plus a code
  before publication.
- **Trend is "Insufficient Data" on all five.** These are first evaluations. Fix the
  assessment interval and the reference dataset version now so the next cycle is
  comparable.
- **EIP links are placeholders.** Action Priorities, Indicators, plans, and example
  projects should be pulled from the EIP Project Tracker rather than retyped, so names
  match the tracker exactly.
- **Monitoring Programs are unnamed.** All five assessments are remote sensing analyses
  rather than standing field monitoring programs. Decide how to describe this
  consistently. TSAC has recommended following the modeling with on-the-ground monitoring.

## Discrepancies to raise with the Working Group

- The canopy class fix may change the report's key point that the forest is "dominated by
  mid-seral closed-canopy conditions." Verify after the rerun, before the Board package.
- The StoryMap's WUI page states 71 percent attainment; the report states 62 percent.
- The StoryMap's Landscape Fire Dynamics page states 19,900 acres and 11 percent using a
  40-acre patch and eight-foot flame lengths; the report's adopted standard gives 14,176
  acres and 8.9 percent using 200-acre patches.
