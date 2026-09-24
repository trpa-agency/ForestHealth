"""Generate the four notebooks. Run once: python scripts/build_notebooks.py"""
import nbformat as nbf
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NB = ROOT / "notebooks"
NB.mkdir(exist_ok=True)

HEADER = '''import sys, os
print(sys.executable)
from pathlib import Path
os.chdir(Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd())
sys.path.insert(0, str(Path.cwd()))
import numpy as np, pandas as pd
from src.io import load_config, get_logger
from src import strata, qa
cfg = load_config()
log = get_logger("{name}")
log.info(f"Project: {{cfg['project']['name']}} | synthetic={{cfg['run']['synthetic']}} | freeze={{cfg['run']['freeze']}}")
P = Path(cfg["paths"]["processed"]); O = Path(cfg["paths"]["outputs"]); P.mkdir(parents=True, exist_ok=True); O.mkdir(exist_ok=True)'''


def nb(name, cells):
    n = nbf.v4.new_notebook()
    n["cells"] = [nbf.v4.new_markdown_cell(c[1]) if c[0] == "md" else nbf.v4.new_code_cell(c[1]) for c in cells]
    n["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3 (arcgispro-py3)", "language": "python"}
    nbf.write(n, NB / f"{name}.ipynb")
    print("wrote", name)


