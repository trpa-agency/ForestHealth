# Inputs and outputs

Extracted from PLAN.md section 13; keep the two in sync.


All paths are in `config.yaml` (`sources:` for inputs, `lidar:` and `paths:` for outputs). Nothing is hardcoded. Resolution is native unless stated; every 30 m product shares one grid snapped to `lidar.grid_origin`, CRS EPSG:26910.

### Inputs

| Input | Resolution or type | Purpose | Source | Status |
|---|---|---|---|---|
| 2022 LiDAR LAZ tiles | Point cloud, 8 to 30 pts per m2 expected | DTM, CHM, all structure metrics | `\\vcenter2\GIS_DATA\LiDAR\2022\LAZ` | In hand, about 2 TB |
| CWHR vegetation (threshold assessment layer) | Polygon | Frame population and forest type stratum via Table 1 mapping; AOI for the LiDAR pass | TRPA (file or REST) | In hand |
| TRPA urban boundary (mixed-use, residential, tourist) | Polygon | Frame exclusion | TRPA | In hand |
| Designated wilderness | Polygon | Frame exclusion | LTBMU / TRPA | In hand |
| Roads, trails, streams, structures, parcels | Line and polygon | Edge buffers (15 m), road distance for access class | TRPA, LTBMU | In hand |
| DEM (or the 1 m DTM produced here) | 10 m (or 1 m) | Slope cutoff, aspect, heat load, TPI, elevation for covariate checks | TRPA / `00a` | In hand |
| Ownership, state line | Polygon | Nevada floor, landowner counts | TRPA | In hand |
| TFFT and Lake Tahoe West treatment units 2027 to 2031 | Polygon | Treatment sub-allocation (pre-treatment plots) | TFFT, LTBMU (Brian) | Requested |
| Fire perimeters and severity 2007 to present | Polygon or 30 m raster | Post-fire sub-allocation | MTBS / CAL FIRE / LTBMU | In hand |
| Soils (SSURGO), climate zones | Polygon / raster | Covariate balance only, never strata | NRCS, Shengli | In hand / requested |
| Shengli's covariate stack | 30 m | Weighting, balance checks, and the grid origin everything snaps to | USFS RSL | Requested |
| F3 representativeness raster | 30 m | Optional inclusion weighting; evaluation | USFS RSL | Requested |
| RRK Sierra rasters: seral (v4.3), canopy cover, TPA, BA, SDI, VP9 and VP10 attainment | 30 m | Evaluation cross-tabs only, never strata | RRK Sierra | In hand |
| Lake Tahoe West LiDAR validation plots (~60) | Points with tree lists | Height-to-QMD calibration; legacy sites | Becky Estes | Requested |
| Hugh Safford burned-area plots | Points | Legacy sites; post-fire sub-allocation | UC Davis | Requested |
| TEON 100-site GRTS layer, 195-site pool, 2/4/8 km hex grids | Points, polygons | Legacy sites; hex ID attribute; co-location | Shale Hunter (PSW) | Pool in hand; 100-site layer requested |
| FIA plots with true coordinates | Points | Calibration; evaluation | RSL / PNW / RMRS | Access requested |
| Threshold definitions (QMD breaks, cover cutoffs, TPA and BA maxima, CWHR mapping) | Table | Class definitions and frame | Threshold report, in `config.yaml` `threshold:` | In hand; DBH floor pending Shengli |

### Outputs

