# Handoff to Andy McClary, September 24, 2026

**From:** Mason Bindl (protocol and RFP from here on). **To:** Andy McClary, who leads the sample design code in `plot-network-design/` with Claude Code as his assistant. **Freeze:** October 16, 2026. **RFP posts:** November 2, 2026.

## What the network is for

TRPA adopted two forest structure standards that are stated as a share of the 115,396 acre conifer frame: VP9, seral stage and canopy cover, 75 percent of each forest type within its desired ranges; VP10, stand density, 50 percent within the trees per acre and basal area maxima. Today's attainment figures come from a model trained on about 30 California plots and none in Nevada. The plot network measures the forest the way the standards are written, at enough places to make the 2028 evaluation defensible and to train the next imputation. What this folder produces is the plot location layer, the allocation table, the backup list, and the installation order that the field only RFP references. Everything the crew does with a plot once they reach it is protocol, which stays with Mason.

## Settled. Do not reopen these.

- **Frame and types.** The report's frame: 115,396 acres of conifer CWHR types outside urban land use, designated wilderness, and non conifer types. Three reporting types per report Table 1: Sierran mixed conifer (with lodgepole and white fir, 70,909 ac), red fir (23,037), Jeffrey pine (with eastside pine and juniper, 21,450).
- **Sampling unit.** A 3 by 3 block of 30 m pixels (90 m, 0.81 ha), plot on the centre pixel, 120 m minimum separation between any two sites, legacy included (spsurvey `mindis`). A design coordinate is never moved; access problems go to the backup list. Plot geometry (nested quarter acre primary plot, 56.4 m macroplot) is protocol v1.0 and not a design question.
- **Split sample.** Half A: equal probability, spatially balanced, forest type fixed at its area share, balanced on TPI class, basin side, and elevation band through `caty_n`. Half B: unequal probability toward structural cells and rare types. 300 is the design target; 60, 100, and 300 are prefixes of one GRTS order.
- **Selection tool.** The frozen selection is `spsurvey::grts()` through `scripts/grts_split_draw.R`, for parity with TEON's backbone. The Python GRTS in `src/strata.py` is for iteration and as the fallback when R is absent.
- **Legacy sites.** Lake Tahoe West LiDAR validation plots and Hugh Safford's burn plots only. TEON MSIM and LTUB sites are not legacy sites and never enter the sample (no monuments, tablet fixed centres; decided September 23, 2026). TEON stays only as the shared frame: Pat Manley's extended owl grid (400 ha) with the 133 ha one third cell nested inside it, already built by `06_tessellation`.
- **Strata inputs.** Decision date October 1, 2026. If the lidar-2022 derived metrics (canopy cover, p95 height, stem density proxy) exist by then, use them; otherwise use the threshold rasters already on F: (RRK seral stage by QMD, CFO canopy cover 2020, TPA, basal area, CWHR type), which are the same 30 m grid the thresholds were assessed on. The template runs on the F: rasters today and swaps to LiDAR by `strata.source` alone. This supersedes the line in `CLAUDE.md` that says RRK rasters are never strata.
- **Data access.** SDE and the threshold project gdb through arcpy, the way the threshold notebooks read them. Not REST. `Vector.sde` is read only: never write, create, or delete through an `.sde` connection.
- **Dates.** Freeze October 16. Nothing after the freeze changes without restarting review. RFP posts November 2. Award before Christmas.

## Yours to decide

1. **The Wilderness question.** The report says the frame excludes designated wilderness. The threshold notebook's non urban clause keeps the Wilderness class of `RegionalLandUse`, and the crosswalk read from `veg_type_nonurban` totals 115,600 acres with it kept. Section 2 of the template prints both readings against 115,396; set `frame.exclude_wilderness` to the one that matches and record why.
2. **The October 1 strata source call**, with Mason: `strata.source: rrk` or `lidar`.
3. **Strata breaks and calibration** (lidar mode only), with Becky Estes: `strata.height_breaks_m` and `strata.density_breaks`, calibrated in `02_strata` against plots with both QMD and LiDAR height. In rrk mode the breaks are the threshold decision points and there is nothing to calibrate.
4. **Cell collapse**: `strata.min_cell_acres`, and whether the collapse log in `outputs/cell_collapse_log.csv` reads sensibly, with Becky.
5. **Half B weights**: `allocation.type_shares`, `seral_shares`, `density_shares`, `tail_boost`, `tail_cells`, `floor_per_cell`, with Becky. Section 4 tells you when the floor cannot be met at the minimum level.
6. **Balance covariates for Half A**: `split_sample.balance.tpi_radius_px`, `lake_axis_anchor_xy`, `elev_bands_m`. Fewer categories are better than a `caty_n` that cannot be honoured.
7. **Backup list rules**: how many backups per stratum go into the RFP appendix, in what order, and the replacement rule text (with Mason).
8. **The SDE class names** marked `# CONFIRM` in `config.yaml`: roads, trails, streams, structures, parcels, ownership, state line, treatments, fire perimeters, and the field names for owner, state, and management zone. Section 1's discovery cell lists the candidates.