# ---------------------------------------------------------------- 01 frame
nb("01_frame", [
("md", """# 01 Frame

Build the sampling frame: the threshold report's 115,396 acre assessment population (CWHR conifer outside urban and wilderness), minus edge buffers, steep ground, and existing plot footprints, with area accounting at every step.

**The sampling unit is a block of `frame.unit_px` by `frame.unit_px` LiDAR pixels** (3 by 3, 90 m, 0.81 ha), decided Sept. 23, 2026. A 30 m pixel is smaller than the primary plot, so it cannot be the unit; the block is the 3 by 3 window the imputation model trains on. The plot sits on the block's centre pixel. A block is in the frame when its centre pixel is in the population and at least `frame.min_unit_fraction` of its pixels are. LiDAR metrics are block means over the population pixels. Output is one row per candidate unit with forest type, LiDAR metrics, slope, road distance, state, ownership, and disturbance flags; `acres` is the population area the unit represents and `unit_acres` the block area.

With `run.synthetic: true` a toy Basin is generated instead so the chain can be exercised. Replace the synthetic block with the real-layer block once layers are in `data/raw/`."""),
("code", HEADER.format(name="01_frame")),
("md", "## Real layers (runs when `run.synthetic` is false)\n\nRasterize forest type to the LiDAR grid, reduce it and the 2022 LiDAR metric rasters to blocks, sample the DEM and distance to roads at each block centre, then apply exclusions. Every step logs acres removed."),
("code", '''if not cfg["run"]["synthetic"]:
    import geopandas as gpd, rasterio
    from rasterio import features
    from shapely.geometry import Point
    from src.layers import read_layer, read_raster        # local file or TRPA REST service, per config.yaml
    src = cfg["sources"]; wcrs = cfg["crs"]["working"]; g = cfg["crs"]["lidar_grid_m"]

    # forest type from CWHR, mapped verbatim from threshold report Table 1
    veg = read_layer(src["cwhr_veg"], cfg, log=log)
    type_map = {c: t for t, cs in cfg["forest_types"].items() if isinstance(cs, list) for c in cs}
    veg["forest_type"] = veg["WHR_TYPE"].map(type_map)          # adjust field name to the layer
    veg = veg[veg["forest_type"].notna()]
    log.info(f"CWHR conifer polygons: {len(veg):,}; acres by type:\\n{veg.assign(ac=veg.area/4046.86).groupby('forest_type')['ac'].sum().round()}")

    # exclusions
    urban = read_layer(src["urban_boundary"], cfg, log=log)
    wild = read_layer(src["wilderness"], cfg, log=log)
    pop = veg.overlay(pd.concat([urban[["geometry"]], wild[["geometry"]]]), how="difference")
    log.info(f"Population after urban + wilderness removal: {pop.area.sum()/4046.86:,.0f} ac (report: 115,396)")

    # sampling units: k x k blocks of LiDAR pixels anchored at the raster origin, plot on the centre pixel
    k = cfg["frame"]["unit_px"]; B = k * g
    bbox = tuple(pop.total_bounds)
    p95, transform, rcrs = read_raster(src["p95_height_30m"], cfg, bbox=bbox, log=log)
    assert abs(transform.a - g) < 1e-6, f"expected {g} m grid, got {transform.a}"
    shape = p95.shape
    ft_raster = features.rasterize(((geom, i + 1) for i, geom in enumerate(pop.geometry)), out_shape=shape, transform=transform, fill=0)
    inpop = ft_raster > 0
    frac = strata.block_reduce(inpop.astype(float), k, "mean")            # share of the block in the population
    centre = strata.block_reduce(ft_raster.astype(float), k, "center")     # polygon index at the centre pixel
    keep = (centre > 0) & (frac >= cfg["frame"]["min_unit_fraction"])
    bi, bj = np.nonzero(keep)
    rows, cols = bi * k + k // 2, bj * k + k // 2
    xs, ys = rasterio.transform.xy(transform, rows, cols)
    frame = pd.DataFrame({"x": xs, "y": ys, "unit_id": bi * keep.shape[1] + bj, "unit_row": bi, "unit_col": bj})
    frame["forest_type"] = pop["forest_type"].values[centre[bi, bj].astype(int) - 1]
    frame["unit_frac_in_frame"] = frac[bi, bj]
    frame["unit_acres"] = B * B / 4046.86
    frame["acres"] = frame["unit_frac_in_frame"] * frame["unit_acres"]   # population acres the unit represents
    log.info(f"Units: {len(frame):,} blocks of {k}x{k} pixels ({B} m); population pixels {int(inpop.sum()):,}, "
             f"in kept units {int((frac[bi, bj] * k * k).sum()):,}")

    def sample(source, name, how="mean"):
        """Block mean over population pixels when the raster shares the LiDAR grid; else the centre-point value."""
        arr, tr, _ = read_raster(source, cfg, bbox=bbox, log=log)
        if arr.shape == shape and abs(tr.a - g) < 1e-6:
            red = strata.block_reduce(np.where(inpop, arr, np.nan), k, how)
            frame[name] = red[bi, bj]
        else:
            rr, cc = rasterio.transform.rowcol(tr, frame["x"].values, frame["y"].values)
            rr = np.clip(rr, 0, arr.shape[0] - 1); cc = np.clip(cc, 0, arr.shape[1] - 1)
            frame[name] = arr[rr, cc]
    sample(src["p95_height_30m"], "p95_height_m")
    sample(src["canopy_cover_30m"], "canopy_cover_pct")
    sample(src["stem_density_30m"], "stem_density")
    if Path(str(src.get("solid_frac_30m", ""))).exists() or str(src.get("solid_frac_30m", "")).startswith("http"):
        sample(src["solid_frac_30m"], "solid_frac")
    sample(src["dem"], "elev_m")   # 1 m DTM: centre-point value; slope/aspect from a pre-computed raster the same way

    pts = gpd.GeoDataFrame(frame, geometry=[Point(xy) for xy in zip(frame.x, frame.y)], crs=wcrs)
    edges = pd.concat([read_layer(src[k], cfg, log=log)[["geometry"]] for k in ["roads", "trails", "streams", "structures"]])
    buf = edges.buffer(cfg["frame"]["edge_buffer_m"]).union_all()
    pts["near_edge"] = pts.intersects(buf)
    roads = read_layer(src["roads"], cfg, log=log)
    pts["dist_road_m"] = pts.geometry.apply(lambda p: roads.distance(p).min())
    pts = pts.sjoin(read_layer(src["state_line"], cfg)[["STATE", "geometry"]], how="left").rename(columns={"STATE": "state"}).drop(columns="index_right")
    pts = pts.sjoin(read_layer(src["ownership"], cfg)[["OWNER", "geometry"]], how="left").rename(columns={"OWNER": "owner"}).drop(columns="index_right")
    fire = read_layer(src["fire_severity"], cfg, log=log); trt = read_layer(src["treatments_2027_2031"], cfg, log=log)
    pts["post_fire"] = pts.intersects(fire.union_all()); pts["treatment_2027_2031"] = pts.intersects(trt.union_all())
    # slope placeholder if no slope raster: compute from DEM outside this notebook and sample here
    if "slope_pct" not in pts: pts["slope_pct"] = np.nan
    frame = pd.DataFrame(pts.drop(columns="geometry"))
    frame = frame[~frame["near_edge"]]'''),
("md", "## Synthetic Basin (runs when `run.synthetic` is true)"),
("code", '''if cfg["run"]["synthetic"]:
    frame = strata.make_synthetic_frame(cfg)
    log.info("Synthetic frame generated")
frame.head()'''),
("md", "## Exclusions and area accounting"),
("code", '''acct = [{"step": "population", "acres": frame["acres"].sum(), "units": len(frame)}]
steep = frame["slope_pct"] > cfg["frame"]["max_slope_pct"]
acct.append({"step": f"removed slope > {cfg['frame']['max_slope_pct']}%", "acres": frame.loc[steep, "acres"].sum(), "units": int(steep.sum())})
frame = frame[~steep].copy()
if cfg["frame"]["max_access_distance_m"]:
    far = frame["dist_road_m"] > cfg["frame"]["max_access_distance_m"]
    acct.append({"step": "removed beyond access distance", "acres": frame.loc[far, "acres"].sum(), "units": int(far.sum())})
    frame = frame[~far].copy()
if "solid_frac" in frame and cfg["frame"].get("max_solid_fraction"):
    solid = (frame["solid_frac"] > cfg["frame"]["max_solid_fraction"]) & (frame["canopy_cover_pct"] > cfg["threshold"]["cover_sparse_pct"])
    acct.append({"step": f"removed solid-surface units (single-return fraction > {cfg['frame']['max_solid_fraction']})", "acres": frame.loc[solid, "acres"].sum(), "units": int(solid.sum())})
    frame = frame[~solid].copy()
acct.append({"step": "frame", "acres": frame["acres"].sum(), "units": len(frame)})
acct = pd.DataFrame(acct)
for r in acct.itertuples(): log.info(f"{r.step}: {r.acres:,.0f} ac, {r.units:,} units")
acct.to_csv(O / "frame_accounting.csv", index=False)
frame["access_class"] = strata.access_class(frame["dist_road_m"], frame["slope_pct"], cfg)
frame.to_parquet(P / "frame.parquet", index=False)
log.info(f"Wrote frame: {len(frame):,} units of {cfg['frame']['unit_px']}x{cfg['frame']['unit_px']} pixels, {frame['acres'].sum():,.0f} ac")
frame.groupby("forest_type")["acres"].sum().round()'''),
])