| Output | Resolution | Purpose | Written by | Lands in |
|---|---|---|---|---|
| Drive inventory (`drive_inventory.csv`) | Table | What the 2 TB actually is, by folder and extension | 00a | outputs, Derived |
| LAS tile index (`las_tile_index.gpkg`, `.csv`) | One record per tile | Extent, count, density, ground share, CRS; AOI selection; QA map | 00a | outputs, Derived |
| Height-normalized LAZ (`<tile>_hag.laz`) | Native point cloud | Reusable base for any future metric, scan calibration, 2026 change | 00a | `LAZ_Basin_HAG` on the drive |
| Bare-earth DTM tiles plus VRT | 1 m | Slope, aspect, TPI, heat load; frame cutoff; navigation | 00a | Derived `dtm_1m_tiles` |
| Canopy height model tiles plus VRT | 1 m | Individual tree detection, rumple, visualization, plot navigation packets | 00a | Derived `chm_1m_tiles` |
| Per-tile partials (`.npz`) | 30 m counts and 0.5 m height histogram | Resume state; exact merge | 00a | server local only |
| Canopy cover (`lidar2022_cover_30m.tif`) | 30 m | Cover class (sparse under 15, open/closed at 40 or 50 percent); primary strata input | 00a | Derived `metrics_30m` |
| Canopy cover above 5 m (`_cover5m_`) | 30 m | Becky's second break; evaluation | 00a | Derived `metrics_30m` |
| p95 height (`lidar2022_p95_30m.tif`) | 30 m | Seral proxy, calibrated to QMD 5 and 25 in | 00a | Derived `metrics_30m` |
| Mid-canopy fraction 2 to 8 m (`_midcanopy_`) | 30 m | Ladder-fuel proxy; candidate density proxy | 00a | Derived `metrics_30m` |
| Return density, ground density | 30 m | Data quality flags for the tile index and the frame | 00a | Derived `metrics_30m` |
| Solid fraction (`_solid_frac_`) | 30 m | Roof and rock screen; cells above 0.85 dropped from the frame | 00a | Derived `metrics_30m` |
| Tree tops per acre (`_itd_per_ac_`) | 30 m from 1 m CHM | Candidate density proxy for the TPA classes | 00_lidar | Derived `metrics_30m` |
| TAO tree table (`taos_trees_2022.parquet`) and crown polygons per tile | Per tree, from 1 m CHM (first pass) or normalized LAZ (lidR second pass) | LITIDA input; detected-tree density; crown cover, clump and gap metrics; 2022 to 2026 tree-level change | 00b_taos, `segment_trees_lidr.R` | Derived `taos` |
| TAO density (`lidar2022_tao_per_ac_30m.tif`) | 30 m | Detected trees per acre on the shared grid; cross-check of the ITD proxy | 00b_taos | Derived `taos` |
| Matched-tree training table (planned) | Per measured tree with TAO ID | LITIDA training and validation; omission rate per plot | after field season | outputs, to Shengli |
| Rumple (`_rumple_`) | 30 m from 1 m CHM | Heterogeneity attribute | 00_lidar | Derived `metrics_30m` |
| CHM-based cover and p95 (`_chm_` names) | 30 m | Comparison to point-based versions; stand-in when 00a did not run | 00_lidar | Derived `metrics_30m` |
| Sanity figures (`las_checks.png`, `lidar_checks.png`) | Figures | Cover versus height, ITD versus cover, mid-canopy versus cover | 00a, 00_lidar | outputs |
| Frame (`frame.parquet`) and `frame_accounting.csv` | One row per 30 m pixel | Sampling frame with LiDAR metrics, slope, road distance, state, owner, disturbance flags, access class; acres removed per exclusion step | 01 | processed, outputs |
| Cell table (`cells.csv`, `cells_by_cover.csv`, `cell_collapse_log.csv`) | One row per stratum cell | Acres per cell; collapse decisions; cover distribution per cell | 02 | outputs |
| Classified frame (`frame_classified.parquet`) | Per pixel | Seral, density, cover class and cell ID per pixel | 02 | processed |
| Allocation table (`allocation_table.csv`) | Per cell and level | Candidates A and B at min, option, full; Nevada floor check; RFP Appendix A | 03 | outputs |
| Plot design layer (`plots_design_<date>.gpkg`, plus `_internal`) | Points, design coordinates on pixel centers | Primary, backup, legacy plots with cell, level, installation order, GRTS weight, access class, flags; internal copy carries the blind remeasurement flag | 03 | outputs; published to Tahoe Open Data at posting |
| spsurvey inputs (`frame_points.gpkg`, `allocation_full.csv`, `legacy_sites.gpkg`) and frozen draw (`grts_draw_spsurvey.gpkg`) | Points | The frozen design drawn with the same tool as TEON's backbone | 03, `grts_draw.R` | processed, outputs |
| Evaluation tables (`eval_class_coverage.csv`, `eval_vp9_crosstab.csv`, `eval_vp10_crosstab.csv`, `eval_covariate_balance.csv`, `eval_practicality.csv`) and `qa_report.csv` | Tables | Coverage by cell and level; threshold-class representation; sample versus frame balance; owner, access, crew-day counts; QA | 04 | outputs |
| Design summary (`docs/DESIGN_SUMMARY.md`) | Document | Objective, inputs, frame, strata and calibration, allocation, draw method and seed, evaluation, what the network cannot represent, backup rule text; attached to the RFP | Mason | docs |
| Run logs and dated config snapshots | Text | Reproducibility; every run records its parameters | all | logs, Derived |

