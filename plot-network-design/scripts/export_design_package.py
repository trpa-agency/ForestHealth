"""Package a sample design run with every input it read: one GeoPackage and one file geodatabase.

Run after notebooks/00_sample_design_template on real layers (run.synthetic: false), in the
arcgispro-py3-plotly env with F: mounted and PROJ_LIB unset (PostgreSQL's PROJ_LIB breaks rasterio):

    python scripts/export_design_package.py --stamp 20261116 --dest "F:/GIS/PROJECTS/ForestHealth_Intiative/ThresholdUpdate"

Writes <dest>/PlotNetwork_SampleDesign_<stamp>.gpkg and .gdb, each holding:
  plots_design_<stamp>       the published selection (min, full, backups), EPSG:26910
  frame_units                centre points of every sampling unit left in the frame, EPSG:26910
  input_<key>                every vector source, as read (definition queries applied), EPSG:26910
  raster_<key>               every raster source on the frame grid (30 m, California Teale Albers, EPSG:3310)
  input_veg_type_rat         the veg_type attribute table (WHRTYPE crosswalk)
Sources resolve exactly as the notebook resolves them, through config.yaml and SourceReader.
Nothing is written through an .sde connection. Refuses to overwrite an existing package.
"""
import argparse, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import geopandas as gpd
import pyogrio
import rasterio
from src.io import load_config, get_logger
from src import design_template as dt

VECTORS = ["boundary", "urban_boundary", "wilderness", "ownership", "roads", "trails", "streams",
           "structures", "mgmt_zone", "state_line", "fire_severity", "treatments_2027_2031"]
RASTERS = ["veg_type", "rrk_seral", "rrk_cover", "rrk_tpa", "rrk_ba", "rrk_density_assessment",
           "rrk_seral_classification"]
NODATA = -9999.0


def read_with_retry(reader, key, log, tries=4, wait_s=45, form=None):
    """reader.layer with retries: the Vector.sde connection drops for minutes at a time."""
    for i in range(1, tries + 1):
        try:
            if reader.available(key, form):
                return reader.layer(key, form=form)
            log.warning(f"{key}: not available (try {i} of {tries})")
        except Exception as e:                               # noqa: BLE001 - connection errors vary
            log.warning(f"{key}: read failed (try {i} of {tries}): {e}")
        if i < tries:
            time.sleep(wait_s)
    return None


def append(a, cfg, log):
    """Add vector layers to an existing package (gpkg and gdb) without touching what is there."""
    import arcpy
    arcpy.env.overwriteOutput = False
    wcrs = cfg["crs"]["working"]
    dest = Path(a.dest)
    base = f"PlotNetwork_SampleDesign_{a.stamp}"
    gpkg, gdb = dest / f"{base}.gpkg", dest / f"{base}.gdb"
    if not gpkg.exists() or not arcpy.Exists(str(gdb)):
        raise SystemExit(f"{gpkg} and {gdb} must both exist for --append")
    # empty layers (a REST read that returned nothing) are treated as missing
    for n, _ in pyogrio.list_layers(gpkg):
        if pyogrio.read_info(gpkg, layer=n).get("features", 1) == 0:
            arcpy.management.Delete(f"{gpkg}/main.{n}")
            log.warning(f"{n}: empty in the gpkg, removed so it can be re-read")
    have = {n for n, _ in pyogrio.list_layers(gpkg)}
    reader = dt.SourceReader(cfg, log=log, synthetic=False)
    for key in a.append:
        name = f"input_{key}"
        if name in have:
            log.info(f"{name}: already in the package, left alone")
            continue
        g = read_with_retry(reader, key, log)
        if key == "urban_boundary" and (g is None or len(g) == 0):
            log.warning("urban_boundary: REST layer returned no features; reading the SDE land use classes instead")
            g = read_with_retry(reader, key, log, form="sde")
        if g is None or len(g) == 0:
            log.error(f"{name}: nothing read, not written")
            continue
        g = g.set_crs(wcrs) if g.crs is None else g.to_crs(wcrs)
        g = g[g.geometry.notna() & ~g.geometry.is_empty]
        g.to_file(gpkg, layer=name, driver="GPKG")
        log.info(f"{name}: {len(g):,} features added to the gpkg")
    sync_gdb(gpkg, gdb, log)


def sync_gdb(gpkg: Path, gdb: Path, log):
    """Copy every gpkg vector layer, table, and raster the gdb does not have yet."""
    import arcpy
    with arcpy.EnvManager(workspace=str(gdb)):
        in_gdb = {n.lower() for n in (arcpy.ListFeatureClasses() or []) + (arcpy.ListTables() or []) + (arcpy.ListRasters() or [])}
    for n, geom in pyogrio.list_layers(gpkg):
        if n.lower() in in_gdb:
            continue
        if geom is None:
            arcpy.conversion.ExportTable(f"{gpkg}/main.{n}", f"{gdb}/{n}")
        else:
            arcpy.conversion.ExportFeatures(f"{gpkg}/main.{n}", f"{gdb}/{n}")
        log.info(f"gdb: {n}")
    for sub in _gpkg_raster_tables(gpkg):
        if sub.lower() in in_gdb:
            continue
        with rasterio.open(gpkg, table=sub) as r:
            data, tr, crs = r.read(1).astype("float32"), r.transform, r.crs
        ll = arcpy.Point(tr.c, tr.f + tr.e * data.shape[0])
        ras = arcpy.NumPyArrayToRaster(data, ll, abs(tr.a), abs(tr.e), NODATA)
        out = f"{gdb}/{sub}"
        ras.save(out)
        epsg = crs.to_epsg()
        sr = arcpy.SpatialReference(int(epsg)) if epsg else arcpy.SpatialReference()
        if not epsg:
            sr.loadFromString(crs.to_wkt("WKT1_ESRI"))
        arcpy.management.DefineProjection(out, sr)
        log.info(f"gdb: {sub} {data.shape}")


