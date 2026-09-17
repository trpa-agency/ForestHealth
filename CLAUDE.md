# CLAUDE.md — ForestHealth

Project context for the Forest Health Threshold Standards Update. Global conventions live in
`Documents\GitHub\CLAUDE.md`; this file covers only what is specific to this repo.

Last verified: 2026-09-15 (reviewed and partially remediated same day)

---

## What this repo is

Analysis and data visualizations backing TRPA's update to the Vegetation Preservation
threshold category. The repo produces the charts, maps, and tables; the public-facing
narrative lives in an ArcGIS StoryMap collection, and the technical write-up lives in a
Box-hosted PDF. **This repo is not the source of truth for the published numbers** — see
"Known divergences" below.

- Analysis notebook: `ForestHealth_ThreholdUpdate_Analysis.ipynb` (note: "Threhold" is
  misspelled in the actual filename)
- Results notebook: `ForestHealth_ThresholdUpdate_Results.ipynb`
- Shared helpers: `utils.py` (arcpy raster workflows, Plotly `stackedbar`, LT Info and
  `maps.trpa.org` fetchers)
- Rendered outputs: `DataVisualizations/*.html`, published via GitHub Pages
- Results page: `index.md` → https://trpa-agency.github.io/ForestHealth

---

## Published outputs (the authoritative surfaces)

### 1. StoryMap collection

**Forest Health Threshold Standards Update**
https://storymaps.arcgis.com/collections/d89adce0aa9047efb018e49a6f8eff87
Collection item ID `d89adce0aa9047efb018e49a6f8eff87`, theme "summit", owner TRPA.

Individual stories (open at `https://storymaps.arcgis.com/stories/<item id>`):

| # | Page | Item ID |
|---|---|---|
| — | Forest Health Threshold Standards Update (executive summary) | `b8cfcbff1bac4d90bec45f9043508391` |
| 1 | Seral Stage & Canopy Cover | `52d2c949764548dba1fa8a119152644b` |
| 2 | Stand Density | `eb85ba5b7c624764be4f7a42331ea04c` |
| 3 | Wildland Urban Interface Fire Dynamics | `c71cbbac37bc41399cab16b4767b9034` |
| 4 | Landscape Fire Dynamics | `24a244191f6842c5ab44bc09e228cf6b` |
| 5 | Subalpine Conifer | `a46630fd0fb048bd84f4fa84fd6bab9d` |
| — | EIP Forest Health Program | `1c1926f5b66944d3b24d13ad18cd43d1` |

Two collection entries are embeds rather than stories:
- **Feedback** — Survey123 form `8538fbbf820641709491b5ee52c9b68e`
- **Full Report** — the Box PDF below

### 2. Full report (Box)

`ForesthHealthThresholdUpdateReport.pdf` — 29 pages, ~2.97 MB, file ID `2124239284709`
https://trpa.app.box.com/s/9wksrvupifkzhrvtc6tlbltonnjijyfc
(The filename typo "Foresth" is on Box, not local.)

This PDF is the most complete and most current source. When the StoryMap, `index.md`, and
the PDF disagree, **the PDF wins.**

### 3. Live dependency — do not break

The Seral Stage & Canopy Cover story embeds a chart served straight out of this repo:

```
https://trpa-agency.github.io/ForestHealth/DataVisualizations/CompositionAge_Chart.html
```

Regenerating or renaming `DataVisualizations/CompositionAge_Chart.html` changes what the
public StoryMap displays, with no review step in between. Verify the chart renders after
any commit that touches it. No other story embeds a github.io URL.

---

## The five proposed standards (canonical, per the Box report)

Assessment vintage: 2023 data covering disturbance through 2022. Primary source is the
Sierra Nevada Regional Resource Kit (California Wildfire & Forest Resilience Task Force,
2024), F3 framework; fire hazard from Pyrologix Wildfire Exposure Simulation Tool.
Forest types come from the California Wildlife Habitat Relationships (WHR) system.

Four of the five standards are currently out of attainment.

| Standard | Target | Current | Status |
|---|---|---|---|
| WUI Defense Zone Fire Dynamics | Surface fire predicted on ≥90% of the zone (40,428 of 44,920 acres) under 90th-percentile fire weather | 62% (28,045 acres); high hazard on 26% (11,848 acres) | Considerably Worse than Target |
| Landscape Fire Dynamics | High-severity patches ≥200 acres on <5% of assessed area (7,892 of 157,843 acres) | 8.9% (14,176 acres); exceeds goal by 6,284 acres, a 44 percent reduction needed | Considerably Worse than Target |
| Stand Density | ≥50% of forested area within TPA and basal area ranges (57,698 of 115,396 acres) | 28% (32,311 acres); 25,387 acres short | Considerably Worse than Target |
| Seral Stage & Canopy Cover | ≥75% of forested area within desired ranges (86,547 of 115,396 acres) | 61% (70,836 acres); 15,711 acres short | Somewhat Worse than Target |
| Subalpine Conifer | Non-degradation of ecological integrity | ~13,350 acres, protections in place | Implemented (in attainment) |

