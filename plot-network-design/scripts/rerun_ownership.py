"""Rerun section 6b (ownership by Identity overlay) on the existing tessellation feature classes.

Run from the folder root in the Pro env:
    python scripts/rerun_ownership.py
Reads the inputs already in data/processed/tessellation_work.gdb (boundary, ltbmu, lake, ownership), writes
the own_* fields into both grids in outputs/tessellation.gdb, re-exports the shapefile and GeoPackage copies
with today's stamp, and updates the ownership block of outputs/tessellation_summary.json. Everything else in
the notebook is untouched, so this takes minutes instead of the full run's hour.
"""
import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.io import load_config, get_logger  # noqa: E402
from src import ownership_overlay as OO  # noqa: E402

cfg = load_config()
log = get_logger("rerun_ownership")
TC = cfg["tessellation"]
O = (ROOT / cfg["paths"]["outputs"]).resolve()
P = (ROOT / cfg["paths"]["processed"]).resolve()
GDB = (O / TC["gdb"]).as_posix()
WORK = (P / "tessellation_work.gdb").as_posix()
GRID = f"TahoeBasin_Hex{int(TC['cell_area_ha'])}ha"
FINE = f"TahoeBasin_Hex{round(float(TC['cell_area_ha']) / int(TC['fine_ratio']))}ha"
STAMP = pd.Timestamp.today().strftime("%Y%m%d")

_t = time.time()
import arcpy  # noqa: E402

arcpy.env.workspace = GDB
arcpy.env.overwriteOutput = True
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(int(TC["epsg"]))
arcpy.env.geographicTransformations = TC["datum_transformation"]
log.info(f"arcpy imported in {time.time() - _t:.0f} s")


def add_fields(fc, spec):
    have = {f.name for f in arcpy.ListFields(fc)}
    for name, ftype, *rest in spec:
        if name not in have:
            arcpy.management.AddField(fc, name, ftype, field_length=rest[0] if rest else None)


def one_geom(fc):
    geom = None
    with arcpy.da.SearchCursor(fc, ["SHAPE@"]) as cur:
        for (shp,) in cur:
            geom = shp if geom is None else geom.union(shp)
    return geom


boundary_fc, ltbmu_fc, lake_fc, own_fc = (f"{WORK}/{n}" for n in ("boundary", "ltbmu", "lake", "ownership"))
for fc in (boundary_fc, ltbmu_fc, lake_fc, own_fc, f"{GDB}/{GRID}", f"{GDB}/{FINE}"):
    assert arcpy.Exists(fc), f"missing {fc}; run the notebook first"

LAND = one_geom(boundary_fc).union(one_geom(ltbmu_fc)).difference(one_geom(lake_fc))
land_fc = f"{WORK}/land"
arcpy.management.CopyFeatures([LAND], land_fc)
log.info(f"land {LAND.area / 1e6:,.1f} km2")

own_stats = OO.run([f"{GDB}/{GRID}", f"{GDB}/{FINE}"], own_fc, TC["ownership_field"], dict(TC["ownership_classes"]),
                   land_fc, boundary_fc, WORK, TC["min_land_frac"], add_fields, log)
for fc, s in own_stats.items():
    print(f"{fc}: " + ", ".join(f"{k} {v}%" for k, v in s.items() if k in (*TC["ownership_classes"], "other", "nodata"))
          + f"; dominant {s['cells_by_dominant']}; rescaled {s['cells_rescaled_for_overlap']}; cells with land {s['cells_with_land']}")

for fc in (GRID, FINE):
    base = O / f"{fc}_UTM10N_{STAMP}"
    arcpy.conversion.ExportFeatures(f"{GDB}/{fc}", f"{base}.shp")
    gpkg = Path(f"{base}.gpkg")
    if gpkg.exists():
        gpkg.unlink()
    arcpy.management.CreateSQLiteDatabase(gpkg.as_posix(), "GEOPACKAGE_1.3")
    arcpy.conversion.ExportFeatures(f"{GDB}/{fc}", f"{gpkg.as_posix()}/{fc}")
    log.info(f"exported {fc} -> {base.name}.shp, .gpkg")

summary_path = O / "tessellation_summary.json"
summary = json.loads(summary_path.read_text(encoding="utf-8"))
summary["ownership"] = {"source": TC["sources"]["ownership"], "method": "identity overlay, src/ownership_overlay.py", **own_stats}
summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
log.info("summary updated")
