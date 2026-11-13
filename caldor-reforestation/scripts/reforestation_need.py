"""Where might we need to replant trees in the Tahoe Basin part of the Caldor Fire?

Three questions, answered on a 30 m grid inside the TRPA boundary portion of the 2021
Caldor Fire perimeter:

  1. Where do high vegetation burn severity and high soil burn severity line up?
  2. How big are the high vegetation severity patches?
  3. Which high severity pixels are farther than 150 m from a surviving seed source?

Run from caldor-reforestation/ in the arcgispro-py3 environment:

    python scripts/reforestation_need.py --check        verify inputs, write nothing
    python scripts/reforestation_need.py                full run (inputs, analysis, web)
    python scripts/reforestation_need.py --stage web    rebuild CSV, GeoJSON, summary only

Outputs (committed):
    outputs/*.csv            summary tables
    web/data/*.geojson       polygons the app draws (WGS84, generalized)
    web/data/summary.json    every number the app shows
Outputs (gitignored):
    data/caldor_reforestation.gdb   every raster and polygon product
    logs/reforestation_need_<date>.log

Method notes are in CLAUDE.md next to this folder's config.yaml.
"""

import argparse
import datetime as dt
import json
import logging
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
M2_PER_ACRE = 4046.8564224

log = logging.getLogger("reforestation")


# ----------------------------------------------------------------------------- setup
def load_config() -> dict:
    with open(ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_logging(log_dir: Path, stamp: str) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"reforestation_need_{stamp}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(path, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
    )
    return path


def resolve(p: str) -> str:
    """Repo-relative paths become absolute; F: paths pass through."""
    path = Path(p)
    return str(path if path.is_absolute() else ROOT / path)


def import_arcpy(gdb: str):
    t0 = dt.datetime.now()
    log.info("importing arcpy")
    import arcpy  # noqa: WPS433

    arcpy.CheckOutExtension("Spatial")
    gdb_path = Path(gdb)
    if not arcpy.Exists(str(gdb_path)):
        gdb_path.parent.mkdir(parents=True, exist_ok=True)
        arcpy.management.CreateFileGDB(str(gdb_path.parent), gdb_path.name)
        log.info("created %s", gdb_path)
    arcpy.env.workspace = str(gdb_path)
    arcpy.env.overwriteOutput = True
    arcpy.env.scratchWorkspace = str(gdb_path)
    log.info("arcpy %s ready in %.0f s, workspace %s", arcpy.GetInstallInfo()["Version"], (dt.datetime.now() - t0).total_seconds(), gdb_path)
    return arcpy


# ----------------------------------------------------------------------------- REST
def rest_query(url: str, params: dict) -> dict:
    data = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(urllib.request.Request(f"{url}/query", data=data), timeout=300) as resp:
        body = json.loads(resp.read())
    if "error" in body:
        raise RuntimeError(f"{url}: {body['error']}")
    return body


def fetch_layer(url: str, out_json: Path, out_fields: str = "*", where: str = "1=1", geometry=None, in_sr: int = None, out_sr: int = 26910) -> Path:
    """Page through a feature layer and save one Esri JSON FeatureSet for JSONToFeatures."""
    out_json.parent.mkdir(parents=True, exist_ok=True)
    if out_json.exists():
        log.info("reusing %s (delete it to refetch)", out_json.name)
        return out_json
    features, offset, page = [], 0, 2000
    meta = None
    while True:
        params = {"where": where, "outFields": out_fields, "returnGeometry": "true", "outSR": out_sr, "f": "json",
                  "resultOffset": offset, "resultRecordCount": page}
        if geometry is not None:
            params.update({"geometry": json.dumps(geometry), "geometryType": "esriGeometryEnvelope",
                           "inSR": in_sr or out_sr, "spatialRel": "esriSpatialRelIntersects"})
        body = rest_query(url, params)
        if meta is None:
            meta = {k: body[k] for k in ("displayFieldName", "fieldAliases", "geometryType", "spatialReference", "fields") if k in body}
        got = body.get("features", [])
        features.extend(got)
        log.info("  %s: %d features (offset %d)", url.rsplit("/", 2)[-2] + "/" + url.rsplit("/", 1)[-1], len(got), offset)
        if len(got) < page or not body.get("exceededTransferLimit", len(got) == page):
            break
        offset += page
    meta["features"] = features
    out_json.write_text(json.dumps(meta), encoding="utf-8")
    log.info("saved %d features to %s", len(features), out_json.name)
    return out_json


# ----------------------------------------------------------------------------- helpers
def rat_rows(arcpy, raster: str, fields):
    with arcpy.da.SearchCursor(raster, fields) as cur:
        return [list(r) for r in cur]