# ---------------------------------------------------------------- 02 strata
nb("02_strata", [
("md", """# 02 Strata

Classify every sampling unit into forest type x seral proxy x density proxy (cover as an attribute), collapse cells below the minimum area, and produce the cell table with acres. Includes the height-to-QMD calibration step that turns the placeholder breaks in `config.yaml` into defensible ones once plots with both QMD and LiDAR height are available."""),
("code", HEADER.format(name="02_strata")),
("code", '''frame = pd.read_parquet(P / "frame.parquet")
log.info(f"Frame: {len(frame):,} units")'''),
("md", """## Calibrate height breaks to the QMD definition (when calibration plots exist)

The standard defines seral by QMD (5 and 25 in). We need the p95 height that corresponds to those QMDs per forest type. Fit on Lake Tahoe West validation plots (and FIA if coordinates are available), then write the breaks back to `config.yaml` by hand and record the fit in `docs/DESIGN_SUMMARY.md`. Skipped on the synthetic run."""),
("code", '''calib = cfg["sources"]["ltw_plots"]
if (str(calib).startswith("http") or Path(calib).exists()) and not cfg["run"]["synthetic"]:
    import geopandas as gpd, rasterio
    from src.layers import read_layer, read_raster
    plots = read_layer(cfg["sources"]["ltw_plots"], cfg, log=log)
    arr, tr, _ = read_raster(cfg["sources"]["p95_height_30m"], cfg, bbox=tuple(plots.total_bounds), log=log)
    rr, cc = rasterio.transform.rowcol(tr, plots.geometry.x.values, plots.geometry.y.values)
    plots["p95_height_m"] = arr[np.clip(rr, 0, arr.shape[0]-1), np.clip(cc, 0, arr.shape[1]-1)]
    for ftype, sub in plots.groupby("forest_type"):
        # monotone fit: height as a function of QMD, then invert at 5 and 25 in
        coef = np.polyfit(sub["qmd_in"], sub["p95_height_m"], 1)
        breaks = [float(np.polyval(coef, q)) for q in cfg["threshold"]["qmd_breaks_in"]]
        log.info(f"{ftype}: n={len(sub)} height = {coef[0]:.2f}*QMD + {coef[1]:.2f}; breaks at QMD 5/25 in -> {breaks[0]:.1f} / {breaks[1]:.1f} m")
else:
    log.info("No calibration plots yet; using placeholder height breaks from config.yaml")'''),
("md", "## Classify and collapse"),
("code", '''classified = strata.classify_cells(frame, cfg)
cells_raw = classified.groupby(["cell_id", "forest_type", "seral_class", "density_class"], as_index=False)["acres"].sum()
log.info(f"Raw cells: {len(cells_raw)}; below {cfg['strata']['min_cell_acres']} ac: {(cells_raw['acres'] < cfg['strata']['min_cell_acres']).sum()}")
classified, collapse_log = strata.collapse_small_cells(classified, cfg, log)
collapse_log.to_csv(O / "cell_collapse_log.csv", index=False)
cells = classified.groupby(["cell_id", "forest_type", "seral_class", "density_class"], as_index=False)["acres"].sum().sort_values("cell_id")
cells["share_of_type"] = cells["acres"] / cells.groupby("forest_type")["acres"].transform("sum")
cells.to_csv(O / "cells.csv", index=False)
classified.to_parquet(P / "frame_classified.parquet", index=False)
log.info(f"Populated cells after collapse: {len(cells)}")
cells'''),
("md", "## Cover distribution by cell (attribute check; decides whether cover becomes a fourth axis)"),
("code", '''xt = pd.crosstab(classified["cell_id"], classified["cover_class"], values=classified["acres"], aggfunc="sum").fillna(0).round()
xt.to_csv(O / "cells_by_cover.csv")
xt'''),
])

