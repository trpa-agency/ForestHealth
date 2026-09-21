# Methods: plot-network-design

> Steps 0a, 0, and 0b below (LAS to CHM, LiDAR metrics, TAOs) moved to `trpa-agency/general-purpose/lidar-2022` on 2026-09-09. They are described here for the record; this folder reads their published products from `\\vcenter2\GIS_DATA\LiDAR\2022\Derived`.

**Owner:** mbindl@trpa.gov
**Last reviewed:** 2026-09-05

## Purpose

Produce the plot location layer, allocation table, backup list, and installation order for TRPA's forest health plot network, so the field-only RFP can reference a furnished design. The plots train and validate the Basin-wide imputed structure product and put precision on VP9 and VP10 for the 2028 evaluation. See `PLAN.md` for the design rationale; this file records what the code does.

## Data sources

| Source | Type | Refresh | Notes |
|---|---|---|---|
| CWHR vegetation (threshold assessment layer) | Feature layer (file or TRPA REST) | Static | Forest type via threshold report Table 1 mapping |
| 2022 LiDAR CHM and derived 30 m rasters (cover, p95 height, stem density) | Raster (file or ImageServer) | 2022 epoch; 2026 possible | Strata proxies |
| Urban boundary, wilderness | Feature layers | Static | Frame exclusions |
| Roads, trails, streams, structures, parcels | Feature layers | Periodic | Edge buffers, access class |
| DEM | Raster | Static | Slope cutoff, covariate checks |
| Ownership, state line | Feature layers | Periodic | Nevada floor, owner counts |
| TFFT and LTW treatment units 2027 to 2031 | Feature layer | Annual | Disturbance sub-allocation |
| Fire perimeters and severity 2007 to present | Feature layer | Annual | Disturbance sub-allocation |
| RRK Sierra rasters (seral, cover, TPA, BA) | Raster | RRK release | Evaluation only, never strata |
| F3 representativeness raster and covariate stack | Raster | From Shengli | Optional weighting, evaluation |
| LTW validation plots, Safford burn plots, TEON 100 GRTS sites | Point layers | From partners | Calibration and legacy sites |

Sources are set in `config.yaml` under `sources:` and may be local files under `data/raw/` or TRPA ArcGIS REST URLs; `src/layers.py` reads either.

## Processing steps

0a. **LAS to CHM and point metrics** (`00a_las_to_chm.ipynb`, work in `src/lidar.py`): built for the ~2 TB LAZ archive on the network drive. Drive inventory by folder and extension with no file opens; header-only tile index; AOI filter by header bounds then polygon; classification sample on random tiles; CRS check. Then per tile, in a multiprocessing pool (`lidar.workers`): copy to `lidar.local_scratch` (one network read), decompress once in memory when under `in_memory_max_points` (else chunked two-pass), DTM from class 2 (mean per cell, nearest-fill, 3x3 smooth; written as a 1 m bare-earth tile), height above ground, 1 m CHM tile (max first-return HAG, pits filled), optional height-normalized LAZ copy, and a partial `.npz` with 30 m counts plus a 0.5 m height histogram. Finished tiles are skipped on rerun. Merge sums the partials exactly (histograms give p95) and writes cover 2 m and 5 m, p95, mid-canopy fraction, return density, ground density.
0. **LiDAR metrics** (`00_lidar.ipynb`): from the 1 m 2022 CHM (file, tile folder via VRT, or cached ImageServer export), in grid-aligned blocks: canopy cover above 2 m and 5 m (vertical projection), p95 height, rumple, and individual-tree-detection count per acre (Gaussian-smoothed CHM, local maxima with a height-dependent window). Optional mid-canopy return fraction (2 to 8 m) from LAZ tiles with laspy. Writes 30 m GeoTIFFs snapped to `lidar.grid_origin` under the `sources:` names notebooks 01 and 02 read; writes `outputs/lidar_checks.png`.
0b. **TAOs** (`00b_taos.ipynb`, work in `src/taos.py`): per CHM tile, read with a 25 px pad from neighbours through a VRT, Gaussian smooth, tops by the same height-dependent local-maximum rule as 00_lidar, marker-controlled watershed crowns on the inverted smoothed CHM masked at 3 m, crown pixels trimmed below half the top height, crowns under 2 m2 dropped; a crown is kept by the tile owning its top. Writes per-tile tree points (GeoParquet: tree_id, x, y, height_m, crown_area_m2, crown_mean_h_m, crown_diam_m, tile) and crown polygons (GeoPackage), a merged tree table, and a 30 m detected-trees-per-acre raster on the shared grid. Parallel and resumable like 00a. Second pass from the normalized point cloud: `scripts/segment_trees_lidr.R` (lidR, lmf + dalponte2016) for validation areas and plot footprints.
1. **Frame** (`01_frame.ipynb`): map CWHR to forest type; remove urban and wilderness; lay the 30 m pixel grid; sample LiDAR metrics, DEM, road distance; flag state, owner, fire, treatment; remove edge buffers and slopes above the cutoff; assign access class; write `frame_accounting.csv`.
2. **Strata** (`02_strata.ipynb`): calibrate p95 height breaks to QMD 5 and 25 in per type when plots with both exist (else config placeholders); classify seral, density, cover; build `cell_id`; collapse cells under `min_cell_acres` within type, updating class labels to the target cell; write `cells.csv` and `cells_by_cover.csv`.
3. **Allocate and draw** (`03_allocate_draw.ipynb`): Candidate A (proportional to area, floor 1) and Candidate B (floor per cell, type shares, seral by density shares within type, tail boost) at `min`, `option`, `full`; Nevada floor check; inclusion weights for disturbance targeting and optional representativeness; legacy sites attached to pixels; GRTS draw with oversample; installation order (tail cells first, round-robin across cells, GRTS rank within cell); nested level labels; blind remeasurement flag; internal and published GeoPackages; export of `frame_points.gpkg`, `allocation_full.csv`, `legacy_sites.gpkg` for `scripts/grts_draw.R`.
4. **Evaluate** (`04_evaluate.ipynb`): class coverage by level; VP9 and VP10 cross-tabs against RRK classes; covariate balance (KS, standardized mean difference); representativeness quartiles; practicality by access class, owner, state, disturbance flags, crew-days; QA report.

