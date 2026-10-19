"""Generate notebooks/00_sample_design_template.ipynb. Run: python scripts/build_sample_design_template.py

Edit this builder, regenerate, never hand-edit the .ipynb (repo convention). Execute with:
    python -m jupyter nbconvert --to notebook --execute --inplace notebooks/00_sample_design_template.ipynb
With run.synthetic: true it runs anywhere (no arcpy, no F:, no R). With run.synthetic: false it
needs the arcgispro-py3 interpreter, F: mounted, and Rscript on run.rscript.

Paths inside the notebook use forward slashes on purpose: arcpy accepts them and it keeps
this builder free of doubled backslashes.
"""
import nbformat as nbf
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NB = ROOT / "notebooks"
NB.mkdir(exist_ok=True)

HEADER = '''import sys, os, time, json, shutil, subprocess, warnings
from pathlib import Path
warnings.filterwarnings("ignore", message="Mean of empty slice")
os.chdir(Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd())
sys.path.insert(0, str(Path.cwd()))
import numpy as np, pandas as pd, geopandas as gpd
from src.io import load_config, get_logger
from src import strata, qa, covariates, sample_size, tessellation as T
from src import design_template as dt
from src.layers import resolve_source, arcpy_available, is_arcgis_path

cfg = load_config()
log = get_logger("00_sample_design_template")
SYN, FREEZE = bool(cfg["run"]["synthetic"]), bool(cfg["run"]["freeze"])
WCRS = cfg["crs"]["working"]
AC = dt.M2_PER_ACRE
STAMP = pd.Timestamp.today().strftime("%Y%m%d")
TYPES = list(cfg["forest_types"]["population_acres"])
P = (Path.cwd() / cfg["paths"]["processed"]).resolve(); P.mkdir(parents=True, exist_ok=True)
O = (Path.cwd() / cfg["paths"]["outputs"]).resolve(); O.mkdir(exist_ok=True)
log.info(f"Project: {cfg['project']['name']} | synthetic={SYN} | freeze={FREEZE} | strata.source={cfg['strata']['source']}")

WORK = None
if not SYN:
    _t = time.time()
    import arcpy                                          # well over a minute in arcgispro-py3
    arcpy.CheckOutExtension("Spatial")
    WORK = (P / "design_template_work.gdb").as_posix()    # scratch only; nothing is ever written through an .sde connection
    if not arcpy.Exists(WORK):
        arcpy.management.CreateFileGDB(str(P), Path(WORK).name)
    arcpy.env.workspace = WORK
    arcpy.env.overwriteOutput = True
    log.info(f"arcpy {arcpy.GetInstallInfo()['Version']} imported in {time.time() - _t:.0f} s; workspace {WORK}")
else:
    arcpy = None
    log.info("synthetic run: arcpy not imported, F: not touched; the toy Basin stands in for every source")

reader = dt.SourceReader(cfg, log=log, synthetic=SYN, scratch_gdb=WORK)'''


def nb(name, cells):
    n = nbf.v4.new_notebook()
    n["cells"] = [nbf.v4.new_markdown_cell(c[1]) if c[0] == "md" else nbf.v4.new_code_cell(c[1]) for c in cells]
    n["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3 (arcgispro-py3)", "language": "python"}
    nbf.write(n, NB / f"{name}.ipynb")
    print("wrote", name)


