# Changelog

## 2026-09-22 (tessellation vegetation attributes)
- `06_tessellation` section 6 attributes both grids from the threshold analysis rasters on F: (`veg_type_nonurban`, `seral_stage_nonurban`, `canopy_cover_nonurban`): acres and shares of the three TRPA types, dominant type, dominant CWHR WHRTYPE with lifeform, and the five VP9 seral and canopy class shares, computed from the component rasters with the corrected class logic rather than the stale classification raster. Writes the WHRTYPE crosswalk (read from the raster attribute table) and a cell by WHRTYPE table. Frame totals: 115,692 ac over the cells against 115,396 in the report. `whr_to_type` and `seral_canopy_classes` added to config. `fetch` now falls back to the copy in the work gdb when a REST service is unreachable.
- Delivery to TEON assembled in `outputs/delivery_20260922/` with `email_tables.md`.

## 2026-09-21 (tessellation rewrite)
- `06_tessellation` rebuilt around arcpy `GenerateTessellation`. The CSO owl grid is one exact lattice in NAD83 UTM 10N (400 ha flat top hexagons, residual under 5 mm over all 8,087 Sierra cells), so anchoring the tool's extent on a lattice point reproduces every delivered cell and extends the grid over Nevada. The sample design grid is the ratio 3 transverse hexagon on the same anchor; every owl centre is a fine centre. Scope cut to those two grids plus occupancy: the bin size sweep, EcObject overlay, rare type analysis, and extra grid family are gone (the sweep is uninformative on 125 sites and Pro 3.5.2 lacks the Esri tool anyway).
- `tessellation:` config block rewritten: CRS is 26910, not 3310; `frame_raster` points at the threshold analysis raster on F: and is optional. `docs/tessellation_config_block.yaml` removed as a duplicate.
- `src/tessellation.py`: `fit_lattice_xy` and `residuals_xy` fit a known construction from a centroid array with no spatial library, so arcpy cursors can feed them. Bug fix: the geopandas fits used `representative_point()`, which is not the centroid, and reported a 3 m residual on an exact lattice.
- Outputs: `outputs/tessellation.gdb` with both grids, shapefile and GeoPackage copies, `tessellation_summary.json` (read by `scripts/build_html_data.py`), `tessellation_lattice_parameters.csv`, occupancy and increment CSVs, and a handoff note. Earlier `TahoeBasin_Hex399ha_*`, `owl_grid_lattice_parameters.csv`, `increment3_*.csv`, and `bin_size_evaluation_teon_sites.csv` came from code no longer in the repo and are superseded.

## 2026-09-09 (repo split)
- LiDAR base processing (00a, 00_lidar, 00b, src/lidar.py, src/taos.py, run_lidar.py, segment_trees_lidr.R, SERVER_RUN.md) moved to trpa-agency/general-purpose/lidar-2022. This folder keeps 01 to 04, strata, qa, and the spsurvey draw, and reads LiDAR products from Derived via config.yaml sources.

## 2026-09-05 (TAOs)
- Added 00b_taos.ipynb and src/taos.py: CHM watershed tree segmentation per tile (tops, crowns, tree table, density raster, publish), parallel and resumable; scripts/segment_trees_lidr.R for the point-cloud second pass. Verified on synthetic CHM tiles (26k trees, TAO vs ITD corr 0.79).

## 2026-09-05 (non-vegetation screening)
- 00a drops building/water/bridge classes from canopy metrics and writes lidar2022_solid_frac_30m.tif (single-return share above 2 m). 01_frame excludes cells above frame.max_solid_fraction and logs the acres. Synthetic tiles now carry multi-return canopy and a single-return roof patch to exercise it.

## 2026-09-05 (bare earth)
- 00a now writes the per-tile 1 m DTM (lidar.dtm_tiles_dir) and publishes it with a VRT next to the CHM. Skip logic includes the DTM tile.

## 2026-09-05 (normalized LAZ)
- Optional height-normalized LAZ copy of every AOI tile (lidar.normalized_dir, default ...\2022\LAZ_Basin_HAG on the external drive); extra dim in the in-memory path, z = HAG in the chunked path. Tested both.

## 2026-09-05 (server run)
- config.yaml points at \\vcenter2\GIS_DATA\LiDAR\2022\LAZ, local scratch C:\lidar_scratch, publish_dir ...\2022\Derived; workers 3 and in_memory_max_points 40 M sized for the 32 GB server. 00a gained a publish step; scripts/run_lidar.py runs 00a (and 00_lidar) headless; docs/SERVER_RUN.md is the runbook.

## 2026-09-05 (network-drive rewrite)
- 00a rebuilt around the 2 TB LAZ archive on the network drive: drive inventory, AOI filter, local scratch staging, multiprocessing pool, per-tile resumable partials with height histograms, exact merge. Core moved to src/lidar.py. Verified: synthetic tiles, resume skip, scratch staging, in-memory and chunked paths.

## 2026-09-05 (latest)
- Added 00a_las_to_chm.ipynb: raw LAS/LAZ tiles to tile index, DTM, 1 m CHM tiles, and point-based 30 m metrics (cover, p95, mid-canopy, densities); laspy or arcpy engine. 00_lidar now reads the CHM tile folder and writes its cover/p95 under _chm_ names. Verified: synthetic LAS tiles -> 00a -> 00_lidar.

## 2026-09-05 (later)
- Added 00_lidar.ipynb: block-processed CHM metrics (cover 2 m and 5 m, p95, rumple, ITD per acre), optional LAZ mid-canopy fraction, grid snapped to lidar.grid_origin; verified on a synthetic CHM.

## 2026-09-05
- Initial build: PLAN.md, config.yaml, src (io, qa, layers, strata), four notebooks, spsurvey script. Chain verified end to end on the synthetic Basin (25 cells, 60/100/300 nested allocation, 300 primaries + 12 legacy + 438 backups).