Assessed extents, which differ by standard and are easy to conflate:
- Forest structure standards (stand density, seral stage): **115,396 acres**, conifer WHR
  types only, excluding designated wilderness, urban land use (mixed-use, residential,
  tourist), and non-conifer types. About 56 percent of the Basin's terrestrial area.
- WUI Defense Zone: **44,920 acres**, the wildland portion outside urban land use. The
  zone extends roughly 0.25 miles from community edges.
- Landscape Fire Dynamics: **157,843 acres**, all WHR types and management zones,
  excluding urban areas, designated wilderness, and water.

WHR to TRPA vegetation type crosswalk (report Table 1):

| TRPA type | WHR types | Acres |
|---|---|---|
| Sierran Mixed Conifer | Sierran Mixed Conifer, Lodgepole Pine, White Fir | 70,909 |
| Red Fir | Red Fir | 23,037 |
| Jeffrey Pine | Jeffrey Pine, Eastside Pine, Juniper | 21,450 |
| **Total** | | **115,396** |

### Stand density desired conditions (TPA / basal area ft²/acre)

| Forest type | Early TPA | Early BA | Mid TPA | Mid BA | Late TPA | Late BA |
|---|---|---|---|---|---|---|
| Jeffrey pine | 200 | 30 | 70 | 80 | 55 | 100 |
| Sierra mixed conifer | 300 | 40 | 90 | 130 | 75 | 180 |
| Red fir | 300 | 50 | 100 | 175 | 80 | 250 |

### Seral stage and canopy cover desired ranges

| Forest type | Early | Mid open | Mid closed | Late open | Late closed |
|---|---|---|---|---|---|
| Jeffrey pine | 5–15% | 25–30% | 5–10% | 40–50% | 5–10% |
| Sierra mixed conifer | 10–20% | 15–20% | 5–15% | 25–35% | 15–25% |
| Red fir | 10–20% | 15–25% | 15–25% | 30–40% | 20–30% |

Definitions that the repo does not currently document:
- Seral stage is defined by Quadratic Mean Diameter: early 0–5 in., mid 5–25 in.,
  late greater than 25 in.
- Open versus closed canopy cutoff is 40 percent canopy cover for Jeffrey pine and
  50 percent for Sierra mixed conifer and red fir.
- Canopy **cover** (vertical projection of crowns), not canopy closure.

---

## Known divergences — resolve before the next publication

These are real conflicts found by comparing the report, the StoryMap, and this repo.

1. **WUI attainment.** Report says 62 percent. The StoryMap Looking Ahead section says
   "71 percent of the WUI Defense Zone meets the desired flame length standard." One is
   stale.
2. **Landscape Fire Dynamics results.** Report says 8.9 percent, 14,176 acres, patches
   ≥200 acres. The StoryMap says "about 19,900 acres (11% of Tahoe's forests)" and
   describes patches "larger than 40 acres" with flame lengths above 8 feet — a different
   number, a different denominator, and a different metric. The 40-acre figure comes from
   the Lake Tahoe West Landscape Resilience Assessment, which the report explicitly
   distinguishes from the adopted 200-acre standard.
3. **RESOLVED — `index.md` rewritten against the report.** It had used the superseded
   "Composition" and "Functional Fire" framing, omitted Subalpine Conifer entirely, cited
   "~55% across ~126,000 acres," carried blank tables and a `* ?` placeholder, misspelled
   "Performance Meassures," and linked to a nonexistent notebook filename. All five
   standards are now present with the report's figures, the class definitions (QMD breaks
   and canopy cutoffs) are documented, and the broken link in `README.md` is fixed.

   Two embedded tables, `CompositionAge_Table_Updated.html` and
   `Composition_Action_Table.html`, hardcode the superseded 127,322-acre run **and** the
   transposed canopy labels. `index.md` carries a visible caveat until they are
   regenerated. Do not remove that caveat before the rerun.
4. **RESOLVED — three conflicting stand-density outputs.** `_new.csv` is authoritative:
   it is the only table written by current notebook code (analysis cell 11) and its 28.5
   percent agrees with the report's 28 percent. The other two came from code no longer in
   the repo and now live in `archive/superseded_outputs/`. Totals were:

   | File | Assessed acres | Meeting | Percent |
   |---|---|---|---|
   | `stand_density_forest_type_attainment.csv` | 127,322 | 75,665 | 59.4% |
   | `stand_density_forest_type_attainment_new.csv` | 111,424 | 31,804 | **28.5%** |
   | `stand_density_forest_type_attainment_hugh.csv` | 127,322 | 93,900 | 73.8% |

   The direction of the density test is settled: the threshold values are **maximums**.
   Analysis cell 10 flags `>= target` as 1 (overstocked, out of attainment); cell 11 counts
   `Value == 0` as attaining. The pipeline was always coherent — only the markdown prose was
   wrong, and it has been rewritten.