## Run order

1. `notebooks/00_sample_design_template.ipynb`, generated by `scripts/build_sample_design_template.py`. The one place to start; sections 0 to 7 run the whole design. First run it with `run.synthetic: true` on any Python to see the chain; then on the arcgispro-py3 interpreter with F: mounted and `run.synthetic: false`.
2. `01_frame`, `02_strata`, `03_allocate_draw`, `04_evaluate` (`scripts/build_notebooks.py`) are the deeper chain, one step per notebook, with the height to QMD calibration in `02_strata`. Same config, same modules.
3. `06_tessellation` (`scripts/build_tessellation_notebook.py`) builds the two hex grids; its `outputs/tessellation_lattice_parameters.csv` is what section 7 of the template tags plots with. Run it once before the freeze export.
4. `scripts/grts_split_draw.R` is called by the template through `run.rscript`; it can also be run by hand from the repo root with the seed, oversample factor, and minimum distance as arguments.

## Working with Claude Code on this repo

- Read `plot-network-design/CLAUDE.md` first and point Claude at it; then `PLAN.md` section 0 and `docs/METHODS.md`.
- Edit builders, not notebooks. Every `.ipynb` is generated from a script under `scripts/`; regenerate and re-execute rather than editing cells.
- Config, not code. Every path, break, floor, share, and seed lives in `config.yaml`. If a number appears in code, move it to config.
- Modules, not notebooks, hold the methods: `src/strata.py` (classes, collapse, allocation, Python GRTS, installation order), `src/covariates.py`, `src/sample_size.py`, `src/tessellation.py`, `src/qa.py`, `src/layers.py` (file, REST, SDE, gdb reads), `src/design_template.py` (the template's helpers).
- Before a commit: `python -m pytest tests -q`, then strip notebook outputs (`python -m jupyter nbconvert --clear-output --inplace notebooks/*.ipynb`). `data/`, `outputs/`, and `logs/` are gitignored.
- Writing rules for everything in the repo: no em-dashes, Oxford commas, tight direct prose, and say selection or selected sites, not draw, for the sampling step. Existing names such as `draw.seed` and `grts_split_draw.R` stay as they are.
- `import arcpy` takes over a minute in arcgispro-py3. Batch questions into one script and run it in the background.

## Who to ask what

| Question | Ask |
|---|---|
| Protocol, the RFP, the LiDAR pipeline and its products, this handoff | Mason Bindl |
| Strata breaks, cell collapse, Half B weights, plot count, which LTW plots qualify | Becky Estes (R5 Ecology) |
| LiDAR metrics, which density proxy the model trains on, the DBH floor for TPA | Shengli Huang (USFS RSL) |
| The shared frame only (owl grid, plot tagging), nothing on plot design | Pat Manley, Shale Hunter (PSW) |

## What changed in this handoff

`config.yaml` (new `sde:` block, paired `rrk:` and `lidar:` forms under `sources:`, `strata.source`, `run.rscript`, `frame.exclude_wilderness`, `frame.population_tolerance_pct`, `split_sample.balance.elev_bands_m`); `src/layers.py` (SDE and gdb reads through arcpy, `resolve_source`); `src/design_template.py` (new); `scripts/build_sample_design_template.py` and `notebooks/00_sample_design_template.ipynb` (new); `src/strata.py` (one fix: the Python GRTS now selects along the hierarchical line and applies the reverse hierarchical order to the selected sites, which is what makes its prefixes spatially balanced); `README.md`; `docs/CHANGELOG.md`.