nb("00_sample_design_template", [

# ------------------------------------------------------------------ title
("md", """# 00 Sample design template

The one place to start. This notebook runs the whole sample design for TRPA's forest health plot network, top to bottom, from the sources the threshold analysis used: `F:\\GIS\\DB_CONNECT\\Vector.sde` (read only), `Raster.sde`, and the threshold project geodatabase. Every number comes from `config.yaml`; every method comes from `src/`. Sections 0 to 7 each open with what the section does, what is already decided, what Andy decides here, and which module does the work.

**What the network is for.** Two adopted standards say what share of the Basin's 115,396 acres of conifer forest should look a certain way: VP9, seral stage and canopy cover, 75 percent of each forest type within its desired ranges; VP10, stand density, 50 percent within the TPA and basal area maxima. Today's figures come from a model. The plots measure the forest the way the standards are written, at enough places to make the 2028 evaluation defensible, and train the next imputation.

**Settled (do not reopen here). Oct 19, 2026, Mason and Andy.** Three forest types per report Table 1 (Sierran mixed conifer with lodgepole and white fir, red fir, Jeffrey pine with eastside pine and juniper). The population is the report's 115,396 acre frame; the sampling frame is its public land (Federal, State, Local), cut 30 m back from private parcels and from mapped roads, trails, streams, and structures. No slope cut. The sampling unit is a 3 by 3 block of 30 m pixels with the plot on the centre pixel. One GRTS selection in `spsurvey` (`scripts/grts_select.R`), stratified by forest type, unequal probability within type: 1.5 on the RRK tail cells, 0.5 where slope is over 50 percent. 40 per type at the minimum (120); the full design (150) adds the next 30 SMC sites in GRTS order. Ranked list three times the full target per type; a rejected site is replaced by the next unused rank in its type and never moved. Access class is hike distance to a drivable road (under 0.5, 0.5 to 1.5, over 1.5 miles). No legacy sites. Reporting uses a model-assisted estimator with 2022 LiDAR as the auxiliary. Seed frozen at contract execution.

**Synthetic mode.** With `run.synthetic: true` a toy Basin stands in for every source and the same section code runs without arcpy, F:, or R. Its numbers mean nothing beyond proving the chain. Flip it to `false` on the arcgispro-py3 interpreter with F: mounted."""),

# ------------------------------------------------------------------ 0 setup
("md", """## 0. Setup

Loads `config.yaml`, opens a log under `logs/`, and, on a real run, imports arcpy and points its workspace at a scratch file geodatabase under `data/processed/`. Nothing is ever written through an `.sde` connection. `reader` is the one door to every source: it reads the real layers through `src/layers.py` (arcpy for `.sde` and `.gdb`, rasterio for files, requests for REST) or hands back the toy Basin.

Decided: paths and the read only rule. Andy decides: nothing here. Module: `src/io.py`, `src/design_template.SourceReader`."""),
("code", HEADER),

# ------------------------------------------------------------------ 1 sources
("md", """## 1. Sources

Two things happen here. First, a discovery walk over `Vector.sde` (and the project gdb) lists every feature dataset and class whose name matches `sde.discovery_keywords`, so the `# CONFIRM` placeholders in `config.yaml` can be replaced with real names. Second, a status table of every entry under `sources:` says which form is picked (`rrk`, `lidar`, `sde`, or `file`) and whether it is found. Read the table before going further: a missing frame or strata source stops section 2.

Decided: the sources are SDE and the project gdb, not REST. Andy decides: the real class names for roads, trails, streams, structures, parcels, ownership, state line, treatments, and fire perimeters, pasted into `config.yaml`. Module: `src/design_template.walk_sde`, `source_status`; `src/layers.resolve_source`."""),
("code", '''if not SYN:
    found = dt.walk_sde(cfg["sde"]["vector"], cfg["sde"]["discovery_keywords"])
    print(f"Vector.sde: {len(found)} datasets and classes match the keyword list")
    with pd.option_context("display.max_rows", 500, "display.width", 200):
        print(found.to_string(index=False))
    found.to_csv(O / f"sde_discovery_{STAMP}.csv", index=False)
    with arcpy.EnvManager(workspace=cfg["sde"]["project_gdb"]):
        gdb_rasters = arcpy.ListRasters() or []
    print(f"\\nproject gdb rasters ({len(gdb_rasters)}): {', '.join(sorted(gdb_rasters))}")
else:
    print("synthetic run: the discovery walk needs arcpy and Vector.sde; skipped")'''),
("code", '''status = dt.source_status(cfg)
with pd.option_context("display.max_rows", 200, "display.width", 250, "display.max_colwidth", 110):
    print(status.to_string(index=False))
status.to_csv(O / f"source_status_{STAMP}.csv", index=False)
needed = ["veg_type", "boundary", "urban_boundary", "wilderness", "dem", "roads", "trails", "streams", "structures", "ownership",
          "rrk_seral", "rrk_cover", "rrk_tpa", "rrk_ba", "rrk_density_assessment"]
if cfg["strata"]["source"] == "lidar":
    needed += ["p95_height_30m", "canopy_cover_30m", "stem_density_30m"]
missing = [k for k in needed if not reader.available(k)]
if missing and not SYN:
    raise SystemExit(f"sources missing, fix config.yaml sources: {missing}")
log.info(f"required sources present: {len(needed) - len(missing)} of {len(needed)}" + (f"; missing {missing}" if missing else ""))'''),

# ------------------------------------------------------------------ 2 frame
("md", """## 2. Frame

The population is the threshold report's assessment frame, rebuilt from the same rasters: `veg_type_nonurban` (RRK 2023 CWHR type, already clipped to non urban land use, 30 m California Teale Albers) mapped to the three TRPA types through its attribute table and `tessellation.whr_to_type`, inside the TRPA boundary, minus the Urban Area, minus designated wilderness. Acres by type are checked against report Table 1 (70,909 / 23,037 / 21,450, total 115,396) and the notebook stops if the population is more than `frame.population_tolerance_pct` off.

The sampling frame is then cut from that population with area accounting at every step:

1. **Public land only.** `sources.ownership` (`OWNERSHIP_TYPE`) values in `frame.public_owner_values` (Federal, State, Local). Private and unmapped ground leaves the frame (Sept 29 and Oct 19, 2026).
2. **Private edge.** `frame.private_edge_buffer_m` (30 m) off any private parcel, so a plot footprint stays on public land.
3. **Mapped features.** `frame.edge_buffer_m` (30 m) around roads, trails, streams, and structures, so these rejections happen in the office, not the field.
4. **No slope cut.** Steep ground stays in the population; slopes over 50 percent get a lower inclusion probability in section 4, and unsafe sites are rejected in the field and logged.

Sampling units are 3 by 3 blocks of pixels anchored at the raster origin, kept when the centre pixel is in the population and at least `frame.min_unit_fraction` of the block is; the cuts above are applied at the unit's centre pixel, where the plot goes. `acres` is the population area a unit represents.

**Access class** (Oct 19, 2026) is hike distance from the nearest drivable road (`sources.roads` filtered by `access.drivable_where`) along the cheapest path over the terrain, with each pixel costed at its surface distance (`access.slope_cost`); the lake is impassable. Classes break at `access.breaks_mi` (0.5 and 1.5 miles) and set the unit rate.

Decided: population, public frame, 30 m buffers, no slope cut, access classes. Andy decides: the drivable road definition (`access.drivable_where`), and the `# CONFIRM` source names. Module: `src/design_template` (frame helpers, `hike_distance_m`, `access_class_mi`), `src/strata.block_reduce`."""),
("code", '''veg, TR, RCRS = reader.raster("veg_type")
rat = reader.rat("veg_type")
SHAPE = veg.shape
CELL = float(abs(TR.a))
PXAC = CELL * CELL / AC
W2T = cfg["tessellation"]["whr_to_type"]
type_code = dt.forest_type_array(veg, rat, W2T)
whr = dt.whrtype_array(veg, rat)
log.info(f"frame raster {SHAPE}, {CELL:.0f} m, CRS {RCRS.to_string()}; working CRS {WCRS}")

boundary = reader.layer("boundary")
urban = reader.layer("urban_boundary")
wilderness = reader.layer("wilderness")
in_bdy = dt.rasterize_mask(boundary, TR, SHAPE, RCRS)
m_urban = dt.rasterize_mask(urban, TR, SHAPE, RCRS)
m_wild = dt.rasterize_mask(wilderness, TR, SHAPE, RCRS)
conifer = (type_code > 0) & in_bdy & ~m_urban

def acres_by_type(mask):
    return {t: float((mask & (type_code == c)).sum()) * PXAC for t, c in dt.TYPE_CODE.items()}

report = cfg["forest_types"]["population_acres"]
tol = cfg["frame"]["population_tolerance_pct"]
kept, ok_kept = dt.population_check(acres_by_type(conifer), report, tol)
dropped, ok_dropped = dt.population_check(acres_by_type(conifer & ~m_wild), report, tol)
print("Wilderness KEPT (threshold notebook clause):"); print(kept.to_string(index=False))
print("\\nWilderness REMOVED (report text):"); print(dropped.to_string(index=False))

EXCL_WILD = bool(cfg["frame"]["exclude_wilderness"])
population = conifer & ~m_wild if EXCL_WILD else conifer
pop_tab, pop_ok = (dropped, ok_dropped) if EXCL_WILD else (kept, ok_kept)
log.info(f"frame.exclude_wilderness={EXCL_WILD}: population {pop_tab.iloc[-1]['acres']:,.0f} ac vs report {sum(report.values()):,}")
if not pop_ok:
    raise SystemExit(f"population is {pop_tab.iloc[-1]['diff_pct']}% from report Table 1 (tolerance {tol}%). "
                     "Check the Wilderness setting, the urban clause, and whr_to_type before going on.")'''),
("code", '''# ownership: public frame and the private edge buffer
own = reader.layer("ownership")
OWN_FIELD = reader.option("ownership", "field", "OWNERSHIP_TYPE")
if OWN_FIELD not in own:
    raise SystemExit(f"ownership has no field {OWN_FIELD} (has {list(own.columns)[:10]}); set sources.ownership.field")
PUBLIC = [str(v) for v in cfg["frame"]["public_owner_values"]]
own_type = own[OWN_FIELD].astype(str).str.strip()
log.info("ownership values: " + ", ".join(f"{k} {v:,}" for k, v in own_type.value_counts().items()))
m_public = dt.rasterize_mask(own[own_type.isin(PUBLIC)], TR, SHAPE, RCRS)
private = own[own_type.str.lower() == "private"]
m_private = dt.rasterize_mask(private, TR, SHAPE, RCRS)
m_public &= ~m_private                                     # overlapping parcels: private wins
m_private_buf = dt.rasterize_mask(private, TR, SHAPE, RCRS, buffer_m=cfg["frame"]["private_edge_buffer_m"])

# mapped features: roads, trails, streams, structures
buf = cfg["frame"]["edge_buffer_m"]
edge_layers = {kk: reader.layer(kk) for kk in ["roads", "trails", "streams", "structures"] if reader.available(kk)}
for kk in ["roads", "trails", "streams", "structures"]:
    if kk in edge_layers:
        log.info(f"{kk}: {len(edge_layers[kk]):,} features buffered {buf} m")
    else:
        log.warning(f"{kk}: not available; not buffered (frame is larger than designed)")
m_edge = dt.rasterize_mask(list(edge_layers.values()), TR, SHAPE, RCRS, buffer_m=buf)

# terrain on the strata grid: the 0.7 m SDE bare earth is projected and snapped to the veg raster on a real run
dem, dem_tr, _ = reader.raster_on_grid("dem", template_key="veg_type")
assert dem.shape == SHAPE, f"DEM grid {dem.shape} does not match the frame raster {SHAPE}; check raster_on_grid"
slope_pct, aspect_deg = dt.terrain(dem, CELL)
max_slope = cfg["frame"]["max_slope_pct"]
steep_cut = (np.nan_to_num(slope_pct, nan=0) > max_slope) if max_slope else np.zeros(SHAPE, bool)

# hike distance to a drivable road
roads_drive = reader.layer("roads", where=cfg["access"]["drivable_where"]) if reader.available("roads") else None
m_drive = dt.rasterize_mask(roads_drive, TR, SHAPE, RCRS)
hike_m = dt.hike_distance_m(m_drive, dem, CELL, slope_cost=bool(cfg["access"]["slope_cost"]), log=log)
log.info(f"drivable road pixels: {int(m_drive.sum()):,}; hike distance computed over {np.isfinite(hike_m).sum():,} pixels")

# pixel accounting
acct = [{"step": "population (report frame)", "acres": population.sum() * PXAC}]
px = population.copy()
for label, cut in [("removed: private or unmapped ownership", ~m_public),
                   (f"removed: within {cfg['frame']['private_edge_buffer_m']} m of a private parcel", m_private_buf),
                   (f"removed: within {buf} m of a road, trail, stream, or structure", m_edge),
                   (f"removed: slope over {max_slope} percent", steep_cut)]:
    acct.append({"step": label, "acres": (px & cut).sum() * PXAC})
    px &= ~cut
acct.append({"step": "frame pixels", "acres": px.sum() * PXAC})
print(pd.DataFrame(acct).round(0).to_string(index=False))'''),
("code", '''# sampling units: k x k blocks anchored at the raster origin, plot on the centre pixel
k = int(cfg["frame"]["unit_px"])
units, bi, bj = dt.build_units(population, type_code, k, cfg["frame"]["min_unit_fraction"], TR)
units["whr_type"] = [whr[r * k + k // 2, c * k + k // 2] for r, c in zip(units["unit_row"], units["unit_col"])]
units["elev_m"] = dt.sample_units(dem, population, k, bi, bj, "mean")
units["slope_pct"] = dt.sample_units(slope_pct, population, k, bi, bj, "center")
units["aspect_deg"] = dt.sample_units(aspect_deg, population, k, bi, bj, "center")
units["hike_m"] = dt.sample_units(hike_m, population, k, bi, bj, "center")
for col, m in [("public", m_public), ("near_private", m_private_buf), ("near_edge", m_edge), ("steep_cut", steep_cut)]:
    units[col] = dt.sample_units(m.astype(float), population, k, bi, bj, "center") > 0

# RRK structure at every unit, always: strata in rrk mode, evaluation in both modes
for key, col, how in [("rrk_seral", "rrk_seral", "center"), ("rrk_cover", "rrk_cover_pct", "mean"),
                      ("rrk_tpa", "rrk_tpa", "mean"), ("rrk_ba", "rrk_ba", "mean"), ("rrk_density_assessment", "rrk_density_exceeds", "center")]:
    arr, tr, _ = reader.raster(key, form="rrk")
    assert arr.shape == SHAPE and abs(tr.a - TR.a) < 1e-6 and abs(tr.c - TR.c) < 1e-3 and abs(tr.f - TR.f) < 1e-3, \\
        f"{key} is not on the frame raster grid ({arr.shape} vs {SHAPE}); snap it to veg_type_nonurban first"
    units[col] = dt.sample_units(arr, population, k, bi, bj, how)
if cfg["strata"]["source"] == "lidar":
    for key, col in [("p95_height_30m", "p95_height_m"), ("stem_density_30m", "stem_density"), ("canopy_cover_30m", "canopy_cover_pct")]:
        arr, tr, _ = reader.raster(key, form="lidar")
        assert arr.shape == SHAPE and abs(tr.a - TR.a) < 1e-6, f"{key} is not on the frame grid; lidar mode needs veg_type on the LiDAR grid too"
        units[col] = dt.sample_units(arr, population, k, bi, bj, "mean")

# polygon attributes at the centre pixel: state, owner, management zone, disturbance flags (attributes only)
def category_at_centre(key, field_default):
    if not reader.available(key):
        return np.array([None] * len(units), dtype=object)
    lyr = reader.layer(key)
    field = reader.option(key, "field", field_default)
    if field not in lyr:
        log.warning(f"{key}: field {field} not found (has {list(lyr.columns)[:8]}); set sources.{key}.field")
        return np.array([None] * len(units), dtype=object)
    arr, lut = dt.rasterize_category(lyr, field, TR, SHAPE, RCRS)
    v = dt.sample_units(arr.astype(float), population, k, bi, bj, "center")
    return np.array([lut.get(int(c)) if c > 0 else None for c in np.nan_to_num(v)], dtype=object)
units["state"] = category_at_centre("state_line", cfg["tessellation"]["state_field"])
units["owner"] = category_at_centre("ownership", "OWNERSHIP_TYPE")
units["mgmt_zone"] = category_at_centre("mgmt_zone", "ZONE_NAME")
for key, col in [("fire_severity", "post_fire"), ("treatments_2027_2031", "treatment_2027_2031")]:
    m = dt.rasterize_mask(reader.layer(key), TR, SHAPE, RCRS) if reader.available(key) else np.zeros(SHAPE, bool)
    units[col] = dt.sample_units(m.astype(float), population, k, bi, bj, "center") > 0

units = dt.to_working_crs(units, RCRS, WCRS)
log.info(f"units on the {CELL:.0f} m grid: {len(units):,} blocks of {k}x{k}; centres carried in {RCRS.to_string()} and {WCRS}")'''),
("code", '''# unit level cuts at the centre pixel, with accounting, then the access class
uacct = [{"step": "candidate units (population)", "acres": units["acres"].sum(), "units": len(units)}]
for label, col in [("not public", None), ("within the private edge buffer", "near_private"),
                   ("within the feature buffer", "near_edge"), ("over the slope cut", "steep_cut")]:
    cut = ~units["public"] if col is None else units[col]
    uacct.append({"step": f"removed: centre {label}", "acres": units.loc[cut, "acres"].sum(), "units": int(cut.sum())})
    units = units[~cut]
units = units.copy()
units["access_class"] = dt.access_class_mi(units["hike_m"], cfg["access"]["breaks_mi"])
uacct.append({"step": "frame units", "acres": units["acres"].sum(), "units": len(units)})
uacct = pd.DataFrame(uacct)
pd.concat([pd.DataFrame(acct).assign(level="pixel"), uacct.assign(level="unit")]).to_csv(O / "frame_accounting.csv", index=False)
print(uacct.round(0).to_string(index=False))
print("\\nframe acres by type:"); print(units.groupby("forest_type")["acres"].sum().round().to_string())
print("\\nframe acres by type and owner:"); print(units.pivot_table(index="forest_type", columns="owner", values="acres", aggfunc="sum", fill_value=0).round().to_string())
print("\\naccess class (units):"); print(units.groupby(["forest_type", "access_class"]).size().unstack(fill_value=0).to_string())
units.to_parquet(P / "frame.parquet", index=False)'''),

# ------------------------------------------------------------------ 3 strata
("md", """## 3. Structure classes and balance covariates

Forest type is the only stratum. Structure classes are not strata; they set the tail weights in section 4. In `rrk` mode (the source as of Oct 19, 2026) they sit at the threshold decision points: seral 1, 2, 3 from `seral_stage_nonurban`; density from `stand_density_threshold_assessment`, low at or below the TPA and basal area maxima and high above; cover from `canopy_cover_nonurban` as an attribute. In `lidar` mode they are p95 height at `strata.height_breaks_m` and stem density at `strata.density_breaks`. Classes come from `strata.classify_cells`; no cells are collapsed, because nothing is allocated by cell any more.

Balance covariates, reported in section 6 and not enforced: TPI class from the DEM on the strata grid (`balance.tpi_radius_px`) and basin side east or west of the lake's long axis. spsurvey's `caty_n` only sets expected counts, so with area-proportional targets it is identical to equal probability; GRTS spatial balance does the spreading.

Decided: forest type as the only stratum, RRK classes for the weights. Andy decides: the TPI radius and the lake axis anchor. Module: `src/strata.classify_cells`, `src/covariates`, `src/design_template.strata_config_for_source`, `proxy_columns`."""),
("code", '''frame = pd.read_parquet(P / "frame.parquet")
cfg_s = dt.strata_config_for_source(cfg)
frame = dt.proxy_columns(frame, cfg)
classified = strata.classify_cells(frame, cfg_s)
cells = classified.groupby(["forest_type", "seral_class", "density_class"], as_index=False)["acres"].sum()
cells["share_of_type"] = cells["acres"] / cells.groupby("forest_type")["acres"].transform("sum")
cells.to_csv(O / "structure_classes.csv", index=False)
for col in ["rrk_seral", "rrk_density_exceeds"] if cfg["strata"]["source"] == "rrk" else ["p95_height_m", "stem_density"]:
    nn = int(frame[col].isna().sum())
    if nn:
        log.warning(f"{col}: {nn:,} frame units have no value; their structure class is a default and never a tail cell unless both axes are set")
print(f"strata.source={cfg['strata']['source']}: structure classes by type"); print(cells.round(3).to_string(index=False))

bal = cfg["balance"]
tpi_grid = covariates.tpi(np.where(np.isnan(dem), np.nanmean(dem), dem), int(bal["tpi_radius_px"]))
classified["tpi"] = [tpi_grid[r * k + k // 2, c * k + k // 2] for r, c in zip(classified["unit_row"], classified["unit_col"])]
classified["tpi_class"] = covariates.tpi_class(classified["tpi"].to_numpy(), classified["slope_pct"].fillna(0).to_numpy())
anchor = bal["lake_axis_anchor_xy"]
if anchor is None:
    c = boundary.to_crs(WCRS).union_all().centroid
    anchor = [float(c.x), float(c.y)]
    log.info(f"balance.lake_axis_anchor_xy is null; using the boundary centroid {anchor[0]:.0f}, {anchor[1]:.0f}")
classified["basin_side"] = covariates.basin_side(classified["x"].to_numpy(), classified["y"].to_numpy(), anchor[0], anchor[1], bal["lake_axis_azimuth_deg"])
classified.to_parquet(P / "frame_classified.parquet", index=False)
print("\\nframe acres by type and basin side:"); print(pd.crosstab(classified["forest_type"], classified["basin_side"], values=classified["acres"], aggfunc="sum").round().to_string())'''),

# ------------------------------------------------------------------ 4 targets and weights
("md", """## 4. Targets, weights, and precision

**Targets** (`allocation.n_by_type`): 40 per type at the RFP minimum (120), 70 SMC plus 40 JP and 40 RF at the full design (150). One selection serves both: the full level is the minimum plus the first 30 SMC sites after it in GRTS order. The ranked list per type is `allocation.backup_multiple` (3) times the full target.

**Weights** (`weights:`): every unit's relative inclusion probability within its type is 1.5 on the tail cells (late seral at or above the density maxima, late seral below them, early seral above them) times 0.5 where the centre slope is over 50 percent. Weights change efficiency, never bias: inclusion probability is n x mult / sum(mult) within type and every site carries it. The disturbance weights of the Sept 5 design were dropped Oct 19, 2026.

**Precision.** The 2027 evaluation uses a model-assisted estimator with LiDAR as the auxiliary (Oct 19, 2026), so the table shows design-based and model-assisted 95 percent CI half widths per type at p = 0.5, with the Kish design effect of the weights and relative efficiency 1.5 and 2.0 (the planning range in the Sept 19 sample size review). The design-based column is what the plots alone support.

Decided: targets, list depth, multipliers, estimator. Andy decides: nothing here unless a check below fails. Module: `src/design_template.inclusion_multiplier`, `selection_targets`, `design_ip`, `expected_counts`; `src/sample_size`."""),
("code", '''frame = dt.inclusion_multiplier(pd.read_parquet(P / "frame_classified.parquet"), cfg)
targets = dt.selection_targets(cfg)
N_MIN = targets.set_index("forest_type")["n_min"].to_dict()
N_FULL = targets.set_index("forest_type")["n_full"].to_dict()
print(targets.to_string(index=False))

wtab = frame.groupby(["forest_type", "is_tail", "is_steep"]).agg(units=("unit_id", "size"), acres=("acres", "sum"), mult=("mult", "first"))
wtab["acre_share"] = wtab["acres"] / wtab.groupby(level=0)["acres"].transform("sum")
wtab["exp_n_min"] = dt.expected_counts(frame, N_MIN, ["forest_type", "is_tail", "is_steep"])
wtab["exp_n_full"] = dt.expected_counts(frame, N_FULL, ["forest_type", "is_tail", "is_steep"])
wtab.round(3).to_csv(O / "weights_by_type.csv")
print("\\nunits, area share, and expected plots by tail and steep flags:"); print(wtab.round(2).to_string())

rows = []
for lvl, nmap in (("min", N_MIN), ("full", N_FULL)):
    for t in TYPES:
        sub = frame[frame["forest_type"] == t]
        deff = float((sub["mult"].mean()) * (1.0 / sub["mult"]).mean())       # expected Kish deff of 1/ip weights
        n = nmap[t]
        rows.append({"level": lvl, "forest_type": t, "n": n, "kish_deff": round(deff, 3),
                     "ci_design_pts": round(100 * sample_size.ci_halfwidth(int(round(n / deff)), 0.5), 1),
                     "ci_model_re1.5_pts": round(100 * sample_size.ci_halfwidth(int(round(1.5 * n / deff)), 0.5), 1),
                     "ci_model_re2.0_pts": round(100 * sample_size.ci_halfwidth(int(round(2.0 * n / deff)), 0.5), 1),
                     "exp_nevada": round(float(dt.design_ip(frame, nmap)[(frame["forest_type"] == t) & (frame["state"] == "NV")].sum()), 1)})
prec = pd.DataFrame(rows)
prec.to_csv(O / "precision_by_type.csv", index=False)
print("\\n95% CI half width at p = 0.5 by type (design-based, then model-assisted at RE 1.5 and 2.0), and expected Nevada plots:")
print(prec.to_string(index=False))'''),

# ------------------------------------------------------------------ 5 selection
("md", """## 5. Selection

Writes `frame_points.gpkg` and `selection_targets.csv` and calls `scripts/grts_select.R` through `run.rscript` with `draw.seed` and `draw.min_distance_m`: `spsurvey::grts()` stratified by forest type, `seltype = "proportional"` on `mult`, `n_base` the minimum per type, `n_over` the rest of the ranked list. When Rscript is missing or fails, the Python GRTS in `src/strata.py` makes the same design for iteration and the log says so; it is never the frozen selection.

Levels and order: within each type, GRTS ranks 1 to 40 are the minimum, the next 30 SMC are the full design, and everything after is the backup list in order. A rejected site (fixed reject reasons, logged, TRPA concurrence) is replaced by the next unused rank in the same type; a design coordinate is never moved. Inclusion probabilities and design weights are written for both levels (`ip_min`, `wgt_min`, `ip_full`, `wgt_full`).

`run.freeze` guards the seed: the freeze happens at contract execution (Oct 19, 2026). A frozen run refuses to proceed if `draw.seed` differs from the one recorded in `outputs/frozen_seed.json`, and records it the first time.

Decided: everything here. Andy decides: nothing on the method. Module: `scripts/grts_select.R`; `src/strata.grts_draw` (fallback); `src/design_template.write_selection_inputs`, `run_rscript`, `python_selection`, `normalise_spsurvey_sites`, `assign_levels`."""),
("code", '''seed_file = O / "frozen_seed.json"
if FREEZE:
    if seed_file.exists():
        rec = json.loads(seed_file.read_text())
        if int(rec["seed"]) != int(cfg["draw"]["seed"]):
            raise SystemExit(f"run.freeze is true and draw.seed {cfg['draw']['seed']} differs from the frozen seed {rec['seed']} ({rec['date']}). Restart review or restore the seed.")
    else:
        seed_file.write_text(json.dumps({"seed": int(cfg["draw"]["seed"]), "date": STAMP, "strata_source": cfg["strata"]["source"]}, indent=2))
        log.info(f"FROZEN: seed {cfg['draw']['seed']} recorded in {seed_file.name}")

paths = dt.write_selection_inputs(frame, targets, cfg, P, log)
r_out = O / "grts_select.gpkg"
if r_out.exists():
    r_out.unlink()
res = dt.run_rscript(cfg, Path("scripts/grts_select.R"), [cfg["draw"]["seed"], cfg["draw"]["min_distance_m"]], Path.cwd(), log)
if res is not None and res.returncode == 0 and r_out.exists():
    sel = dt.normalise_spsurvey_sites(gpd.read_file(r_out), frame)
    SELECTION = "spsurvey::grts (scripts/grts_select.R)"
else:
    log.warning("spsurvey selection not available; the Python GRTS makes the same design. This is NOT the frozen selection.")
    sel = dt.python_selection(frame, targets, cfg, log)
    sel = sel[[c for c in ["unit_id", "stratum", "status", "grts_rank", "wgt", "ip"]]].merge(frame, on="unit_id", how="left")
    SELECTION = "python strata.grts_draw (iteration only)"

sel = dt.assign_levels(sel, targets)
sel["ip_min"] = sel["unit_id"].map(pd.Series(dt.design_ip(frame, N_MIN).values, index=frame["unit_id"].values))
sel["ip_full"] = sel["unit_id"].map(pd.Series(dt.design_ip(frame, N_FULL).values, index=frame["unit_id"].values))
sel["wgt_min"] = np.where(sel["level"] == "min", 1 / sel["ip_min"], np.nan)
sel["wgt_full"] = np.where(sel["level"].isin(["min", "full"]), 1 / sel["ip_full"], np.nan)
rng = np.random.default_rng(int(cfg["draw"]["seed"]) + 1)
at_min = sel.index[sel["level"] == "min"]
sel["remeasure_flag"] = False
sel.loc[rng.choice(at_min, int(round(len(at_min) * cfg["draw"]["remeasure_share"])), replace=False), "remeasure_flag"] = True
sel.to_parquet(P / "selected.parquet", index=False)
log.info(f"selection by {SELECTION}: {len(sel)} sites")
print(sel.groupby(["forest_type", "level"]).size().unstack(fill_value=0)[["min", "full", "backup"]].to_string())'''),

# ------------------------------------------------------------------ 6 evaluate
("md", """## 6. Evaluate

Before anything freezes, for the minimum level and the full level: spatial balance (spsurvey's `sp_balance` when the R script ran, and a quadrant chi-square against the frame where 1 is simple random sampling); realized against expected counts under the design (sum of inclusion probabilities) by type and basin side, type and TPI class, type and tail flag, type and steep flag, and type and state; VP9 and VP10 class coverage of the minimum sites against the RRK rasters; access class and owner counts; design-weighted covariate means against the frame; and the QA report from `src/qa.py`.

A realized count far from its expectation is a property of one random selection, not an error. If a gap matters (for example, no Nevada red fir), the remedy is a different seed chosen before the freeze for a stated reason and recorded, never moving sites.

Decided: what is checked. Andy decides: whether any flag warrants a recorded reseed before the freeze. Module: `src/qa.py`; `src/design_template.spatial_balance`, `expected_counts`, `vp9_class`, `vp10_class`, `coverage_table`."""),
("code", '''sel = pd.read_parquet(P / "selected.parquet")
LV = {"min": sel[sel["level"] == "min"], "full": sel[sel["level"].isin(["min", "full"])]}
NMAP = {"min": N_MIN, "full": N_FULL}

bal_file = O / "grts_select_balance.csv"
if bal_file.exists() and SELECTION.startswith("spsurvey"):
    print("spsurvey sp_balance (Pielou evenness of Voronoi polygons; lower is better balanced), base sites:"); print(pd.read_csv(bal_file).to_string(index=False))
sb = {lvl: {t: dt.spatial_balance(s.loc[s["forest_type"] == t, ["x", "y"]].to_numpy(float), frame.loc[frame["forest_type"] == t, ["x", "y"]].to_numpy(float), nq=3)
            for t in TYPES} for lvl, s in LV.items()}
print("\\nquadrant chi-square per df by type (1 is simple random sampling):", json.dumps({l: {t: v["chi2_per_df"] for t, v in d.items()} for l, d in sb.items()}))

checks_rx = []
for lvl, s in LV.items():
    for by in ["basin_side", "tpi_class", "is_tail", "is_steep", "state", "access_class"]:
        exp = dt.expected_counts(frame, NMAP[lvl], ["forest_type", by])
        real = s.groupby(["forest_type", by]).size().rename("n_realized")
        tab = exp.to_frame().join(real, how="outer").fillna(0)
        tab["diff"] = tab["n_realized"] - tab["n_expected"]
        checks_rx.append(tab.reset_index().rename(columns={by: "category"}).assign(level=lvl, covariate=by))
rx = pd.concat(checks_rx, ignore_index=True)
rx["n_expected"] = rx["n_expected"].round(1)
rx.to_csv(O / "eval_realized_vs_expected.csv", index=False)
show = rx[(rx["level"] == "min") & rx["covariate"].isin(["basin_side", "is_tail", "is_steep", "state"])]
print("\\nminimum level, realized vs expected:"); print(show[["covariate", "forest_type", "category", "n_expected", "n_realized", "diff"]].to_string(index=False))
big = rx[(rx["diff"].abs() > 2 * np.sqrt(rx["n_expected"].clip(lower=1)))]
print("\\ncategories more than 2 sqrt(expected) off:"); print(big.to_string(index=False) if len(big) else "none")'''),
("code", '''cut = cfg["threshold"]["cover_open_closed_pct"]
for df in (frame, sel):
    df["vp9_class"] = dt.vp9_class(df["rrk_seral"], df["rrk_cover_pct"], df["forest_type"], cut)
    df["vp10_class"] = dt.vp10_class(df["rrk_seral"], df["rrk_density_exceeds"])
smin = sel[sel["level"] == "min"]
vp9 = dt.coverage_table(frame[frame["vp9_class"] != ""], smin[smin["vp9_class"] != ""], "vp9_class")
vp10 = dt.coverage_table(frame[frame["vp10_class"] != ""], smin[smin["vp10_class"] != ""], "vp10_class")
vp9.to_csv(O / "eval_vp9_crosstab.csv"); vp10.to_csv(O / "eval_vp10_crosstab.csv")
empty_vp9, empty_vp10 = int((vp9["sample_n"] == 0).sum()), int((vp10["sample_n"] == 0).sum())
print("VP9 classes at the minimum level (frame share vs sites):"); print(vp9.to_string())
print("\\nVP10 classes at the minimum level:"); print(vp10.to_string())

covs = [c for c in ["elev_m", "slope_pct", "rrk_cover_pct", "rrk_tpa", "rrk_ba", "hike_m"] if c in frame]
rows = []
for c in covs:
    for lvl, s in LV.items():
        w = s["wgt_min"] if lvl == "min" else s["wgt_full"]
        for t in TYPES:
            m, fm = s["forest_type"] == t, frame["forest_type"] == t
            ok = m & s[c].notna()
            ht = float(np.average(s.loc[ok, c], weights=w[ok])) if ok.any() else np.nan
            rows.append({"covariate": c, "level": lvl, "forest_type": t, "frame_mean": round(frame.loc[fm, c].mean(), 2),
                         "weighted_sample_mean": round(ht, 2), "smd": round((ht - frame.loc[fm, c].mean()) / frame.loc[fm, c].std(), 3)})
cb = pd.DataFrame(rows); cb.to_csv(O / "eval_covariate_balance.csv", index=False)
flag = cb[cb["smd"].abs() > 0.25]
print("\\ndesign-weighted covariate means off the frame by more than 0.25 SD:"); print(flag.to_string(index=False) if len(flag) else "none")'''),
("code", '''checks = {
    "selection": {"method": SELECTION, "seed": int(cfg["draw"]["seed"]), "strata_source": cfg["strata"]["source"], "synthetic": SYN},
    "nulls": qa.check_nulls(LV["full"], ["plot_id", "x", "y", "forest_type", "access_class", "owner", "level", "ip_full"]),
    "duplicate_plot_ids": qa.check_duplicates(sel, ["plot_id"]),
    "duplicate_units": qa.check_duplicates(sel, ["unit_id"]),
    "sites_closer_than_min_distance": qa.check_min_distance(sel, cfg["draw"]["min_distance_m"]),
    "count_min": qa.check_row_count(LV["min"], expected_min=cfg["allocation"]["levels"]["min"], expected_max=cfg["allocation"]["levels"]["min"]),
    "count_full": qa.check_row_count(LV["full"], expected_min=cfg["allocation"]["levels"]["full"], expected_max=cfg["allocation"]["levels"]["full"]),
    "list_depth": {t: int((sel["forest_type"] == t).sum()) for t in TYPES},
    "forest_type_domain": qa.check_value_domain(sel, "forest_type", TYPES),
    "owner_domain": qa.check_value_domain(sel, "owner", cfg["frame"]["public_owner_values"]),
    "population_vs_report": {"acres": float(pop_tab.iloc[-1]["acres"]), "report": sum(report.values()), "diff_pct": float(pop_tab.iloc[-1]["diff_pct"]), "wilderness_excluded": EXCL_WILD},
    "frame_acres": float(frame["acres"].sum()),
    "empty_vp9_classes_at_min": {"count": empty_vp9},
    "empty_vp10_classes_at_min": {"count": empty_vp10},
    "realized_vs_expected_flags": {"count": int(len(big))},
    "covariate_flags": {"count": int(len(flag))},
}
for kk, v in checks.items():
    log.info(f"QA {kk}: {v}")
pd.json_normalize(checks).T.to_csv(O / "qa_report.csv", header=False)
log.info("evaluation complete; read outputs/qa_report.csv before the freeze")'''),

# ------------------------------------------------------------------ 7 export
("md", """## 7. Export and RFP Appendix A

Two GeoPackages in EPSG:26910: `plots_design_<date>.gpkg`, the public layer with `run.publish_strip_fields` removed, and `plots_design_<date>_internal.gpkg` with everything. Every site carries its level (min, full, backup), installation order or backup order, inclusion probabilities and weights at both levels, and the 400 ha owl cell and 133 ha sample design cell keys from the `06_tessellation` lattice (the `hex_source` field says when a placeholder lattice was used). The installation order and backup list go out as CSVs.

**Appendix A** (`appendix_a_<date>.md` and CSVs): plots by forest type and access class, and by forest type and owner, at 120 and 150, the list depth per type, and a frame map (`appendix_a_frame_map_<date>.png`). Coordinates are not in Appendix A; they are furnished at contract execution.

**Backup rule (Oct 19, 2026).** A site is rejected only for a logged reason on the fixed list (unsafe terrain, no legal access, not forest on the ground, feature the frame buffers missed), with TRPA's written concurrence. The replacement is the next unused rank in the same forest type. A design coordinate is never moved.

Module: `src/design_template.appendix_a_tables`, `hex_keys`; `src/tessellation`."""),
("code", '''owl_key, fine_key, hex_src = dt.hex_keys(sel["x"], sel["y"], cfg, O / "tessellation_lattice_parameters.csv", log)
sel["owl_cell_key"], sel["fine_cell_key"], sel["hex_source"] = owl_key, fine_key, hex_src
sel["selection"] = SELECTION
sel["design_crs"] = WCRS
sel["strata_source"] = cfg["strata"]["source"]
sel["design_date"] = STAMP

drop_internal = ["tpi", "mult", "is_tail", "is_steep", "rrk_tpa", "rrk_ba", "rrk_density_exceeds", "rrk_seral", "rrk_cover_pct"]
public_cols = [c for c in sel.columns if c not in set(cfg["run"]["publish_strip_fields"]) | set(drop_internal)]
internal = gpd.GeoDataFrame(sel, geometry=gpd.points_from_xy(sel["x"], sel["y"]), crs=WCRS)
for c in internal.columns:
    if internal[c].dtype == object and c != "geometry":
        internal[c] = internal[c].astype(str).where(internal[c].notna(), None)
internal.to_file(O / f"plots_design_{STAMP}_internal.gpkg", driver="GPKG")
internal[public_cols + ["geometry"]].to_file(O / f"plots_design_{STAMP}.gpkg", driver="GPKG")

order_cols = [c for c in ["install_order", "plot_id", "forest_type", "level", "grts_rank", "access_class", "owner", "state", "basin_side",
                          "ip_min", "ip_full", "owl_cell_key", "fine_cell_key", "x", "y"] if c in sel]
prim = sel[sel["level"].isin(["min", "full"])].sort_values("install_order").copy()
prim["install_order"] = prim["install_order"].astype(int)
prim[order_cols].to_csv(O / f"installation_order_{STAMP}.csv", index=False)
back = sel[sel["level"] == "backup"].sort_values(["forest_type", "backup_order"])
back[[c for c in ["plot_id", "forest_type", "grts_rank", "backup_order", "access_class", "owner", "state", "owl_cell_key", "fine_cell_key", "x", "y"] if c in back]].to_csv(O / f"backup_list_{STAMP}.csv", index=False)
log.info(f"wrote plots_design_{STAMP}.gpkg ({len(prim)} sites at min and full, {len(back)} backups), _internal, installation_order, backup_list; hex keys from {hex_src}")'''),
("code", '''# Appendix A: counts, list depth, and the frame map
A = dt.appendix_a_tables(sel)
for name, tab in A.items():
    tab.to_csv(O / f"appendix_a_{name}_{STAMP}.csv")
lines = [f"# Appendix A. Plot Allocation and Access Classes", "",
         f"Design of {STAMP}. Selection: {SELECTION}. Strata source: {cfg['strata']['source']}. Frame: {frame['acres'].sum():,.0f} acres of public conifer forest outside urban areas and designated wilderness.",
         "", "Access classes are hike distance from the nearest drivable road: class 1 under 0.5 mile, class 2 from 0.5 to 1.5 miles, class 3 over 1.5 miles.", ""]
for lvl, n in (("min", cfg["allocation"]["levels"]["min"]), ("full", cfg["allocation"]["levels"]["full"])):
    lines += [f"## {n} plots, by forest type and access class", "", dt.to_markdown(A[f"access_{lvl}"]), "",
              f"## {n} plots, by forest type and owner", "", dt.to_markdown(A[f"owner_{lvl}"]), ""]
lines += ["## Backup sites available per forest type", "", dt.to_markdown(A["list_depth"]), "",
          "Plot coordinates are furnished at contract execution."]
(O / f"appendix_a_{STAMP}.md").write_text("\\n".join(lines))

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(7, 9))
boundary.to_crs(WCRS).boundary.plot(ax=ax, color="#444444", linewidth=0.8)
colors = {"SMC": "#2E7D32", "JP": "#C9A227", "RF": "#8E3B46"}
for t in TYPES:
    f = frame[frame["forest_type"] == t]
    ax.scatter(f["x"], f["y"], s=0.15, color=colors.get(t, "grey"), label=f"{t} ({f['acres'].sum():,.0f} ac)", rasterized=True)
ax.set_axis_off(); ax.set_aspect("equal")
ax.legend(loc="lower left", markerscale=25, frameon=False, title="Sampling frame, public land")
ax.set_title("Forest structure plot network: sampling frame")
fig.savefig(O / f"appendix_a_frame_map_{STAMP}.png", dpi=200, bbox_inches="tight"); plt.close(fig)
print("\\n".join(lines))
if FREEZE:
    log.info(f"FROZEN design: seed {cfg['draw']['seed']}, strata.source {cfg['strata']['source']}, selection {SELECTION}, {STAMP}. Nothing after this changes without restarting review.")'''),
])