def _gpkg_raster_tables(gpkg: Path):
    import sqlite3
    with sqlite3.connect(str(gpkg)) as c:
        return [r[0] for r in c.execute("SELECT table_name FROM gpkg_contents WHERE data_type IN ('tiles', '2d-gridded-coverage')")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stamp", required=True, help="date stamp of the notebook run, e.g. 20261116")
    ap.add_argument("--dest", required=True)
    ap.add_argument("--append", nargs="+", metavar="KEY", help="add these vector sources to an existing package")
    a = ap.parse_args()
    if a.append:
        cfg = load_config()
        append(a, cfg, get_logger("export_design_package_append"))
        return

    cfg = load_config()
    if cfg["run"]["synthetic"]:
        raise SystemExit("run.synthetic is true; this packages real runs only")
    log = get_logger("export_design_package")
    dest = Path(a.dest)
    base = f"PlotNetwork_SampleDesign_{a.stamp}"
    gpkg, gdb = dest / f"{base}.gpkg", dest / f"{base}.gdb"
    if gpkg.exists() or gdb.exists():
        raise SystemExit(f"{gpkg} or {gdb} already exists; not overwriting")

    t = time.time()
    import arcpy
    arcpy.CheckOutExtension("Spatial")
    arcpy.env.overwriteOutput = True
    P = (ROOT / cfg["paths"]["processed"]).resolve()
    work = (P / "design_template_work.gdb").as_posix()
    log.info(f"arcpy imported in {time.time() - t:.0f} s")
    reader = dt.SourceReader(cfg, log=log, synthetic=False, scratch_gdb=work)
    wcrs = cfg["crs"]["working"]

    # ---- vectors -> gpkg
    plots_src = ROOT / cfg["paths"]["outputs"] / f"plots_design_{a.stamp}.gpkg"
    plots = gpd.read_file(plots_src)
    plots.to_file(gpkg, layer=f"plots_design_{a.stamp}", driver="GPKG")
    frame = pd.read_parquet(P / "frame.parquet")
    frame = dt.units_as_points(frame, wcrs)
    for c in frame.columns:                                  # object columns of mixed type upset the GPKG writer
        if frame[c].dtype == object and c != "geometry":
            frame[c] = frame[c].astype("string")
    frame.to_file(gpkg, layer="frame_units", driver="GPKG")
    vec_layers = [f"plots_design_{a.stamp}", "frame_units"]
    for key in VECTORS:
        if not reader.available(key):
            log.warning(f"{key}: not available, skipped")
            continue
        g = reader.layer(key)
        if g.crs is None or g.crs.to_string() != wcrs:
            g = g.set_crs(wcrs) if g.crs is None else g.to_crs(wcrs)
        g = g[g.geometry.notna() & ~g.geometry.is_empty]
        g.to_file(gpkg, layer=f"input_{key}", driver="GPKG")
        vec_layers.append(f"input_{key}")
        log.info(f"input_{key}: {len(g):,} features")

    rat = reader.rat("veg_type")
    pyogrio.write_dataframe(rat, gpkg, layer="input_veg_type_rat")

    # ---- rasters on the frame grid -> gpkg (Float32 gridded coverage) and gdb
    grids = {}
    for key in RASTERS:
        arr, tr, crs = reader.raster(key, form="rrk") if key != "veg_type" else reader.raster(key)
        grids[f"raster_{key}"] = (arr, tr, crs)
    dem, dtr, dcrs = reader.raster_on_grid("dem", template_key="veg_type")
    grids["raster_dem_30m"] = (dem, dtr, dcrs)
    for name, (arr, tr, crs) in grids.items():
        data = np.where(np.isfinite(arr), arr, NODATA).astype("float32")
        with rasterio.open(gpkg, "w", driver="GPKG", height=data.shape[0], width=data.shape[1], count=1,
                           dtype="float32", crs=crs, transform=tr, nodata=NODATA,
                           RASTER_TABLE=name, APPEND_SUBDATASET="YES", TILE_FORMAT="TIFF") as dst:
            dst.write(data, 1)
        log.info(f"{name}: {data.shape}, {abs(tr.a):.0f} m, {crs.to_string()}")

    # ---- gdb: same content through arcpy
    arcpy.management.CreateFileGDB(str(dest), gdb.name)
    for lyr in vec_layers:
        arcpy.conversion.ExportFeatures(f"{gpkg}/main.{lyr}", f"{gdb}/{lyr}")
    arcpy.conversion.ExportTable(f"{gpkg}/main.input_veg_type_rat", f"{gdb}/input_veg_type_rat")
    for name, (arr, tr, crs) in grids.items():
        data = np.where(np.isfinite(arr), arr, NODATA).astype("float32")
        ll = arcpy.Point(tr.c, tr.f + tr.e * data.shape[0])
        r = arcpy.NumPyArrayToRaster(data, ll, abs(tr.a), abs(tr.e), NODATA)
        out = f"{gdb}/{name}"
        r.save(out)
        epsg = crs.to_epsg()
        if epsg:
            sr = arcpy.SpatialReference(int(epsg))
        else:
            sr = arcpy.SpatialReference()
            sr.loadFromString(crs.to_wkt("WKT1_ESRI"))
        arcpy.management.DefineProjection(out, sr)
    log.info(f"wrote {gpkg} and {gdb}: {len(vec_layers)} vector layers, {len(grids)} rasters, 1 table "
             f"in {time.time() - t:.0f} s")


if __name__ == "__main__":
    main()
