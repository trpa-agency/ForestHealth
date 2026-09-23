"""Generate notebooks/06_tessellation.ipynb. Run: python scripts/build_tessellation_notebook.py

Edit this builder, regenerate, never hand-edit the .ipynb (repo convention).
Execute the result with the Pro env:
    python -m jupyter nbconvert --to notebook --execute --inplace notebooks/06_tessellation.ipynb

Paths inside the notebook use forward slashes on purpose: arcpy accepts them and it keeps
this builder free of doubled backslashes.
"""
import nbformat as nbf
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NB = ROOT / "notebooks"
NB.mkdir(exist_ok=True)

HEADER = '''import sys, os, math, json, time
from pathlib import Path
os.chdir(Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd())
sys.path.insert(0, str(Path.cwd()))
import numpy as np, pandas as pd
_t = time.time()
import arcpy
from src.io import load_config, get_logger
from src import tessellation as T

cfg = load_config()
log = get_logger("06_tessellation")
TC = cfg["tessellation"]
SR = arcpy.SpatialReference(int(TC["epsg"]))
CRS = f"EPSG:{int(TC['epsg'])}"
HA, AC = 10_000.0, 4046.8564224
STAMP = pd.Timestamp.today().strftime("%Y%m%d")

O = (Path.cwd() / cfg["paths"]["outputs"]).resolve(); O.mkdir(exist_ok=True)
P = (Path.cwd() / cfg["paths"]["processed"]).resolve(); P.mkdir(parents=True, exist_ok=True)
GDB = (O / TC["gdb"]).as_posix()                      # deliverable feature classes
WORK = (P / "tessellation_work.gdb").as_posix()       # scratch copies of the inputs
for g in (GDB, WORK):
    if not arcpy.Exists(g):
        arcpy.management.CreateFileGDB(str(Path(g).parent), Path(g).name)
arcpy.env.workspace = GDB
arcpy.env.overwriteOutput = True
arcpy.env.outputCoordinateSystem = SR                 # every copy lands in the tessellation CRS
arcpy.env.geographicTransformations = TC["datum_transformation"]
log.info(f"arcpy {arcpy.GetInstallInfo()['Version']} imported in {time.time() - _t:.0f} s; "
         f"CRS {SR.name} ({CRS}); gdb {GDB}")'''


def nb(name, cells):
    n = nbf.v4.new_notebook()
    n["cells"] = [nbf.v4.new_markdown_cell(c[1]) if c[0] == "md" else nbf.v4.new_code_cell(c[1]) for c in cells]
    n["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3 (arcgispro-py3)", "language": "python"}
    nbf.write(n, NB / f"{name}.ipynb")
    print("wrote", name)