## Key assumptions

- Population equals the threshold report's 115,396 acres; lodgepole and white fir sit inside SMC, eastside pine and juniper inside Jeffrey pine.
- Seral and density strata are LiDAR proxies for the QMD and TPA definitions; the plots verify the proxies, and RRK rasters are never used as strata.
- Strata are allocation-time bins; inference is model-based and refit per LiDAR epoch, with GRTS weights carried for any design-based estimate.
- Disturbance is a flagged sub-allocation via inclusion weights, not a stratum.
- The Python GRTS is for iteration; the frozen draw is `spsurvey::grts()` for parity with TEON's backbone.
- The DBH floor for TPA (`threshold.tpa_dbh_floor_in`) is unset until Shengli confirms the RRK/F3 definition; the protocol and this config must agree before the first plot.

## Known caveats

- Height and density breaks in `config.yaml` are placeholders until calibrated.
- The synthetic Basin (`run.synthetic: true`) has the real type acreages but invented metrics; its cell table means nothing beyond exercising the chain.
- Legacy sites pull toward their original frames (TEON: 2003 MSIM design, steep ground excluded, pre-Angora and pre-Caldor); the covariate balance check is how that is watched.
- Tree versus rock versus building is handled in layers, none of them sufficient alone. Frame: CWHR conifer types only, urban boundary and wilderness out, buffers around structures, roads, trails, streams, slopes over 70 percent out. Point classes: noise (7, 18) and building, water, bridge (6, 9, 17) dropped from canopy metrics where the vendor classified them; vegetation classes 3 to 5 are not relied on because deliverables often leave them unpopulated. Structure: the solid fraction raster (share of above-2 m first returns from single-return pulses) flags roofs and rock that survived the frame layers; `frame.max_solid_fraction` (0.85) drops those cells in `01_frame`, with the acres logged. Residual risk: small boulders under canopy inflate nothing (they are below 2 m or shadowed) and isolated dead snags read as single-return; both are what the plots measure.
- Point-based cover (first returns above 2 m over all first returns) is the standard LiDAR canopy cover and is what `01_frame` reads; CHM-based cover from `00_lidar` is kept under `_chm_` names for comparison and stands in only when no point cloud was processed.
- p95 in 00a comes from a per-cell 0.5 m height histogram (0 to 80 m), so it is exact to 0.5 m and merges across tile overlaps; the Basin-wide histogram needs about nrow x ncol x 160 x 4 bytes of RAM at merge time (the notebook logs the figure).
- Throughput is the network read. The log projects total runtime after 5, 20, and 50 tiles; levers are workers, an SSD scratch, and overnight runs. Partials make the run interruptible.
- Noise classes 7 and 18 are dropped; returns above `lidar.max_hag_m` (80 m) are dropped.
- TAO count is detected-tree density, not TPA: suppressed stems under closed canopy are not detected; CHM watershed merges crowns in dense fir and can split large pines. Compare with the lidR pass at plots before choosing which layer LITIDA trains on. Without GDAL (VRT) tiles are segmented without neighbour padding and edge crowns may be clipped; arcgispro-py3 has GDAL so this only affects other environments.
- ITD under-detects suppressed stems beneath closed canopy; treat it as a proxy that separates sparse from dense stands, not as TPA. The mid-canopy return fraction is the better proxy for ladder stems where the point cloud is available.
- `lidar.grid_origin` must match Shengli's covariate grid before the real run or the strata rasters will be offset from his stack by up to one cell.
- `read_layer` pages through `maxRecordCount`; very large services (parcels) are slow and should be pre-clipped to the Basin or cached locally.

## Downstream consumers

- Forest health plot network RFP, Appendix A (allocation table, access class definitions, backup rule).
- Design and Protocol Package (`docs/DESIGN_SUMMARY.md`, to be written at freeze).
- Shengli Huang's imputation and LOOCV test of the candidate designs.
- Tahoe Open Data and LTInfo (published plot layer, remeasurement flag stripped).

## Changelog

See `CHANGELOG.md`.