def raster_table(arcpy, raster: str) -> list:
    """Attribute table of an integer raster as [[Value, Count], ...], building it if needed."""
    try:
        arcpy.management.BuildRasterAttributeTable(raster, "Overwrite")
    except Exception:  # noqa: BLE001  some rasters already carry one and refuse a rebuild
        pass
    return rat_rows(arcpy, raster, ["Value", "Count"])


def acres(count: int, cell: float) -> float:
    return count * cell * cell / M2_PER_ACRE


def tabulate_area(arcpy, zone_raster: str, zone_field: str, class_raster: str, class_field: str, out_table: str, cell: float) -> dict:
    """TabulateArea as {zone: {class: acres}}. Class field names come back as VALUE_<n>."""
    arcpy.sa.TabulateArea(zone_raster, zone_field, class_raster, class_field, out_table, cell)
    fields = [f.name for f in arcpy.ListFields(out_table) if f.name.startswith("VALUE_") or f.name.upper() == zone_field.upper()]
    zone_col = [f for f in fields if f.upper() == zone_field.upper()][0]
    out = {}
    with arcpy.da.SearchCursor(out_table, fields) as cur:
        for row in cur:
            rec = dict(zip(fields, row))
            z = rec.pop(zone_col)
            out[z] = {int(k.split("_")[1]): v / M2_PER_ACRE for k, v in rec.items()}
    return out