# ---------------------------------------------------------------- 03 allocate + draw
nb("03_allocate_draw", [
("md", """# 03 Allocate and draw

Nested allocation at `min`, `option`, and `full` under Candidate A (proportional) and Candidate B (tail-boosted floor), then a GRTS draw with oversample, legacy sites, installation order, disturbance and remeasurement flags. The Python GRTS here is for iteration; the frozen design is drawn with `scripts/grts_draw.R` (spsurvey) from the files this notebook exports."""),
("code", HEADER.format(name="03_allocate_draw")),
("code", '''frame = pd.read_parquet(P / "frame_classified.parquet")
cells = pd.read_csv(O / "cells.csv")'''),
("md", "## Allocation at three nested levels"),
("code", '''alloc = pd.concat([strata.allocate(cells, cfg, lvl) for lvl in cfg["allocation"]["levels"]], ignore_index=True)
alloc = strata.apply_nevada_floor(alloc, frame.groupby(["cell_id", "state"], as_index=False)["acres"].sum(), cfg)
alloc.to_csv(O / "allocation_table.csv", index=False)
for lvl in cfg["allocation"]["levels"]:
    a = alloc[alloc["level"] == lvl]
    log.info(f"{lvl}: n={a['n_B'].sum()}  cells at floor (B)={int((a['n_B'] == cfg['allocation']['floor_per_cell'][lvl]).sum())}  cells with 0-1 plots (A)={int((a['n_A'] <= 1).sum())}")
alloc.pivot_table(index=["forest_type", "seral_class", "density_class"], columns="level", values=["n_A", "n_B"]).astype(int)'''),
("md", "## Inclusion weights: disturbance targeting and tail boost\n\nDisturbance is not a stratum. It enters as an inclusion weight that lifts post-fire and scheduled-treatment units so the expected share of the sample lands near `allocation.disturbance_shares`. Representativeness weighting is switched on with `draw.weight_by_representativeness` once Shengli's raster is in hand."),
("code", '''ds = cfg["allocation"]["disturbance_shares"]
w = pd.Series(1.0, index=frame.index)
for flag, share in [("post_fire", ds["post_fire"]), ("treatment_2027_2031", ds["treatment"])]:
    p_frame = frame[flag].mean()
    if 0 < p_frame < share:
        w[frame[flag]] *= share / p_frame          # lift so expected share ~ target
    log.info(f"{flag}: frame share {p_frame:.3f}, target {share:.2f}")
if cfg["draw"]["weight_by_representativeness"] and "representativeness" in frame:
    w *= 1 + (frame["representativeness"].rank(pct=True))   # later-imputed (less represented) units up-weighted
frame["inclusion_weight"] = w'''),
("md", "## Legacy sites\n\nExisting permanently marked plots that fall inside the frame are attached to the sampling unit that contains them and passed to the draw as legacy sites. They count toward the cell's allocation, the new plots balance around them, and the minimum-distance rule keeps new plots off them."),
("code", '''legacy_mask = pd.Series(False, index=frame.index)
if not cfg["run"]["synthetic"]:
    import geopandas as gpd
    from shapely.geometry import Point
    pts = gpd.GeoDataFrame(frame, geometry=[Point(xy) for xy in zip(frame.x, frame.y)], crs=cfg["crs"]["working"])
    from src.layers import read_layer
    for key in cfg["draw"]["legacy_sources"]:
        src_k = cfg["sources"][key]
        if not (str(src_k).startswith("http") or Path(src_k).exists()): log.info(f"{key}: not available yet"); continue
        leg = read_layer(src_k, cfg, log=log)
        half_diag = cfg["crs"]["lidar_grid_m"] * cfg["frame"]["unit_px"] * 0.7072   # any point in the block is this close to its centre
        near = gpd.sjoin_nearest(leg[["geometry"]], pts[["unit_id", "geometry"]], max_distance=half_diag)
        legacy_mask[frame["unit_id"].isin(near["unit_id"])] = True
        log.info(f"{key}: {len(leg)} sites, {near['unit_id'].nunique()} inside the frame")
else:
    legacy_mask[frame.sample(12, random_state=1).index] = True   # pretend a dozen LTW plots exist
frame["legacy"] = legacy_mask
log.info(f"Legacy sites in frame: {int(legacy_mask.sum())}")'''),
("md", "## GRTS draw (Python, for iteration)\n\nOne unit per site, and no two sites closer than `draw.min_distance_m` (two macroplot radii), legacy sites included, so no plot footprints overlap. The frozen draw applies the same rule through spsurvey's `mindis`."),
("code", '''full = alloc[alloc["level"] == "full"].set_index("cell_id")["n_B"].to_dict()
sel = strata.grts_draw(frame, full, frame["inclusion_weight"], seed=cfg["draw"]["seed"],
                       oversample_factor=cfg["draw"]["oversample_factor"], legacy_mask=frame["legacy"],
                       min_distance_m=cfg["draw"]["min_distance_m"])
sel = strata.installation_order(sel, cfg, alloc).merge(
    sel[sel["status"] == "backup"], how="outer")
sel["status"] = sel["status"].fillna("backup")
rng = np.random.default_rng(cfg["draw"]["seed"] + 1)
prim = sel["status"].isin(["primary", "legacy"]) & (sel["level"] == "min")
sel["remeasure_flag"] = False
sel.loc[sel[prim].sample(frac=cfg["draw"]["remeasure_share"], random_state=int(rng.integers(1e6))).index, "remeasure_flag"] = True
sel["plot_id"] = "FH-" + sel["cell_id"] + "-" + sel.groupby("cell_id").cumcount().add(1).astype(str).str.zfill(3)
log.info(f"Selected: {len(sel)} rows; primary {int((sel.status=='primary').sum())}, legacy {int((sel.status=='legacy').sum())}, backup {int((sel.status=='backup').sum())}")
sel.groupby(["level", "status"]).size().unstack(fill_value=0)'''),
("md", "## Export for the frozen spsurvey draw and for review"),
("code", '''alloc[alloc["level"] == "full"][["cell_id", "n_B"]].to_csv(P / "allocation_full.csv", index=False)
try:
    import geopandas as gpd
    from shapely.geometry import Point
    keep_cols = [c for c in ["unit_id", "cell_id", "forest_type", "inclusion_weight", "balance_caty", "x", "y"] if c in frame]
    gpd.GeoDataFrame(frame[keep_cols],
                     geometry=[Point(xy) for xy in zip(frame.x, frame.y)], crs=cfg["crs"]["working"]).to_file(P / "frame_points.gpkg", driver="GPKG")
    gpd.GeoDataFrame(frame.loc[frame["legacy"], [c for c in ["unit_id", "cell_id", "forest_type"] if c in frame]],
                     geometry=[Point(xy) for xy in zip(frame.loc[frame.legacy].x, frame.loc[frame.legacy].y)], crs=cfg["crs"]["working"]).to_file(P / "legacy_sites.gpkg", driver="GPKG")
    stamp = pd.Timestamp.today().strftime("%Y%m%d")
    internal = gpd.GeoDataFrame(sel, geometry=[Point(xy) for xy in zip(sel.x, sel.y)], crs=cfg["crs"]["working"])
    internal.to_file(O / f"plots_design_{stamp}_internal.gpkg", driver="GPKG")
    internal.drop(columns=cfg["run"]["publish_strip_fields"]).to_file(O / f"plots_design_{stamp}.gpkg", driver="GPKG")
    log.info(f"Wrote plots_design_{stamp}.gpkg (published) and _internal.gpkg (with remeasure flag)")
except Exception as e:
    log.warning(f"GeoPackage export skipped: {e}")
sel.to_parquet(P / "selected.parquet", index=False)
sel.to_csv(O / "plot_list_review.csv", index=False)
if cfg["run"]["freeze"]:
    log.info(f"FROZEN design: seed={cfg['draw']['seed']} levels={cfg['allocation']['levels']}")'''),
])