5. **RESOLVED — the acreage gap was a missing Lodgepole Pine class.** `veg_map` had no
   `LPN` key, so 9,261 acres fell to NODATA. Recomputing the report's Table 1 crosswalk
   directly from the `veg_type_nonurban` raster attribute table gives Sierran Mixed Conifer
   71,033 / Red Fir 23,079 / Jeffrey Pine 21,488, totaling 115,600 against the report's
   115,396 — within 0.2 percent. `"LPN": 2` has been added to both notebooks. A rerun is
   required before the outputs reflect it.

   Note the repo labels the class "White Fir" where the report says "Sierran Mixed
   Conifer." Same class, different name; worth aligning.
6. **RESOLVED — misleading `utils.py` classifiers deleted.** `classify_snrrk_tpa` and
   `classify_ecobject_tpa` used single TPA cutoffs that did not implement the adopted
   3×2 forest-type-by-seral-stage matrix, and were called by neither notebook. Removed.

7. **OPEN, highest severity — canopy classes were transposed.** In `classify_seral_stage`
   and `classify_seral_stage_single_raster`, the `combined_class_r` codes for mid and late
   seral contradicted both `seral_stage_map` and the keys of `desired_conditions`, so each
   mid and late class was scored against the wrong target range. The code is fixed; the
   **outputs are not**. `output/seral_stage_with_classification.csv`,
   `CompositionAge_Chart.html` (embedded live in the StoryMap),
   `CompositionAge_Table_Updated.html`, and `Composition_Action_Table.html` all still carry
   the swap. Rerun required.

8. **OPEN — the WUI Defense Zone assessment exists but is not committed.** The raster
   `functionalfire_dominant_severity_tahoe_nonurban_wuidefensezone` in the project gdb
   holds it: 28,095 acres surface fire, 5,036 moderate, 11,869 high hazard, roughly 45,000
   total, closely matching the report's 28,045 / 11,848 / 44,920. No committed notebook
   cell creates this raster. The method needs recovering and adding to the analysis
   notebook.

---

## Repo hygiene notes

Done:

- `CompositionAge_Chart_Ecobject.html` (34 MB), `debug.log`, and
  `__pycache__/utils.cpython-311.pyc` are untracked and listed in `.gitignore`. The files
  remain on disk; they were untracked rather than deleted. History still carries the 34 MB
  blob, so a clone is not smaller — rewriting history is a separate decision.
- `.env` added to `.gitignore`.
- `utils.py`: removed the four Climate Resilience Dashboard functions that wrote to a
  nonexistent `html/` directory, removed `classify_snrrk_tpa` and `classify_ecobject_tpa`,
  and made `FeatureLayer` a lazy import inside the two fetchers that need it (a
  module-level `import arcgis` would cost seconds on every `from utils import *`). The
  `numpy` gap disappeared with the function that used it.

Still open:

- `utils.py` and both notebooks hardcode paths under `F:\GIS\`. Per global conventions
  these belong in `config.yaml`. Nothing here runs without the `F:` drive and a live SDE
  connection.
- Both notebooks are committed with **every cell output stripped** and execution counts
  almost entirely null, so no acreage is auditable from git. Commit them with outputs
  after the next run.
- Analysis cell 21 writes the 9x9 focal product's area field as `acres_area` while the
  3x3 uses `acres`, so `sum_area_by_criteria(area_field="acres")` breaks on the 9x9.
- Results cell 29 reads a feature class (`ID_MGMTzones_FunctionalFire_DominantClass_Tahoe_SNVRRK`)
  that no analysis cell creates, and writes to the `F:` AnalysisProduct directory rather
  than `output/`. Several Results cells (21-23, 26) are hardcoded literals transcribed
  from a report table rather than derived from any CSV.

---

## Process and timeline

- Developed with the Tahoe Fire and Fuels Team, a partnership of 21 agencies and
  organizations.
- Peer review by the Tahoe Science Advisory Council (TSAC), which recommended following
  the modeling with on-the-ground monitoring.
- Input from the Threshold Update Initiative Stakeholder Work Group (TUISWG).
- Goes to the TRPA Advisory Planning Commission and Governing Board in **early 2026**.
- Public feedback via the Survey123 form embedded at the end of the collection.
- Standards for sensitive, uncommon, wetland, and riparian vegetation are unchanged.
- Legacy standards limiting shrub coverage and mandating "immature" tree ratios are being
  removed; late-seral and old-growth intent is folded into Seral Stage & Canopy Cover.

---

## Environment

Windows, `arcgispro-py3` conda env (arcpy, pandas, geopandas) at
`C:\Program Files\ArcGIS\Proin\Python\envsrcgispro-py3`.

The Bash tool occasionally fails at startup with an msys2 `add_item` fatal error. It is
transient — retry once, and fall back to PowerShell if it persists.

`import arcpy` takes well over a minute in this environment. Run arcpy scripts in the
background rather than waiting on them inline, and batch several questions into one script
to amortize the import.