nb("06_tessellation", [

# ------------------------------------------------------------------ why
("md", """# 06 Tessellation

Two grids, built with arcpy `GenerateTessellation`, from one fitted lattice.

**1. The Basin wide owl grid** for Pat Manley and Shale Hunter. Their California spotted owl (CSO) grid stops at the state line. This notebook recovers the lattice it was built on, regenerates every delivered cell exactly with its original `cell_id`, and extends the same lattice over the Nevada side. One layer goes out, with `source` saying which cells are delivered and which are new, plus the occupancy counts that size Pat's sampling increments.

**2. The sample design grid** for the VP9 (seral stage and canopy cover) and VP10 (stand density) plot network. A finer hexagon lattice at one third the owl cell area, sharing every centre with the owl lattice. TRPA draws on the fine grid; a plot lands in exactly one owl cell, so the Forest Service aggregates by location with nothing to reconcile.

## The fact that makes both possible

The owl grid was constructed as 400 hectare flat top hexagons in NAD83 UTM zone 10N and delivered in WGS84. Fitted over all 8,087 Sierra cells it is one exact lattice in UTM 10N, with a residual under five millimetres. `GenerateTessellation` builds flat top hexagons with a cell centre exactly on the lower left corner of the extent it is given, so anchoring the extent on a lattice point and asking for 400 hectares reproduces the delivered cells and continues them over Nevada. A transverse hexagon at one third the area, anchored the same way, is the fine lattice.

This only holds in UTM 10N. In California Albers the same cells are rotated 1.8 degrees, vary in area across the Sierra, and do not fit a single lattice. `tessellation.epsg` in `config.yaml` is not a preference.

## What this notebook does not do

Cell size is not a stratification; forest type and structure strata come from `02_strata`. The bin size sweep that earlier drafts ran (the criteria behind Pro's Evaluate Bin Sizes for Point Aggregation) is gone from here: it answers a display question, and on 125 sites its within cell test cannot run at any size. The sample design cell size follows from the sample size in `src/sample_size.py`, not from a point pattern. The reimplementation stays in `src/tessellation.py` if a dense point pattern ever warrants it."""),

("code", HEADER),

("code", '''def fetch(key: str, name: str) -> str:
    """Copy a config source, TRPA REST layer URL or local file, into the work gdb in the tessellation CRS."""
    src = str(TC["sources"][key])
    if not src.lower().startswith("http"):
        src = (Path.cwd() / src).resolve().as_posix()
    out = f"{WORK}/{name}"
    try:
        arcpy.management.CopyFeatures(src, out)
    except arcpy.ExecuteError:
        if src.lower().startswith("http") and arcpy.Exists(out):
            log.warning(f"{key}: service unreachable ({arcpy.GetMessages(2).strip().splitlines()[-1]}); "
                        f"reusing the copy already in {Path(WORK).name}")
        else:
            raise
    n = int(arcpy.management.GetCount(out)[0])
    log.info(f"{key}: {n:,} features -> {name} ({arcpy.Describe(out).spatialReference.name})")
    return out

def one_geom(fc: str, where: str | None = None):
    """Union of every shape in fc as a single arcpy Geometry."""
    geom = None
    with arcpy.da.SearchCursor(fc, ["SHAPE@"], where_clause=where) as cur:
        for (shp,) in cur:
            geom = shp if geom is None else geom.union(shp)
    return geom

def centroids(fc: str) -> np.ndarray:
    with arcpy.da.SearchCursor(fc, ["SHAPE@TRUECENTROID"]) as cur:
        return np.array([xy for (xy,) in cur], float)

def table(fc: str, fields: list, where: str | None = None) -> pd.DataFrame:
    with arcpy.da.SearchCursor(fc, fields, where_clause=where) as cur:
        return pd.DataFrame([list(r) for r in cur], columns=fields)

def add_fields(fc: str, spec: list) -> None:
    have = {f.name for f in arcpy.ListFields(fc)}
    for name, ftype, *rest in spec:
        if name not in have:
            arcpy.management.AddField(fc, name, ftype, field_length=rest[0] if rest else None)'''),

# ------------------------------------------------------------------ inputs
("md", """## 1. Inputs

Boundary, lake, state line, the delivered owl grid, and the TEON sites. `fetch` copies each one into a scratch geodatabase, projected to UTM 10N on the way in, so nothing downstream touches a service or a WGS84 file again.

The boundary matters more than it looks. The TRPA boundary, the LTBMU administrative boundary, and the USGS HUC8 disagree around the edges by enough to change the cell count. `tessellation.sources.boundary` names the authoritative one."""),

("code", '''boundary_fc = fetch("boundary", "boundary")
lake_fc = fetch("water", "lake")
states_fc = fetch("state_line", "states")
owl_fc = fetch("owl_grid", "owl_grid")
sites_fc = fetch("teon_sites", "teon_sites")

BOUND = one_geom(boundary_fc)
LAKE = one_geom(lake_fc)
LAND = BOUND.difference(LAKE)
NV = one_geom(states_fc, f"{TC['state_field']} = 'NV'")
log.info(f"boundary {BOUND.area / 1e6:,.1f} km2, lake {LAKE.area / 1e6:,.1f} km2, "
         f"land {LAND.area / 1e6:,.1f} km2 ({100 * LAND.area / BOUND.area:.0f}% of boundary)")'''),

# ------------------------------------------------------------------ fit
("md", """## 2. Recover the lattice

A cell lattice is two basis vectors and an origin: every centre sits at `origin + i * a1 + j * a2`. The construction is known (400 hectares, flat top), so `fit_lattice_xy` seeds a regular lattice from the first centre, assigns every delivered cell integer indices, and solves the affine map from indices to coordinates by least squares. The residual is the distance from each delivered centre to the nearest lattice point. Millimetres means the layer is one exact lattice in this CRS. Metres would mean it was built somewhere else, and the assertion below would stop the extension rather than let it ship cells that are nearly right.

The fit runs over all 8,087 Sierra cells, not a local subset, because in UTM 10N it holds end to end. The free fit is then snapped to the construction, exact area and exact orientation with the fitted origin, and the residual is reported against the snapped lattice. A least squares fit is regular only to a few parts per million, which is two centimetres of drift across the Basin, and `GenerateTessellation` is exactly regular."""),

("code", '''owl_xy = centroids(owl_fc)
owl_ids = table(owl_fc, [TC["owl_id_field"]])[TC["owl_id_field"]].tolist()
A_M2 = float(TC["cell_area_ha"]) * HA

fit = T.fit_lattice_xy(owl_xy, area_m2=A_M2, rotation_deg=float(TC["hex_orientation_deg"]), shape="hex", crs=CRS)
print("free affine fit:")
print(pd.Series(fit.summary()).to_string())

# Snap to the construction: exact configured area, exact orientation, fitted origin. The free fit is
# regular only to a few parts per million, which is 2 cm of drift across the Basin; GenerateTessellation
# is exactly regular, so everything downstream is derived from the snapped lattice, not the fit.
lat = T.Lattice.regular(spacing_m=T.hex_spacing_from_area(A_M2), rotation_deg=float(TC["hex_orientation_deg"]),
                        origin_x=fit.origin_x, origin_y=fit.origin_y, shape="hex", crs=CRS)
res = T.residuals_xy(owl_xy, lat)
print(f"\\nsnapped to {lat.cell_area_ha:.4f} ha at {lat.rotation_deg:.1f} degrees; residual over all {len(owl_xy):,} "
      f"delivered cells (m): median {np.median(res):.4f}  p99 {np.percentile(res, 99):.4f}  max {res.max():.4f}")
assert res.max() < TC["max_fit_residual_m"], "delivered grid is not one exact lattice in this CRS"
assert fit.anisotropy < 1e-4, "free fit is not regular; the construction assumption is wrong"

owl_ij = np.round(lat.indices(owl_xy)).astype(int)
assert len({tuple(r) for r in owl_ij}) == len(owl_ij), "two delivered cells share a lattice index"
owl_index = {tuple(ij): cid for ij, cid in zip(owl_ij, owl_ids)}
log.info(f"lattice recovered: spacing {lat.spacing_m:.4f} m, area {lat.cell_area_ha:.4f} ha, max residual {res.max():.4f} m")'''),

# ------------------------------------------------------------------ extend
("md", """## 3. Extend the grid over the Basin

`GenerateTessellation` puts a cell centre exactly on the extent's lower left corner and fills up and to the right. So the extent is anchored on a lattice point southwest of the Basin, the tool is asked for the configured cell area, and the output is the same lattice. The first check below proves it: every generated centre is a fitted lattice point to within a centimetre.

Cells that intersect the boundary are kept and attributed: lattice indices, a deterministic `cell_key` from them, the delivered `cell_id` where the indices match a delivered cell and a new id otherwise, `source`, the fraction of each cell inside the boundary and on land, and which state the centre is in. Both projected and geodesic areas are carried, because a UTM cell of exactly 400 hectares is about 399.7 on the ground at this distance from the central meridian."""),

("code", '''def anchor_below(lat, x, y):
    """Lattice point with integer indices at or southwest of (x, y), the one nearest the corner."""
    i0, j0 = np.floor(lat.indices(np.array([[x, y]]))[0]).astype(int)
    best = None
    for i in range(i0 - 3, i0 + 3):
        for j in range(j0 - 3, j0 + 3):
            cx, cy = lat.centres(np.array([[i, j]]))[0]
            if cx <= x and cy <= y and (best is None or cx + cy > best[0] + best[1]):
                best = (float(cx), float(cy), int(i), int(j))
    return best

e = BOUND.extent
pad = TC["pad_cells"] * lat.spacing_m
ax, ay, ai, aj = anchor_below(lat, e.XMin - pad, e.YMin - pad)
EXT = arcpy.Extent(ax, ay, e.XMax + pad, e.YMax + pad, spatial_reference=SR)
log.info(f"anchor: lattice index ({ai}, {aj}) at ({ax:.3f}, {ay:.3f}); extent to ({e.XMax + pad:.0f}, {e.YMax + pad:.0f})")

raw400 = f"{WORK}/hex{int(TC['cell_area_ha'])}_raw"
arcpy.management.GenerateTessellation(raw400, EXT, "HEXAGON", f"{TC['cell_area_ha']} Hectares", SR)
raw_res = T.residuals_xy(centroids(raw400), lat)
print(f"GenerateTessellation reproduces the fitted lattice: max centre offset {raw_res.max():.6f} m over {len(raw_res):,} cells")
assert raw_res.max() < 0.01'''),

("code", '''GRID = f"TahoeBasin_Hex{int(TC['cell_area_ha'])}ha"
arcpy.management.MakeFeatureLayer(raw400, "hex400_lyr")
arcpy.management.SelectLayerByLocation("hex400_lyr", "INTERSECT", boundary_fc)
arcpy.management.CopyFeatures("hex400_lyr", f"{GDB}/{GRID}")
arcpy.management.DeleteField(GRID, ["GRID_ID"])

CELL_FIELDS = [("i", "LONG"), ("j", "LONG"), ("cell_key", "TEXT", 16), ("cell_id", "TEXT", 16),
               ("source", "TEXT", 8), ("x_coord", "DOUBLE"), ("y_coord", "DOUBLE"),
               ("area_ha", "DOUBLE"), ("geod_ha", "DOUBLE"), ("in_frac", "DOUBLE"),
               ("land_frac", "DOUBLE"), ("land_ha", "DOUBLE"), ("state", "TEXT", 2)]

def attribute_cells(fc, lat, key_prefix, index=None, new_prefix=None):
    """Lattice indices, keys, ids, boundary and land fractions, state. index maps (i, j) -> delivered id."""
    cols = [n for n, *_ in CELL_FIELDS]
    with arcpy.da.UpdateCursor(fc, ["SHAPE@"] + cols) as cur:
        for r in cur:
            shp = r[0]
            c = shp.trueCentroid
            i, j = np.round(lat.indices(np.array([[c.X, c.Y]]))[0]).astype(int)
            cid = index.get((int(i), int(j))) if index else None
            inside = shp.intersect(BOUND, 4).area
            land = shp.intersect(LAND, 4).area
            r[1:] = [int(i), int(j), f"{key_prefix}{i:+05d}{j:+05d}", cid, "existing" if cid else "new",
                     c.X, c.Y, shp.area / HA, shp.getArea("GEODESIC", "HECTARES"),
                     inside / shp.area, land / shp.area, land / HA,
                     "NV" if NV.contains(arcpy.PointGeometry(c, SR)) else "CA"]
            cur.updateRow(r)
    if new_prefix:   # new cells get sequential ids in row order, south to north then west to east
        n = 0
        with arcpy.da.UpdateCursor(fc, ["cell_id"], where_clause="cell_id IS NULL",
                                   sql_clause=(None, "ORDER BY j, i")) as cur:
            for r in cur:
                n += 1
                r[0] = f"{new_prefix}{n:04d}"
                cur.updateRow(r)

add_fields(GRID, CELL_FIELDS)
attribute_cells(GRID, lat, key_prefix="C", index=owl_index, new_prefix=TC["new_id_prefix"])

cells = table(GRID, ["cell_key", "cell_id", "source", "state", "area_ha", "geod_ha", "in_frac", "land_frac", "land_ha"])
print(pd.crosstab(cells["state"], cells["source"], margins=True).to_string())
print(f"\\ncells with land: {(cells.land_frac > TC['min_land_frac']).sum()}   all water: {(cells.land_frac <= TC['min_land_frac']).sum()}")
print(f"cell area: {cells.area_ha.mean():.2f} ha projected, {cells.geod_ha.mean():.2f} ha geodesic ({cells.geod_ha.mean() * HA / AC:.1f} ac)")'''),

("code", '''# Regenerated cells must reproduce the delivered ones. IoU below min_iou means the lattice is close but wrong.
owl_shapes = {cid: shp for shp, cid in arcpy.da.SearchCursor(owl_fc, ["SHAPE@", TC["owl_id_field"]])}
iou = []
with arcpy.da.SearchCursor(GRID, ["SHAPE@", "cell_id"], where_clause="source = 'existing'") as cur:
    for shp, cid in cur:
        o = owl_shapes[cid]
        iou.append(shp.intersect(o, 4).area / shp.union(o).area)
iou = np.array(iou)
print(f"IoU against {len(iou)} delivered cells: min {iou.min():.5f}  median {np.median(iou):.5f}")
assert iou.min() > TC["min_iou"], "regenerated cells do not reproduce the delivered grid"'''),

# ------------------------------------------------------------------ occupancy
("md", """## 4. Occupancy: what the existing sites already cover

Shale's question in plain terms: with the 99 core sites and the remaining MSIM sites on the grid, how many cells are still empty, and how many new sites would the higher increments need. That is a spatial join and a count, and it is the number that sizes Pat's increments.

Two things to watch. Cells holding two sites are real, and a one point per cell design has to decide whether a doubled cell keeps both. Sites in no cell are outside the boundary, which after the extension is the only way that can happen."""),

("code", '''AQ, C99 = TC["site_fields"]["aquatic"], TC["site_fields"]["core99"]
sj = f"{WORK}/sites_in_cells"
arcpy.analysis.SpatialJoin(sites_fc, GRID, sj, "JOIN_ONE_TO_ONE", "KEEP_ALL", match_option="WITHIN")
s = table(sj, ["Join_Count", AQ, C99, "cell_key", "cell_id"])
s["group"] = np.where(s[AQ].eq("Y"), "aquatic", np.where(s[C99].eq("Y"), "core99", "msim_other"))
print(s["group"].value_counts().to_string())
print(f"\\nsites in no cell: {(s.Join_Count == 0).sum()}")

hit = s[s.Join_Count > 0]
counts = pd.crosstab(hit["cell_key"], hit["group"]).reindex(columns=["core99", "msim_other", "aquatic"], fill_value=0)
add_fields(GRID, [("n_sites", "SHORT"), ("n_core99", "SHORT"), ("n_msim", "SHORT"), ("n_aquatic", "SHORT")])
with arcpy.da.UpdateCursor(GRID, ["cell_key", "n_sites", "n_core99", "n_msim", "n_aquatic"]) as cur:
    for r in cur:
        c = counts.loc[r[0]] if r[0] in counts.index else None
        r[1:] = [int(c.sum()), int(c["core99"]), int(c["msim_other"]), int(c["aquatic"])] if c is not None else [0, 0, 0, 0]
        cur.updateRow(r)

cells = table(GRID, ["cell_key", "cell_id", "source", "state", "area_ha", "geod_ha", "in_frac", "land_frac", "land_ha",
                     "n_sites", "n_core99", "n_msim", "n_aquatic"])
land = cells[cells.land_frac > TC["min_land_frac"]]
terr = land.n_core99 + land.n_msim
print(f"\\ncells with land: {len(land)}")
print(f"  holding a core99 site:         {(land.n_core99 > 0).sum()}")
print(f"  holding any terrestrial site:  {(terr > 0).sum()}")
print(f"  holding two or more:           {(terr > 1).sum()}")
print(f"  EMPTY:                         {(terr == 0).sum()}")

inc = pd.DataFrame([
    {"increment": "1. core 99 resample sites", "sites": int((s.group == "core99").sum()), "cells_occupied": int((land.n_core99 > 0).sum())},
    {"increment": "2. plus remaining MSIM", "sites": int((s.group != "aquatic").sum()), "cells_occupied": int((terr > 0).sum())},
    {"increment": "4. one site in every land cell", "sites": int(len(land)), "cells_occupied": int(len(land))},
])
inc["new_sites_needed"] = (inc["cells_occupied"] - int((terr > 0).sum())).clip(lower=0)
print("\\n" + inc.to_string(index=False))
log.info("increment 3 (under represented vegetation types) is a targeted allocation inside cells, not a cell count")'''),

# ------------------------------------------------------------------ fine grid
("md", """## 5. The sample design grid

The owl cell puts about 117 cells on the 115,396 acre forested threshold frame, against a sample size of about 300. One point per owl cell is a third of a design. The fix is not a different grid but a finer one on the same centres.

Hexagons never subdivide into hexagons, so no hex grid truly nests. What a design needs is weaker and exact: at area ratios 3 and 4 there is a finer hex lattice every one of whose centres includes every owl centre. Ratio 3 turns the lattice 30 degrees, which is the transverse hexagon `GenerateTessellation` already makes; ratio 4 keeps the orientation. Anchored on the same corner, either shares every owl centre to a fraction of a millimetre, and the checks below prove it on the generated cells rather than assume it.

What this buys: a plot drawn on the fine grid lies in exactly one owl cell, so the Forest Service aggregates TRPA plots to owl cells by location. What it does not buy: a parent cell for every fine cell. Two thirds of ratio 3 cells are centred on an owl cell vertex and overlap three owl cells equally. `on_owl_ctr` flags the third that share a centre. Do not add a parent field; aggregation is by plot, not by cell."""),

("code", '''ratio = int(TC["fine_ratio"])
assert ratio in (3, 4), "only ratios 3 and 4 nest without a rotation GenerateTessellation cannot make"
fine_lat = T.fine_lattice(lat, ratio)
shape_type = {3: "TRANSVERSE_HEXAGON", 4: "HEXAGON"}[ratio]
FINE = f"TahoeBasin_Hex{round(fine_lat.cell_area_ha)}ha"

raw_fine = f"{WORK}/hex_fine_raw"
arcpy.management.GenerateTessellation(raw_fine, EXT, shape_type, f"{A_M2 / ratio:.6f} SquareMeters", SR)
fine_res = T.residuals_xy(centroids(raw_fine), fine_lat)
owl_on_fine = T.residuals_xy(owl_xy, fine_lat)
print(f"{shape_type} at {fine_lat.cell_area_ha:.3f} ha: generated centres sit on the fine lattice to {fine_res.max():.6f} m; "
      f"every delivered owl centre is a fine centre to {owl_on_fine.max():.4f} m (fit tolerance {TC['max_fit_residual_m']} m)")
assert fine_res.max() < 0.01, "GenerateTessellation output does not sit on the derived fine lattice"
assert owl_on_fine.max() < TC["max_fit_residual_m"], "owl centres do not sit on the fine lattice"

arcpy.management.MakeFeatureLayer(raw_fine, "fine_lyr")
arcpy.management.SelectLayerByLocation("fine_lyr", "INTERSECT", boundary_fc)
arcpy.management.CopyFeatures("fine_lyr", f"{GDB}/{FINE}")
arcpy.management.DeleteField(FINE, ["GRID_ID"])
add_fields(FINE, CELL_FIELDS + [("on_owl_ctr", "SHORT"), ("owl_key", "TEXT", 16)])
attribute_cells(FINE, fine_lat, key_prefix=TC["fine_id_prefix"], index=None, new_prefix=None)
arcpy.management.DeleteField(FINE, ["cell_id", "source"])   # every fine cell is new; those fields mean nothing here
with arcpy.da.UpdateCursor(FINE, ["x_coord", "y_coord", "on_owl_ctr", "owl_key"]) as cur:
    for r in cur:
        ij = lat.indices(np.array([[r[0], r[1]]]))[0]
        on = bool(np.abs(ij - np.round(ij)).max() < 1e-6)
        i, j = np.round(ij).astype(int)
        r[2:] = [int(on), f"C{i:+05d}{j:+05d}" if on else None]
        cur.updateRow(r)

fine = table(FINE, ["cell_key", "state", "area_ha", "geod_ha", "in_frac", "land_frac", "land_ha", "on_owl_ctr"])
print(f"\\n{FINE}: {len(fine)} cells intersect the boundary, {(fine.land_frac > TC['min_land_frac']).sum()} with land, "
      f"{fine.on_owl_ctr.sum()} centred on an owl cell ({100 * fine.on_owl_ctr.mean():.0f}%, expect {100 / ratio:.0f}%)")
frame_ac = sum(cfg["forest_types"]["population_acres"].values())
for name, li in [("owl", lat), ("fine", fine_lat)]:
    print(f"  {name} cell {li.cell_area_ha:7.2f} ha = {li.cell_area_acres:7.1f} ac -> {frame_ac / li.cell_area_acres:6.0f} cells on the "
          f"{frame_ac:,} ac threshold frame (target {cfg['allocation']['levels']['full']} plots)")'''),

# ------------------------------------------------------------------ vegetation
("md", """## 6. Vegetation attributes: forest type, the WHR crosswalk, and seral and canopy class

Both grids carry the vegetation conditions the threshold standards are assessed against, so a cell can be read the way TRPA reports: by the three forest types and the five seral and canopy classes. That is what makes the fine grid a reporting unit for the plot network rather than just a frame, and it is what lets any cell be compared with the plots that land in it. It also answers TEON's request to attribute the hexes with vegetation conditions, since the same fields serve both. The source is the threshold analysis rasters, which live in the threshold project geodatabase on F: and nowhere else. Without F: this section stops with a clear error and nothing before it needs rerunning.

**One classification, two levels.** The report does not use two vegetation schemes. Its frame raster is the Sierra Nevada Regional Resource Kit 2023 CWHR type layer, and every cell of it carries both a WHRTYPE (Sierran mixed conifer, Jeffrey pine, red fir, lodgepole pine, white fir, eastside pine, juniper, subalpine conifer, aspen, montane chaparral, wet meadow, and so on) and CWHR's own lifeform rollup of that type (conifer forest, conifer woodland, hardwood forest, hardwood woodland, herbaceous, shrub, wetland, barren, water, urban). Table 1 is the type level, restricted to the seven types that make up the assessed frame and grouped into the three TRPA reporting types. The appendix map is the lifeform level of the same raster. The crosswalk table this section writes is read straight from the raster attribute table, so it is the report's, not a reconstruction.

**Primary attribution is the threshold grouping.** `jp_ac`, `smc_ac`, `rf_ac` are the acres of each TRPA type in the cell and `frame_ac` their sum, with `frame_frac` the share of the cell inside the frame. `jp_pct`, `smc_pct`, `rf_pct` are shares of the frame area in the cell, so they sum to 100 wherever there is frame. `trpa_type` is the dominant of the three and `type_pct` its share. Subalpine conifer is not one of the three; it has its own non-degradation standard and sits outside this frame on purpose.

**Secondary field to crosswalk from.** `whr_type` is the dominant WHRTYPE over all non-urban land in the cell, forest or not, `whr_pct` its share of that land, and `lifeform` its CWHR lifeform. The full cell by WHRTYPE table goes out as a CSV so any other grouping can be built from it.

**Seral stage and canopy class.** `sc_early`, `sc_midop`, `sc_midcl`, `sc_lateop`, `sc_latecl` are the shares of the frame area in the cell in each of the five VP9 classes: seral stage by quadratic mean diameter at 5 and 25 inches, open versus closed at 40 percent cover for Jeffrey pine and 50 percent for the other two. They are computed here from the component rasters with the class logic in `config.yaml`, not read from the classification raster in the geodatabase, because that product predates the fix to the mid and late canopy codes recorded in the ForestHealth repo. The five shares sum to less than 100 where the seral raster has no data."""),

("code", '''FRAME, SERAL, CANOPY = (TC["sources"][k] for k in ("frame_raster", "seral_raster", "canopy_raster"))
missing = [r for r in (FRAME, SERAL, CANOPY) if not arcpy.Exists(r)]
assert not missing, f"threshold rasters not reachable, mount F: and rerun from here: {missing}"
arcpy.CheckOutExtension("Spatial")
from arcpy.sa import Raster, Con, IsNull, SetNull, Reclassify, RemapValue, TabulateArea

RSR = arcpy.Describe(FRAME).spatialReference
CELL = float(arcpy.Describe(FRAME).meanCellWidth)
W2T = TC["whr_to_type"]
TYPES = ("JP", "SMC", "RF")
SC = TC["seral_canopy_classes"]

# The crosswalk, read from the raster attribute table. Value codes differ by source map, so group on WHRTYPE.
xw = table(FRAME, ["Value", "Count", "WHRTYPE", "WHRNAME", "WHR13NAME"])
xw["trpa_type"] = xw["WHRTYPE"].map(W2T).fillna("not assessed")
xw["acres_nonurban"] = xw["Count"] * CELL * CELL / AC
crosswalk = (xw.groupby(["WHRTYPE", "WHRNAME", "WHR13NAME", "trpa_type"], as_index=False)["acres_nonurban"].sum()
               .rename(columns={"WHR13NAME": "lifeform"}).sort_values("acres_nonurban", ascending=False))
print(crosswalk.round(0).to_string(index=False))
frame_by_type = crosswalk[crosswalk.trpa_type != "not assessed"].groupby("trpa_type")["acres_nonurban"].sum()
print("\\nassessed frame acres by TRPA type, raster vs report Table 1:")
for t in TYPES:
    print(f"  {t:4s} {frame_by_type.get(t, 0):9,.0f}  vs {cfg['forest_types']['population_acres'][t]:9,}")
print(f"  all  {frame_by_type.sum():9,.0f}  vs {frame_ac:9,}")
LIFEFORM = crosswalk.drop_duplicates("WHRTYPE").set_index("WHRTYPE")["lifeform"].to_dict()'''),

("code", '''# Forest type (1 JP, 2 SMC, 3 RF) and the five seral and canopy classes, on the frame only.
code = {"JP": 1, "SMC": 2, "RF": 3}
cut = cfg["threshold"]["cover_open_closed_pct"]
with arcpy.EnvManager(outputCoordinateSystem=RSR, snapRaster=FRAME, cellSize=FRAME, extent=FRAME):
    ft = Reclassify(Raster(FRAME), "WHRTYPE", RemapValue([[w, code[t]] for w, t in W2T.items()]), "NODATA")
    ft.save(f"{WORK}/frame_type")
    cc = Con(IsNull(Raster(CANOPY)), 0, Raster(CANOPY))
    closed = Con(ft == 1, Con(cc >= cut["JP"], 1, 0), Con(ft == 2, Con(cc >= cut["SMC"], 1, 0), Con(cc >= cut["RF"], 1, 0)))
    se = Raster(SERAL)
    cls = Con(se == 1, 1, Con(se == 2, Con(closed == 1, 3, 2), Con(se == 3, Con(closed == 1, 5, 4))))
    cls = SetNull(IsNull(ft), cls)
    cls.save(f"{WORK}/frame_seral_canopy")
sc_tab = table(f"{WORK}/frame_seral_canopy", ["Value", "Count"])
sc_tab["class"] = sc_tab["Value"].map(SC); sc_tab["acres"] = sc_tab["Count"] * CELL * CELL / AC
sc_tab["pct_of_frame"] = 100 * sc_tab["acres"] / frame_by_type.sum()
print(sc_tab[["Value", "class", "acres", "pct_of_frame"]].round(1).to_string(index=False))
log.info(f"seral and canopy classes cover {sc_tab.acres.sum():,.0f} of {frame_by_type.sum():,.0f} frame acres")'''),

("code", '''VEG_FIELDS = [("frame_ac", "DOUBLE"), ("frame_frac", "DOUBLE"), ("jp_ac", "DOUBLE"), ("smc_ac", "DOUBLE"), ("rf_ac", "DOUBLE"),
              ("jp_pct", "DOUBLE"), ("smc_pct", "DOUBLE"), ("rf_pct", "DOUBLE"), ("trpa_type", "TEXT", 4), ("type_pct", "DOUBLE"),
              ("whr_type", "TEXT", 4), ("whr_pct", "DOUBLE"), ("lifeform", "TEXT", 20), ("other_ac", "DOUBLE"),
              ("sc_early", "DOUBLE"), ("sc_midop", "DOUBLE"), ("sc_midcl", "DOUBLE"), ("sc_lateop", "DOUBLE"), ("sc_latecl", "DOUBLE")]
SC_FIELD = {1: "sc_early", 2: "sc_midop", 3: "sc_midcl", 4: "sc_lateop", 5: "sc_latecl"}

def tabulate(fc, raster, field):
    """Area (m2) of each raster class per cell, zones projected to the raster's CRS so nothing is resampled."""
    zones = f"{WORK}/{fc}_albers"
    arcpy.management.Project(fc, zones, RSR)
    tab = f"{WORK}/tab_{fc}_{field}"
    with arcpy.EnvManager(snapRaster=FRAME, cellSize=FRAME):
        TabulateArea(zones, "cell_key", raster, field, tab, CELL)
    # An integer class field yields VALUE_1, VALUE_2, ...; a string class field yields the values themselves
    # (RFR, SMC, ...) with no prefix. The zone key comes back upper cased.
    cols = [f.name for f in arcpy.ListFields(tab) if f.name.upper() not in ("OBJECTID", "CELL_KEY")]
    t = table(tab, ["cell_key"] + cols).set_index("cell_key")
    pre = field.upper() + "_"
    t.columns = [c[len(pre):] if c.upper().startswith(pre) else c for c in t.columns]
    return t

veg_long, veg_stats = [], {}
for fc in (GRID, FINE):
    add_fields(fc, VEG_FIELDS)
    keys = table(fc, ["cell_key", "land_ha"]).set_index("cell_key")
    whr = (tabulate(fc, FRAME, "WHRTYPE") / AC).reindex(keys.index, fill_value=0.0)            # acres by WHRTYPE
    scl = (tabulate(fc, f"{WORK}/frame_seral_canopy", "Value") / AC).reindex(keys.index, fill_value=0.0)
    scl.columns = [int(c) for c in scl.columns]
    type_ac = pd.DataFrame({t: whr[[w for w in W2T if W2T[w] == t and w in whr.columns]].sum(axis=1) for t in TYPES})
    frame = type_ac.sum(axis=1)
    land_tab = whr.sum(axis=1)
    dom_t = type_ac.idxmax(axis=1).where(frame > 0)
    dom_w = whr.idxmax(axis=1).where(land_tab > 0)
    rows = {}
    for k in keys.index:
        f = frame[k]
        r = {"frame_ac": f, "frame_frac": None, "jp_ac": type_ac.at[k, "JP"], "smc_ac": type_ac.at[k, "SMC"], "rf_ac": type_ac.at[k, "RF"],
             "jp_pct": 100 * type_ac.at[k, "JP"] / f if f else None, "smc_pct": 100 * type_ac.at[k, "SMC"] / f if f else None,
             "rf_pct": 100 * type_ac.at[k, "RF"] / f if f else None,
             "trpa_type": dom_t[k] if f else None, "type_pct": 100 * type_ac.loc[k].max() / f if f else None,
             "whr_type": dom_w[k] if land_tab[k] else None, "whr_pct": 100 * whr.loc[k].max() / land_tab[k] if land_tab[k] else None,
             "lifeform": LIFEFORM.get(dom_w[k]) if land_tab[k] else None, "other_ac": land_tab[k] - f}
        for v, name in SC_FIELD.items():
            r[name] = 100 * scl.at[k, v] / f if (f and v in scl.columns) else None
        rows[k] = r
        for w in whr.columns:
            if whr.at[k, w] > 0:
                veg_long.append({"grid": fc, "cell_key": k, "whr_type": w, "acres": whr.at[k, w],
                                 "pct_of_cell_land": 100 * whr.at[k, w] / land_tab[k],
                                 "trpa_type": W2T.get(w, "not assessed"), "lifeform": LIFEFORM.get(w)})
    names = [n for n, *_ in VEG_FIELDS]
    with arcpy.da.UpdateCursor(fc, ["SHAPE@", "cell_key"] + names) as cur:
        for rec in cur:
            r = rows[rec[1]]
            r["frame_frac"] = r["frame_ac"] * AC / rec[0].area
            rec[2:] = [r[n] for n in names]
            cur.updateRow(rec)
    v = table(fc, ["cell_key", "land_frac", "frame_ac", "frame_frac", "trpa_type", "whr_type", "lifeform"])
    veg_stats[fc] = {"frame_acres": float(v.frame_ac.sum()), "cells_touching_frame": int((v.frame_frac > 0).sum()),
                     "cells_half_in_frame": int((v.frame_frac >= 0.5).sum()), "cell_equivalents": float(v.frame_frac.sum()),
                     "cells_by_trpa_type": v.trpa_type.value_counts().to_dict(), "cells_by_lifeform": v.lifeform.value_counts().to_dict()}
    print(f"\\n{fc}: frame {v.frame_ac.sum():,.0f} ac over {(v.frame_frac > 0).sum()} cells "
          f"({v.frame_frac.sum():.0f} cell equivalents); dominant type of cells with frame: {v.trpa_type.value_counts().to_dict()}")
    print(f"  dominant lifeform of cells with land: {v[v.land_frac > TC['min_land_frac']].lifeform.value_counts().to_dict()}")
veg_long = pd.DataFrame(veg_long)
log.info(f"vegetation attributes written to {GRID} and {FINE}; {len(veg_long):,} cell by WHRTYPE rows")'''),

# ------------------------------------------------------------------ export
("md", """## 7. Exports

Both grids go out as feature classes in `outputs/tessellation.gdb`, plus a shapefile and a GeoPackage of each. The owl extension is one layer with every cell, `source` distinguishing delivered from new and the original `cell_id` preserved, so Pat and Shale drop it in without merging two grids.

Everything is written in UTM 10N. A hexagon grid is not an ordinary vector layer; its value is the construction, equal projected area, constant spacing, one orientation, and those hold in the projection it was constructed in and nowhere else. Reprojecting forward costs a consumer nothing. Reprojecting back is forensics, which is what section 2 had to do. The handoff note carries the CRS, the datum transformation applied to the WGS84 inputs, the cell area, the spacing, the anchor, and the fit residual, so the next person can extend the grid again instead of refitting it."""),

("code", '''def export(fc: str, base: str) -> dict:
    out = {"gdb": f"{GDB}/{fc}"}
    shp = O / f"{base}_{STAMP}.shp"
    arcpy.conversion.ExportFeatures(fc, shp.as_posix())
    out["shp"] = shp.name
    gpkg = O / f"{base}_{STAMP}.gpkg"
    if gpkg.exists():
        gpkg.unlink()
    arcpy.management.CreateSQLiteDatabase(gpkg.as_posix(), "GEOPACKAGE_1.3")
    arcpy.conversion.ExportFeatures(fc, f"{gpkg.as_posix()}/{fc}")   # no "main." prefix, or the layer is named "main"
    out["gpkg"] = gpkg.name
    log.info(f"exported {fc} -> {out['shp']}, {out['gpkg']}")
    return out

files = {GRID: export(GRID, f"{GRID}_UTM10N"), FINE: export(FINE, f"{FINE}_UTM10N")}

lattice_rows = [{"grid": GRID, **lat.summary()}, {"grid": FINE, **fine_lat.summary()}]
pd.DataFrame(lattice_rows).to_csv(O / "tessellation_lattice_parameters.csv", index=False)
cells.to_csv(O / f"{GRID}_occupancy_{STAMP}.csv", index=False)
inc.to_csv(O / f"teon_increments_{STAMP}.csv", index=False)
crosswalk.to_csv(O / f"whrtype_crosswalk_{STAMP}.csv", index=False)
veg_long.to_csv(O / f"TahoeBasin_Hex_whrtype_by_cell_{STAMP}.csv", index=False)
sc_tab[["Value", "class", "acres", "pct_of_frame"]].to_csv(O / f"seral_canopy_class_acres_{STAMP}.csv", index=False)

summary = {
    "generated": pd.Timestamp.today().strftime("%Y-%m-%d"),
    "crs": CRS, "datum_transformation": TC["datum_transformation"],
    "boundary": TC["sources"]["boundary"], "basin_land_km2": round(LAND.area / 1e6, 1),
    "grid": {
        "name": GRID, "cell_ha": round(lat.cell_area_ha, 2), "cell_acres": round(float(cells.geod_ha.mean() * HA / AC), 1),
        "cell_ha_geodesic": round(float(cells.geod_ha.mean()), 2), "spacing_m": round(lat.spacing_m, 3),
        "total_cells": int(len(cells)), "existing_cells": int((cells.source == "existing").sum()),
        "new_cells": int((cells.source == "new").sum()), "nevada_new_cells": int(((cells.source == "new") & (cells.state == "NV")).sum()),
        "land_cells": int(len(land)), "occupied_cells": int((terr > 0).sum()), "empty_cells": int((terr == 0).sum()),
        "fit_residual_median_m": round(float(np.median(res)), 4), "fit_residual_max_m": round(float(res.max()), 4),
        "iou_min": round(float(iou.min()), 4), "anisotropy": round(lat.anisotropy, 6),
        "anchor_xy": [ax, ay], "anchor_ij": [ai, aj], **{f"file_{k}": v for k, v in files[GRID].items()},
    },
    "increments": {"label": inc.increment.tolist(), "sites": inc.sites.tolist(), "cells": inc.cells_occupied.tolist(),
                   "new_sites_needed": inc.new_sites_needed.tolist(), "source": Path(TC["sources"]["teon_sites"]).name},
    "fine": {
        "name": FINE, "ratio": ratio, "shape": shape_type, "cell_ha": round(fine_lat.cell_area_ha, 3),
        "cell_acres": round(fine_lat.cell_area_acres, 1), "spacing_m": round(fine_lat.spacing_m, 3),
        "total_cells": int(len(fine)), "land_cells": int((fine.land_frac > TC["min_land_frac"]).sum()),
        "on_owl_centre": int(fine.on_owl_ctr.sum()), "expected_cells_on_frame": round(frame_ac / fine_lat.cell_area_acres),
        "frame": veg_stats.get(FINE), **{f"file_{k}": v for k, v in files[FINE].items()},
    },
    "veg": {
        "frame_acres_by_type": {t: float(frame_by_type.get(t, 0)) for t in TYPES},
        "frame_acres_report": cfg["forest_types"]["population_acres"],
        "seral_canopy_pct_of_frame": dict(zip(sc_tab["class"], sc_tab["pct_of_frame"].round(1))),
        "grid": veg_stats.get(GRID), "fine": veg_stats.get(FINE),
    },
    "frame_acres_configured": int(frame_ac), "target_plots": int(cfg["allocation"]["levels"]["full"]),
}
(O / "tessellation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

frac_word = {3: "third", 4: "quarter"}[ratio]
handoff = f"""Tahoe Basin hexagon grids, generated {summary['generated']} by plot-network-design/notebooks/06_tessellation.ipynb

CRS: NAD83 UTM zone 10N ({CRS}). The lattice exists only in this projection; reproject copies forward, never the master.
Datum transformation applied to the WGS84 partner files on import: {TC['datum_transformation']}

{GRID}: extension of the California spotted owl grid over the whole Basin.
  cell area {lat.cell_area_ha:.3f} ha projected ({cells.geod_ha.mean():.2f} ha, {cells.geod_ha.mean() * HA / AC:.1f} ac geodesic)
  centre spacing {lat.spacing_m:.4f} m, flat top, GenerateTessellation HEXAGON anchored at ({ax:.3f}, {ay:.3f})
  {len(cells)} cells intersect the TRPA boundary: {(cells.source == 'existing').sum()} delivered (cell_id kept), {(cells.source == 'new').sum()} new (cell_id {TC['new_id_prefix']}nnnn)
  fit residual over 8,087 delivered cells: max {res.max():.4f} m; IoU against delivered cells min {iou.min():.5f}
  fields: cell_key (lattice index), cell_id, source, state, in_frac, land_frac, land_ha, n_sites, n_core99, n_msim, n_aquatic

{FINE}: sample design grid, one {frac_word} of the owl cell, {shape_type}, same anchor.
  cell area {fine_lat.cell_area_ha:.3f} ha ({fine_lat.cell_area_acres:.1f} ac), spacing {fine_lat.spacing_m:.4f} m
  every owl centre is a centre of this grid (max offset {owl_on_fine.max():.6f} m); on_owl_ctr flags those cells
  {len(fine)} cells intersect the boundary; about {frame_ac / fine_lat.cell_area_acres:.0f} on the {frame_ac:,} ac threshold frame

Vegetation fields on both grids, from the threshold analysis rasters (RRK 2023 CWHR type, 30 m):
  frame_ac, frame_frac        acres and share of the cell in the assessed frame (the seven WHRTYPEs of report Table 1)
  jp_ac, smc_ac, rf_ac        acres of Jeffrey pine, Sierran mixed conifer, red fir (TRPA threshold types)
  jp_pct, smc_pct, rf_pct     shares of the frame area in the cell; sum to 100 where frame_ac > 0
  trpa_type, type_pct         dominant TRPA type and its share
  whr_type, whr_pct, lifeform dominant CWHR WHRTYPE over all non urban land in the cell, its share, its CWHR lifeform
  other_ac                    non urban land in the cell outside the frame
  sc_early, sc_midop, sc_midcl, sc_lateop, sc_latecl
                              shares of the frame area in the five seral stage and canopy classes (VP9)
  Full cell by WHRTYPE table: TahoeBasin_Hex_whrtype_by_cell_{STAMP}.csv; crosswalk: whrtype_crosswalk_{STAMP}.csv

Boundary: {TC['sources']['boundary']}
"""
(O / f"TahoeBasin_Hex_handoff_{STAMP}.txt").write_text(handoff, encoding="utf-8")
print(handoff)'''),
])