# ---------------------------------------------------------------- 04 evaluate
nb("04_evaluate", [
("md", """# 04 Evaluate before freeze

Class coverage under both candidates, threshold class cross-tab against RRK (evaluation only), covariate balance sample versus frame, representativeness, practicality counts by owner and access class, and the QA report. Shengli's model test happens outside this notebook; its result and the one design iteration are recorded in `docs/DESIGN_SUMMARY.md`."""),
("code", HEADER.format(name="04_evaluate")),
("code", '''frame = pd.read_parquet(P / "frame_classified.parquet")
sel = pd.read_parquet(P / "selected.parquet")
alloc = pd.read_csv(O / "allocation_table.csv")
prim = sel[sel["status"].isin(["primary", "legacy"])]'''),
("md", "## 1. Class coverage by level"),
("code", '''cov = prim.groupby(["level", "cell_id"]).size().unstack("level", fill_value=0)
cov["cum_min"] = cov.get("min", 0); cov["cum_option"] = cov["cum_min"] + cov.get("option", 0); cov["cum_full"] = cov["cum_option"] + cov.get("full", 0)
floor = cfg["allocation"]["floor_per_cell"]
cov["below_floor_min"] = cov["cum_min"] < floor["min"]
log.info(f"Cells below floor at min: {int(cov['below_floor_min'].sum())} of {len(cov)}")
cov.to_csv(O / "eval_class_coverage.csv"); cov'''),
("md", "## 2. Threshold class check (RRK, evaluation only)\n\nEvery VP9 and VP10 class, attaining and non-attaining, must be represented per forest type at the minimum quantity. On the synthetic run the RRK classes are stubbed from the proxies."),
("code", '''if "rrk_seral" not in prim:
    prim = prim.assign(rrk_seral=prim["seral_class"], rrk_cover=prim["cover_class"],
                       rrk_density_attain=np.where(prim["density_class"] == "high", "exceeds", "meets"))
xt1 = pd.crosstab([prim["forest_type"], prim["rrk_seral"]], prim["rrk_cover"])
xt2 = pd.crosstab([prim["forest_type"], prim["rrk_seral"]], prim["rrk_density_attain"])
missing = int((xt2 == 0).sum().sum())
log.info(f"Empty forest type x seral x density-attainment combinations: {missing}")
xt1.to_csv(O / "eval_vp9_crosstab.csv"); xt2.to_csv(O / "eval_vp10_crosstab.csv"); xt2'''),
("md", "## 3. Covariate balance: sample vs frame (KS test and standardized mean difference)"),
("code", '''from scipy import stats
covs = [c for c in ["elev_m", "slope_pct", "aspect_deg", "p95_height_m", "canopy_cover_pct", "stem_density", "dist_road_m"] if c in frame]
rows = []
for c in covs:
    for ftype in ["ALL"] + sorted(frame["forest_type"].unique()):
        f = frame if ftype == "ALL" else frame[frame["forest_type"] == ftype]
        s = prim if ftype == "ALL" else prim[prim["forest_type"] == ftype]
        if len(s) < 5: continue
        ks = stats.ks_2samp(s[c].dropna(), f[c].dropna())
        smd = (s[c].mean() - f[c].mean()) / f[c].std()
        rows.append({"covariate": c, "forest_type": ftype, "n_sample": len(s), "ks_stat": round(ks.statistic, 3), "ks_p": round(ks.pvalue, 3), "smd": round(smd, 3)})
bal = pd.DataFrame(rows)
flag = bal[(bal["smd"].abs() > 0.25) & (bal["ks_p"] < 0.05)]
log.info(f"Covariate imbalance flags (|SMD|>0.25 and KS p<0.05): {len(flag)}")
bal.to_csv(O / "eval_covariate_balance.csv", index=False); flag'''),
("md", "## 4. Representativeness (when Shengli's raster is available)"),
("code", '''if "representativeness" in frame:
    q = np.quantile(frame["representativeness"], [0.25, 0.5, 0.75]); qs = np.quantile(prim["representativeness"], [0.25, 0.5, 0.75])
    log.info(f"Representativeness quartiles frame {q} vs sample {qs}")
else:
    log.info("Representativeness raster not available; skipped")'''),
("md", "## 5. Practicality: owner, state, access class, disturbance flags, crew days"),
("code", '''prac = prim.groupby(["level", "access_class"]).size().unstack(fill_value=0)
own = prim.groupby(["level", "owner"]).size().unstack(fill_value=0)
st = prim.groupby(["level", "state"]).size().unstack(fill_value=0)
dist = prim.groupby("level")[["post_fire", "treatment_2027_2031", "remeasure_flag"]].sum()
days_per_class = {1: 0.5, 2: 0.75, 3: 1.0, 4: 2.0}       # crew-days per plot, placeholder until unit costs arrive
crew_days = (prac * pd.Series(days_per_class)).sum(axis=1)
log.info(f"Crew-days by level (cumulative): {crew_days.cumsum().round(1).to_dict()}")
pd.concat({"access": prac, "owner": own, "state": st, "flags": dist}, axis=1).to_csv(O / "eval_practicality.csv")
pd.concat({"access": prac, "state": st, "flags": dist}, axis=1)'''),
("md", "## 6. QA report"),
("code", '''checks = {
    "nulls": qa.check_nulls(prim, ["plot_id", "cell_id", "x", "y", "forest_type", "access_class"]),
    "duplicate_plot_ids": qa.check_duplicates(sel, ["plot_id"]),
    "duplicate_units": qa.check_duplicates(sel, ["unit_id"]),
    "sites_closer_than_min_distance": qa.check_min_distance(prim, cfg["draw"]["min_distance_m"]),
    "row_count_primary": qa.check_row_count(prim, expected_min=cfg["allocation"]["levels"]["min"], expected_max=cfg["allocation"]["levels"]["full"] + 50),
    "forest_type_domain": qa.check_value_domain(prim, "forest_type", list(cfg["forest_types"]["population_acres"])),
    "cells_below_floor_min": {"count": int(cov["below_floor_min"].sum())},
    "empty_threshold_classes": {"count": missing},
    "covariate_flags": {"count": len(flag)},
}
for k, v in checks.items(): log.info(f"QA {k}: {v}")
pd.json_normalize(checks).T.to_csv(O / "qa_report.csv", header=False)
log.info("Evaluation complete; review outputs/ before freeze")'''),
])