def write_csv(path: Path, header: list, rows: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(",".join(header) + "\n")
        for r in rows:
            f.write(",".join("" if v is None else (f"{v:.2f}" if isinstance(v, float) else str(v)) for v in r) + "\n")
    log.info("wrote %s (%d rows)", path.relative_to(ROOT), len(rows))


def band_label(edges: list, idx: int, unit: str) -> str:
    """Band 1..len(edges)+1 to '0-50 m', '50-100 m', ..., '>300 m'."""
    if idx <= 0:
        return "none"
    if idx > len(edges):
        return f">{edges[-1]:g} {unit}"
    lo = 0 if idx == 1 else edges[idx - 2]
    return f"{lo:g}-{edges[idx - 1]:g} {unit}"


# ----------------------------------------------------------------------------- stage: inputs
def stage_inputs(arcpy, cfg: dict, paths: dict):
    sa = arcpy.sa
    epsg = cfg["crs"]["working_epsg"]
    cell = cfg["crs"]["cell_size_m"]
    sr = arcpy.SpatialReference(epsg)
    arcpy.env.outputCoordinateSystem = sr
    arcpy.env.cellSize = cell
    src = cfg["sources"]
    fetched = Path(paths["fetched"])

    # Soil burn severity polygons and the fire perimeter.
    log.info("soil burn severity")
    arcpy.management.Project(src["soil_severity"]["file"], "sbs_poly", sr)
    if src["perimeter"].get("file"):
        arcpy.management.Project(src["perimeter"]["file"], "fire_perimeter", sr)
    else:
        arcpy.management.Dissolve("sbs_poly", "fire_perimeter", multi_part="MULTI_PART")
    per_acres = sum(r[0] for r in rat_rows(arcpy, "fire_perimeter", ["SHAPE@AREA"])) / M2_PER_ACRE
    log.info("fire perimeter %.0f acres", per_acres)

    # TRPA boundary and the Basin frame.
    log.info("TRPA boundary")
    bdy = fetch_layer(src["trpa_boundary"]["rest"], fetched / "trpa_boundary.json", out_fields="OBJECTID", out_sr=epsg)
    arcpy.conversion.JSONToFeatures(str(bdy), "trpa_boundary")
    arcpy.analysis.Clip("fire_perimeter", "trpa_boundary", "frame_basin")
    basin_acres = sum(r[0] for r in rat_rows(arcpy, "frame_basin", ["SHAPE@AREA"])) / M2_PER_ACRE
    log.info("Caldor inside the TRPA boundary: %.0f acres", basin_acres)

    # Processing extent: perimeter plus buffer, so seed sources beyond the edge are seen.
    buf = cfg["analysis"]["buffer_m"]
    arcpy.analysis.Buffer("fire_perimeter", "frame_buffer", f"{buf} Meters", dissolve_option="ALL")
    ext = arcpy.Describe("frame_buffer").extent
    # Snap the grid to whole 30 m multiples so every raster lines up.
    xmin, ymin = (ext.XMin // cell) * cell, (ext.YMin // cell) * cell
    xmax, ymax = (ext.XMax // cell + 1) * cell, (ext.YMax // cell + 1) * cell
    arcpy.env.extent = arcpy.Extent(xmin, ymin, xmax, ymax)
    arcpy.management.AddField("frame_buffer", "one", "SHORT")
    arcpy.management.CalculateField("frame_buffer", "one", "1")
    arcpy.conversion.PolygonToRaster("frame_buffer", "one", "template", "CELL_CENTER", cellsize=cell)
    arcpy.env.snapRaster = "template"
    log.info("grid: %d x %d cells at %d m", int((xmax - xmin) / cell), int((ymax - ymin) / cell), cell)

    for name, fc in (("fire_mask", "fire_perimeter"), ("basin_mask", "frame_basin")):
        arcpy.management.AddField(fc, "one", "SHORT")
        arcpy.management.CalculateField(fc, "one", "1")
        arcpy.conversion.PolygonToRaster(fc, "one", name, "CELL_CENTER", cellsize=cell)

    # Vegetation burn severity.
    log.info("vegetation burn severity")
    vs = src["veg_severity"]
    if vs.get("raster"):
        arcpy.management.ProjectRaster(vs["raster"], "veg_sev_src", sr, "NEAREST", cell)
        sa.ExtractByMask("veg_sev_src", "frame_buffer").save("veg_sev")
    else:
        env = {"xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax, "spatialReference": {"wkid": epsg}}
        vj = fetch_layer(vs["rest"], fetched / "veg_severity.json", out_fields=vs["field"], geometry=env, in_sr=epsg, out_sr=epsg)
        arcpy.conversion.JSONToFeatures(str(vj), "veg_sev_poly")
        arcpy.conversion.PolygonToRaster("veg_sev_poly", vs["field"], "veg_sev", "MAXIMUM_AREA", cellsize=cell)
    arcpy.conversion.PolygonToRaster("sbs_poly", src["soil_severity"]["field"], "sbs", "MAXIMUM_AREA", cellsize=cell)

    # Pre-fire canopy cover and vegetation type, projected onto the working grid.
    log.info("pre-fire canopy cover and CWHR type")
    arcpy.management.ProjectRaster(src["canopy_cover_prefire"]["file"], "canopy_2020", sr, "BILINEAR", cell)
    arcpy.management.ProjectRaster(src["whr_type"]["file"], "whr_type", sr, "NEAREST", cell)
    arcpy.management.BuildRasterAttributeTable("whr_type", "Overwrite")
    lk = src["whr_type"]
    lookup = {int(v): t for v, t in rat_rows(arcpy, lk["lookup_raster"], ["Value", lk["lookup_field"]])}
    arcpy.management.AddField("whr_type", "WHRTYPE", "TEXT", field_length=8)
    missing = set()
    with arcpy.da.UpdateCursor("whr_type", ["Value", "WHRTYPE"]) as cur:
        for row in cur:
            row[1] = lookup.get(int(row[0]))
            if row[1] is None:
                missing.add(int(row[0]))
            cur.updateRow(row)
    if missing:
        log.warning("WHR values with no WHRTYPE in the lookup raster (not conifer by default): %s", sorted(missing))
    conifer_vals = [v for v, t in lookup.items() if t in set(lk["conifer_types"])]
    # InList returns the matched value itself, so test for NoData rather than == 1.
    sa.Con(sa.IsNull(sa.InList("whr_type", conifer_vals)), 0, 1).save("conifer")

    # Ownership, parcels within the Basin frame, coded.
    log.info("ownership")
    own = src["ownership"]
    bext = arcpy.Describe("frame_basin").extent
    benv = {"xmin": bext.XMin, "ymin": bext.YMin, "xmax": bext.XMax, "ymax": bext.YMax, "spatialReference": {"wkid": epsg}}
    oj = fetch_layer(own["rest"], fetched / "ownership.json", out_fields=f"APN,{own['field']},JURISDICTION", geometry=benv, in_sr=epsg, out_sr=epsg)
    arcpy.conversion.JSONToFeatures(str(oj), "parcels")
    arcpy.management.AddField("parcels", "OWN_CODE", "SHORT")
    codes = own["codes"]
    with arcpy.da.UpdateCursor("parcels", [own["field"], "OWN_CODE"]) as cur:
        for row in cur:
            row[1] = codes.get((row[0] or "").strip() or "Unknown", codes["Unknown"])
            cur.updateRow(row)
    arcpy.conversion.PolygonToRaster("parcels", "OWN_CODE", "ownership_raw", "MAXIMUM_AREA", cellsize=cell)
    sa.Con(sa.IsNull("ownership_raw"), codes["Unknown"], "ownership_raw").save("ownership")

    return {"perimeter_acres": per_acres, "basin_acres": basin_acres,
            "grid": {"xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax, "cell": cell}}


# ----------------------------------------------------------------------------- stage: analysis
def stage_analysis(arcpy, cfg: dict):
    sa = arcpy.sa
    a = cfg["analysis"]
    cell = cfg["crs"]["cell_size_m"]
    arcpy.env.snapRaster = "template"
    arcpy.env.extent = arcpy.Describe("template").extent
    arcpy.env.cellSize = cell
    vs, ss = cfg["sources"]["veg_severity"], cfg["sources"]["soil_severity"]

    veg, sbs = sa.Raster("veg_sev"), sa.Raster("sbs")
    # 1 where high, NoData elsewhere: the shape RegionGroup and EucDistance want.
    high_veg = sa.SetNull(veg != vs["high_value"], 1)
    high_veg.save("high_veg")
    high_sbs = sa.SetNull(sbs != ss["high_value"], 1)
    high_sbs.save("high_sbs")
    sa.Con((veg == vs["high_value"]) & (sbs == ss["high_value"]), 1).save("overlap_high_high")

    # Patches of high vegetation severity across the whole fire, so a patch that crosses the
    # Basin boundary keeps its full size.
    log.info("high severity patches")
    patches = sa.RegionGroup(high_veg, a["patch_connectivity"], "WITHIN", "NO_LINK")
    patches.save("patches")
    patch_acres = sa.Lookup("patches", "Count") * (cell * cell / M2_PER_ACRE)
    patch_acres.save("patch_acres")
    edges = a["patch_size_classes_acres"]
    remap = sa.RemapRange([[0, edges[0], 1]] + [[edges[i - 1], edges[i], i + 1] for i in range(1, len(edges))] + [[edges[-1], 1e9, len(edges) + 1]])
    sa.Reclassify("patch_acres", "Value", remap, "NODATA").save("patch_size_class")
    # Depth into the patch: distance from the nearest pixel that is not high severity.
    not_high = sa.SetNull(sa.IsNull(high_veg) == 0, 1)
    sa.EucDistance(not_high, cell_size=cell).save("patch_depth")

    # Seed source and distance to it.
    log.info("seed sources and distance")
    s = a["seed_source"]
    survived = sa.IsNull(sa.InList(veg, vs["seed_values"])) == 0
    if s["include_outside_perimeter"]:
        survived = survived | sa.IsNull(veg)
    seed_cond = survived & (sa.Raster("canopy_2020") >= s["canopy_cover_min_pct"])
    if s["require_conifer_type"]:
        seed_cond = seed_cond & (sa.Raster("conifer") == 1)
    seed = sa.Con(seed_cond, 1)
    seed.save("seed_source")
    dist = sa.EucDistance(seed, cell_size=cell)
    dist.save("dist_seed")
    bands = a["seed_distance_bands_m"]
    remap = sa.RemapRange([[0, bands[0], 1]] + [[bands[i - 1], bands[i], i + 1] for i in range(1, len(bands))] + [[bands[-1], 1e9, len(bands) + 1]])
    sa.Reclassify("dist_seed", "Value", remap, "NODATA").save("dist_band")
    far = sa.Con(dist > a["seed_distance_threshold_m"], 1, 0)
    far.save("far_from_seed")

    # Replanting need code on high vegetation severity pixels inside the Basin:
    #   1 high vegetation severity only
    #   3 plus high soil burn severity
    #   5 plus beyond the seed distance threshold
    #   7 all three
    log.info("need classes")
    basin = sa.Raster("basin_mask")
    hv = sa.Con(veg == vs["high_value"], 1, 0)
    # The BAER map stops short of the incident perimeter in places; treat no data as not high.
    hs = sa.Con(sa.IsNull(sbs), 0, sa.Con(sbs == ss["high_value"], 1, 0))
    nf = a.get("need_frame", {})
    if nf.get("prefire_forest_only", False):
        forest = (sa.Raster("conifer") == 1) | (sa.Raster("canopy_2020") >= nf["canopy_cover_min_pct"])
        sa.Con(forest, 1, 0).save("prefire_forest")
        need = sa.SetNull((hv == 0) | sa.IsNull(basin) | (sa.Raster("prefire_forest") == 0), hv + 2 * hs + 4 * far)
    else:
        need = sa.SetNull((hv == 0) | sa.IsNull(basin), hv + 2 * hs + 4 * far)
    need.save("need_code")
    # Need code with distance band for the web polygons: code * 10 + band.
    (need * 10 + sa.Raster("dist_band")).save("need_code_band")
    # Everything inside the Basin frame, for the severity cross tabulation.
    sa.Con(basin == 1, veg).save("veg_sev_basin")
    sa.Con(basin == 1, sbs).save("sbs_basin")
    sa.Con(basin == 1, sa.Raster("patches")).save("patches_basin")


# ----------------------------------------------------------------------------- stage: web
def stage_web(arcpy, cfg: dict, paths: dict, meta: dict):
    sa = arcpy.sa
    a = cfg["analysis"]
    cell = cfg["crs"]["cell_size_m"]
    arcpy.env.snapRaster = "template"
    arcpy.env.extent = arcpy.Describe("template").extent
    arcpy.env.cellSize = cell
    out_dir, web_dir = Path(paths["outputs"]), Path(paths["web"])
    out_dir.mkdir(parents=True, exist_ok=True)
    web_dir.mkdir(parents=True, exist_ok=True)
    vs, ss = cfg["sources"]["veg_severity"], cfg["sources"]["soil_severity"]
    veg_names, sbs_names = {int(k): v for k, v in vs["classes"].items()}, {int(k): v for k, v in ss["classes"].items()}
    thr = a["seed_distance_threshold_m"]
    bands, pedges = a["seed_distance_bands_m"], a["patch_size_classes_acres"]
    summary = {"generated": dt.datetime.now().strftime("%Y-%m-%d"), "fire": cfg["project"]["fire"],
               "perimeter_acres": meta.get("perimeter_acres"), "basin_acres": meta.get("basin_acres"),
               "cell_m": cell, "seed_distance_threshold_m": thr, "seed_distance_bands_m": bands,
               "patch_size_classes_acres": pedges, "seed_source": a["seed_source"]}

    # 1. Severity cross tabulation inside the Basin: vegetation class by soil class.
    log.info("severity cross tabulation")
    cross = tabulate_area(arcpy, "veg_sev_basin", "Value", "sbs_basin", "Value", "tab_veg_by_sbs", cell)
    rows = []
    for v in sorted(cross):
        for s_, ac in sorted(cross[v].items()):
            rows.append([v, veg_names.get(v, str(v)), s_, sbs_names.get(s_, str(s_)), ac])
    write_csv(out_dir / "severity_crosstab_basin.csv", ["veg_code", "veg_class", "soil_code", "soil_class", "acres"], rows)
    summary["crosstab"] = [{"veg": r[0], "veg_class": r[1], "soil": r[2], "soil_class": r[3], "acres": round(r[4], 1)} for r in rows]
    veg_tot = {v: sum(d.values()) for v, d in cross.items()}
    sbs_tot = {}
    for d in cross.values():
        for s_, ac in d.items():
            sbs_tot[s_] = sbs_tot.get(s_, 0) + ac
    summary["veg_acres"] = {veg_names.get(k, str(k)): round(v, 1) for k, v in sorted(veg_tot.items())}
    summary["high_veg_all_acres"] = round(veg_tot.get(vs["high_value"], 0.0), 1)
    summary["need_frame"] = a.get("need_frame", {"prefire_forest_only": False})
    summary["soil_acres"] = {sbs_names.get(k, str(k)): round(v, 1) for k, v in sorted(sbs_tot.items())}

    # 2. Need classes (acres by code), and by distance band.
    log.info("need classes")
    code_names = {1: "High vegetation severity only", 3: "High vegetation and high soil severity",
                  5: f"High vegetation severity, beyond {thr} m of seed", 7: f"High vegetation and soil severity, beyond {thr} m of seed"}
    need_tab = {int(v): acres(c, cell) for v, c in raster_table(arcpy, "need_code")}
    write_csv(out_dir / "need_classes_basin.csv", ["need_code", "need_class", "acres"], [[k, code_names[k], v] for k, v in sorted(need_tab.items())])
    summary["need"] = [{"code": k, "label": code_names[k], "acres": round(v, 1)} for k, v in sorted(need_tab.items())]
    summary["need_totals"] = {
        "high_veg": round(sum(need_tab.values()), 1),
        "high_veg_high_soil": round(need_tab.get(3, 0) + need_tab.get(7, 0), 1),
        "high_veg_far": round(need_tab.get(5, 0) + need_tab.get(7, 0), 1),
        "all_three": round(need_tab.get(7, 0), 1),
    }
    band_tab = tabulate_area(arcpy, "need_code", "Value", "dist_band", "Value", "tab_need_by_band", cell)
    rows, dist_rows = [], []
    for code in sorted(band_tab):
        for b, ac in sorted(band_tab[code].items()):
            rows.append([code, code_names[code], b, band_label(bands, b, "m"), ac])
    write_csv(out_dir / "need_by_seed_distance_band.csv", ["need_code", "need_class", "band", "distance_band", "acres"], rows)
    summary["need_by_band"] = [{"code": r[0], "band": r[2], "band_label": r[3], "acres": round(r[4], 1)} for r in rows]
    # Distance bands for all high veg pixels and for the high/high overlap, so the app can move the cutoff.
    for code in sorted(band_tab):
        for b, ac in band_tab[code].items():
            dist_rows.append({"code": code, "soil_high": code in (3, 7), "band": b, "acres": ac})
    summary["dist_bands"] = [{"band": i + 1, "label": band_label(bands, i + 1, "m"),
                              "high_veg": round(sum(r["acres"] for r in dist_rows if r["band"] == i + 1), 1),
                              "high_veg_high_soil": round(sum(r["acres"] for r in dist_rows if r["band"] == i + 1 and r["soil_high"]), 1)}
                             for i in range(len(bands) + 1)]
    # Mean and distribution of distance for high severity pixels in the Basin.
    hv_dist = sa.Con(sa.IsNull(sa.Raster("need_code")) == 0, sa.Raster("dist_seed"))
    hv_dist.save("dist_seed_highveg_basin")
    r = sa.Raster("dist_seed_highveg_basin")
    summary["dist_stats"] = {"mean_m": round(float(r.mean), 1), "max_m": round(float(r.maximum), 1)}

    # 3. Patches: size class acres inside the Basin, and the per-patch table.
    log.info("patches")
    size_names = {i + 1: band_label(pedges, i + 1, "acres") for i in range(len(pedges) + 1)}
    size_tab = tabulate_area(arcpy, "basin_mask", "Value", "patch_size_class", "Value", "tab_size_basin", cell)
    size_acres = size_tab.get(1, {})
    write_csv(out_dir / "patch_size_classes_basin.csv", ["size_class", "patch_size", "acres_in_basin"], [[k, size_names[k], v] for k, v in sorted(size_acres.items())])
    summary["patch_size_classes"] = [{"cls": k, "label": size_names[k], "acres": round(v, 1)} for k, v in sorted(size_acres.items())]

    # Per patch: whole-fire acres, Basin acres, max depth, share high soil, share beyond threshold.
    pt = {int(v): acres(c, cell) for v, c in raster_table(arcpy, "patches")}
    pb = {int(v): acres(c, cell) for v, c in raster_table(arcpy, "patches_basin")}
    arcpy.sa.ZonalStatisticsAsTable("patches_basin", "Value", "patch_depth", "zs_depth", "DATA", "MAXIMUM")
    depth = {int(r[0]): r[1] for r in rat_rows(arcpy, "zs_depth", ["Value", "MAX"])}
    arcpy.sa.ZonalStatisticsAsTable("patches_basin", "Value", "dist_seed", "zs_dist", "DATA", "MEAN")
    mdist = {int(r[0]): r[1] for r in rat_rows(arcpy, "zs_dist", ["Value", "MEAN"])}
    soil_tab = tabulate_area(arcpy, "patches_basin", "Value", "high_sbs", "Value", "tab_patch_soil", cell)
    far_tab = tabulate_area(arcpy, "patches_basin", "Value", "far_from_seed", "Value", "tab_patch_far", cell)
    own_tab = tabulate_area(arcpy, "patches_basin", "Value", "ownership", "Value", "tab_patch_own", cell)
    own_names = {v: k for k, v in cfg["sources"]["ownership"]["codes"].items()}
    patch_rows = []
    for pid, ac_b in sorted(pb.items(), key=lambda kv: -kv[1]):
        own = own_tab.get(pid, {})
        major = own_names.get(max(own, key=own.get), "Unknown") if own else "Unknown"
        patch_rows.append({
            "patch_id": pid, "acres_total": round(pt.get(pid, ac_b), 1), "acres_basin": round(ac_b, 1),
            "size_class": next((i + 1 for i, e in enumerate(pedges) if pt.get(pid, ac_b) <= e), len(pedges) + 1),
            "depth_max_m": round(depth.get(pid, 0.0), 0), "dist_seed_mean_m": round(mdist.get(pid, 0.0), 0),
            "acres_high_soil": round(soil_tab.get(pid, {}).get(1, 0.0), 1),
            "acres_far": round(far_tab.get(pid, {}).get(1, 0.0), 1),
            "owner_major": major,
        })
    write_csv(out_dir / "patches_basin.csv", list(patch_rows[0].keys()) if patch_rows else ["patch_id"], [list(r.values()) for r in patch_rows])
    summary["patches"] = patch_rows
    summary["patch_count_basin"] = len(patch_rows)

    # 4. By ownership and by vegetation type.
    log.info("ownership and vegetation type")
    own_need = tabulate_area(arcpy, "ownership", "Value", "need_code", "Value", "tab_own_need", cell)
    rows = []
    for oc in sorted(own_need):
        for code, ac in sorted(own_need[oc].items()):
            rows.append([own_names.get(oc, str(oc)), code, code_names[code], ac])
    write_csv(out_dir / "need_by_ownership.csv", ["ownership", "need_code", "need_class", "acres"], rows)
    summary["by_owner"] = [{"owner": r[0], "code": r[1], "acres": round(r[3], 1)} for r in rows]
    whr_need = tabulate_area(arcpy, "whr_type", "Value", "need_code", "Value", "tab_whr_need", cell)
    lookup = {int(v): t for v, t in rat_rows(arcpy, "whr_type", ["Value", "WHRTYPE"])}
    names = cfg["sources"]["whr_type"]["names"]
    rows = []
    for wv in sorted(whr_need):
        t = lookup.get(wv) or f"value {wv}"
        for code, ac in sorted(whr_need[wv].items()):
            rows.append([t, names.get(t, t), code, code_names[code], ac])
    write_csv(out_dir / "need_by_whr_type.csv", ["whr_type", "whr_name", "need_code", "need_class", "acres"], rows)
    summary["by_whr"] = [{"type": r[0], "name": r[1], "code": r[2], "acres": round(r[4], 1)} for r in rows]

    # 5. Polygons for the app.
    log.info("web polygons")
    tol = f"{cfg['web']['generalize_tolerance_m']} Meters"

    def to_geojson(fc: str, name: str):
        out = web_dir / f"{name}.geojson"
        if out.exists():
            out.unlink()
        arcpy.conversion.FeaturesToJSON(fc, str(out), "NOT_FORMATTED", "NO_Z_VALUES", "NO_M_VALUES", "GEOJSON", "WGS84", "USE_FIELD_NAME")
        log.info("wrote %s (%.1f MB)", out.relative_to(ROOT), out.stat().st_size / 1e6)

    # Need classes with distance band.
    arcpy.conversion.RasterToPolygon("need_code_band", "need_poly_raw", "NO_SIMPLIFY", "Value")
    arcpy.management.Dissolve("need_poly_raw", "need_poly", "gridcode", multi_part="MULTI_PART")
    for fname, ftype in (("need_code", "SHORT"), ("dist_band", "SHORT"), ("soil_high", "SHORT"), ("far", "SHORT"), ("acres", "DOUBLE")):
        arcpy.management.AddField("need_poly", fname, ftype)
    with arcpy.da.UpdateCursor("need_poly", ["gridcode", "need_code", "dist_band", "soil_high", "far", "acres", "SHAPE@AREA"]) as cur:
        for row in cur:
            code, band = divmod(row[0], 10)
            row[1], row[2], row[3], row[4], row[5] = code, band, int(code in (3, 7)), int(code in (5, 7)), row[6] / M2_PER_ACRE
            cur.updateRow(row)
    arcpy.management.CopyFeatures("need_poly", "need_poly_web")
    arcpy.edit.Generalize("need_poly_web", tol)
    to_geojson("need_poly_web", "need")

    # Patches inside the Basin, attributed.
    arcpy.conversion.RasterToPolygon("patches_basin", "patch_poly_raw", "NO_SIMPLIFY", "Value")
    arcpy.management.Dissolve("patch_poly_raw", "patch_poly", "gridcode", multi_part="MULTI_PART")
    for fname, ftype in (("patch_id", "LONG"), ("acres_total", "DOUBLE"), ("acres_basin", "DOUBLE"), ("size_class", "SHORT"), ("depth_max_m", "DOUBLE"),
                         ("dist_seed_mean_m", "DOUBLE"), ("acres_high_soil", "DOUBLE"), ("acres_far", "DOUBLE"), ("owner_major", "TEXT")):
        arcpy.management.AddField("patch_poly", fname, ftype)
    by_id = {r["patch_id"]: r for r in patch_rows}
    with arcpy.da.UpdateCursor("patch_poly", ["gridcode", "patch_id", "acres_total", "acres_basin", "size_class", "depth_max_m", "dist_seed_mean_m", "acres_high_soil", "acres_far", "owner_major"]) as cur:
        for row in cur:
            r = by_id.get(int(row[0]))
            if r is None:
                cur.deleteRow()
                continue
            row[1:] = [r["patch_id"], r["acres_total"], r["acres_basin"], r["size_class"], r["depth_max_m"], r["dist_seed_mean_m"], r["acres_high_soil"], r["acres_far"], r["owner_major"]]
            cur.updateRow(row)
    arcpy.management.DeleteField("patch_poly", ["gridcode"])
    arcpy.management.CopyFeatures("patch_poly", "patch_poly_web")
    arcpy.edit.Generalize("patch_poly_web", tol)
    to_geojson("patch_poly_web", "patches")

    # Soil burn severity inside the Basin frame, for a toggle layer.
    arcpy.analysis.Clip("sbs_poly", "frame_basin", "sbs_basin_poly")
    arcpy.management.CopyFeatures("sbs_basin_poly", "sbs_basin_web")
    arcpy.edit.Generalize("sbs_basin_web", tol)
    to_geojson("sbs_basin_web", "soil_severity")

    # Vegetation severity inside the Basin frame (from the raster so it matches the analysis).
    arcpy.conversion.RasterToPolygon("veg_sev_basin", "veg_basin_raw", "NO_SIMPLIFY", "Value")
    arcpy.management.Dissolve("veg_basin_raw", "veg_basin_poly", "gridcode", multi_part="MULTI_PART")
    arcpy.edit.Generalize("veg_basin_poly", tol)
    to_geojson("veg_basin_poly", "veg_severity")

    # Seed sources within the Basin frame plus buffer, for context.
    arcpy.analysis.Buffer("frame_basin", "frame_basin_buffer", f"{a['buffer_m']} Meters", dissolve_option="ALL")
    sa.ExtractByMask("seed_source", "frame_basin_buffer").save("seed_source_basin")
    arcpy.conversion.RasterToPolygon("seed_source_basin", "seed_raw", "NO_SIMPLIFY", "Value")
    arcpy.management.Dissolve("seed_raw", "seed_poly", "gridcode", multi_part="MULTI_PART")
    arcpy.edit.Generalize("seed_poly", tol)
    to_geojson("seed_poly", "seed_sources")

    # Frames.
    to_geojson("frame_basin", "frame_basin")
    arcpy.analysis.Clip("fire_perimeter", "frame_basin_buffer", "perimeter_near_basin")
    arcpy.edit.Generalize("perimeter_near_basin", tol)
    to_geojson("perimeter_near_basin", "perimeter")

    (web_dir / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    log.info("wrote %s", (web_dir / "summary.json").relative_to(ROOT))
    return summary


# ----------------------------------------------------------------------------- check
def check_inputs(cfg: dict) -> bool:
    ok = True
    src = cfg["sources"]
    for label, p in (("soil severity", src["soil_severity"]["file"]), ("canopy cover 2020", src["canopy_cover_prefire"]["file"]),
                     ("WHR type", src["whr_type"]["file"]), ("WHR lookup raster", src["whr_type"]["lookup_raster"])):
        exists = Path(p).exists() or Path(p).parent.exists()  # a raster inside a gdb is not a file
        log.info("%-20s %s %s", label, "ok " if exists else "MISSING", p)
        ok &= exists
    for label, url in (("veg severity", src["veg_severity"]["rest"]), ("TRPA boundary", src["trpa_boundary"]["rest"]), ("ownership", src["ownership"]["rest"])):
        try:
            body = rest_query(url, {"where": "1=1", "returnCountOnly": "true", "f": "json"})
            log.info("%-20s ok  %s (%s features)", label, url, body.get("count"))
        except Exception as e:  # noqa: BLE001
            log.error("%-20s FAIL %s: %s", label, url, e)
            ok = False
    return ok


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="verify inputs and exit")
    ap.add_argument("--stage", choices=["all", "inputs", "analysis", "web"], default="all")
    args = ap.parse_args()

    cfg = load_config()
    paths = {k: resolve(v) for k, v in cfg["paths"].items()}
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    setup_logging(Path(paths["logs"]), stamp)
    log.info("config %s", ROOT / "config.yaml")

    if args.check:
        sys.exit(0 if check_inputs(cfg) else 1)

    arcpy = import_arcpy(paths["gdb"])
    meta_path = Path(paths["gdb"]).parent / "run_meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    t0 = dt.datetime.now()
    if args.stage in ("all", "inputs"):
        meta = stage_inputs(arcpy, cfg, paths)
        meta_path.write_text(json.dumps(meta))
    if args.stage in ("all", "analysis"):
        stage_analysis(arcpy, cfg)
    if args.stage in ("all", "web"):
        summary = stage_web(arcpy, cfg, paths, meta)
        log.info("high veg %.0f ac; high veg + high soil %.0f ac; high veg beyond %d m %.0f ac; all three %.0f ac",
                 summary["need_totals"]["high_veg"], summary["need_totals"]["high_veg_high_soil"],
                 cfg["analysis"]["seed_distance_threshold_m"], summary["need_totals"]["high_veg_far"], summary["need_totals"]["all_three"])
    log.info("done in %.0f s", (dt.datetime.now() - t0).total_seconds())


if __name__ == "__main__":
    main()
