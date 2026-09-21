# Changelog

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
