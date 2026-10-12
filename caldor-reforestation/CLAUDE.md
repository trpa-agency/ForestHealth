# caldor-reforestation

Where might we need to replant trees in the Tahoe Basin part of the 2021 Caldor Fire? One
arcpy pipeline, one single file app. Global conventions live two levels up in
`Documents\GitHub\CLAUDE.md`; the ForestHealth repo context is one level up.

Started Oct. 11, 2026.

## What it answers

1. Where high vegetation burn severity and high soil burn severity line up.
2. How big the high vegetation severity patches are.
3. Which high severity pixels sit farther than 150 m from a surviving seed source.

Frame: the Caldor incident perimeter clipped to the TRPA boundary, 30 m grid, NAD83 UTM 10N.
Patches are delineated across the whole fire so a patch that crosses the Basin boundary
keeps its full size; acres are reported inside the Basin.

## Layout

- `config.yaml` — every source path, class value, threshold, band, and tolerance. Nothing is
  hardcoded in the script.
- `scripts/reforestation_need.py` — the pipeline. `--check` verifies inputs without arcpy;
  `--stage inputs|analysis|web` reruns one part. Run from this folder with the
  `arcgispro-py3` interpreter by full path (the `python` on PATH lacks arcpy and yaml).
- `index.html` — the app. Reads `web/data/summary.json` and the GeoJSON next to it at load,
  same origin, so it runs locally with `python -m http.server` from this folder and on GitHub
  Pages at `https://trpa-agency.github.io/ForestHealth/caldor-reforestation/`.
- `web/data/` — GeoJSON (WGS84, generalized to 5 m) and `summary.json`. Committed.
- `outputs/` — CSV summary tables. Committed.
- `data/`, `logs/` — scratch gdb, fetched REST JSON, logs. Gitignored.

## Inputs (as of Oct. 11, 2026)

| Input | Source | Notes |
|---|---|---|
| Vegetation burn severity | `Fire/MapServer/5` on maps.trpa.org, 81,166 polygons, gridcode 0 to 4 and 9 | RAVG style 4 class product (1 unburned/very low, 2 low, 3 moderate, 4 high, 9 mask). The source raster was not found on F:; the polygons are rasterized at 30 m. If the raster turns up, set `veg_severity.raster`. |
| Soil burn severity | `F:\GIS\GIS_DATA\Fire\Caldor\Caldor_Final_Soil_Burn_Severity_for_team\*.shp` | BAER final BARC4, Sept. 14, 2021, dissolved by class, 218,952 acres. Same thing the Fire service publishes as layer 4. |
| Fire perimeter | `Caldor_Datalayers.gdb\CaldorFirePerimeter` | Incident perimeter, one polygon. |
| TRPA boundary | `Boundaries/MapServer/4` | |
| Pre-fire canopy cover | RRK download, CFO summer 2020, percent, 30 m | Decides whether a surviving pixel was forest. |
| CWHR type | RRK Fveg April 2023, WHRTYPE via the threshold `veg_type_nonurban` attribute table | Conifer filter on seed sources; vegetation type breakdown. |
| Ownership | `Ownership/MapServer/0`, OWNERSHIP_TYPE | Federal, State, Local, Private, blank (Unknown). |

## Method decisions

- **High vegetation severity** is class 4 of the published product. **High soil burn severity**
  is BARC4 class 4. Overlap is the pixelwise AND.
- **Seed source** is a pixel that burned at unburned/very low or low severity (or lies outside
  the perimeter), carried at least 25 percent canopy cover in 2020, and is a conifer CWHR type.
  Moderate severity does not count. All three parts are in `analysis.seed_source`.
- **Distance** is Euclidean distance to the nearest seed source pixel, computed over the
  perimeter plus a 600 m buffer so edges and the Basin boundary do not truncate it. The
  150 m planning cutoff is `seed_distance_threshold_m`; bands at 50, 100, 120, 150, 200, 300 m are
  written too so the app can show other cutoffs without a rerun. The 150 m figure is from
  Haffey et al. 2018 (Fire Ecology 14:143), Southwest ponderosa pine: areas more than 150 m
  from a seed source "are much less likely" to regenerate. Welch et al. 2016 and Stewart et
  al. 2021 give the Sierra mixed conifer distance response. Citations in `docs/references.md`.
- **Need frame.** Replanting need is only asked of pixels that were forest before the fire:
  conifer CWHR type or at least 25 percent canopy cover in 2020 (`analysis.need_frame`).
  The first run without the filter put 228 acres of montane chaparral and 16 of barren in
  the need total; the severity cross tabulation still covers every pixel.
- **Need code** on high vegetation severity pixels inside the Basin: 1 high veg only, 3 plus
  high soil, 5 plus beyond the cutoff, 7 all three.
- **Patches** are 8 connected regions of high vegetation severity. Size classes break at 10,
  100, and 200 acres: 200 is TRPA's adopted Landscape Fire Dynamics standard for a large high
  severity patch (the report's rationale is seed source loss and type conversion, with
  natural regeneration failing beyond about 120 m), and 10 and 100 follow PSW-GTR-270
  chapter 4. Patch depth is the distance from the nearest non high pixel.

## Known limits

- The vegetation severity polygons were published without metadata saying which RAVG metric
  they are (CBI, basal area loss, or canopy cover loss). Class 4 is "high" in all three but
  the thresholds differ. Confirm with the source before quoting the product name.
- Soil burn severity is the Sept. 14, 2021 BAER map, not a later field revision.
- Ownership comes from parcels; roads and unparceled land fall to Unknown.
