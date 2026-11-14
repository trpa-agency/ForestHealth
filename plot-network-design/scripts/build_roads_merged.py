"""Merge USFS_Roads (Vector.sde, read only) and the PROTECT curated OSM road network into one
line layer for the frame buffer and access classes. Writes data/processed/roads_merged.gdb/roads.

Fields: src (USFS or PROTECT), road_class, drivable (1 = a crew can drive to it).
  PROTECT: every segment drivable (public OSM network: primary to service).
  USFS:    ROUTE_STATUS 'EX', OPER_MAINT_LEVEL 2 to 5, RD_GATED not YES. Decommissioned routes are dropped.
Run in arcgispro-py3 with F: mounted:  python scripts/build_roads_merged.py
"""
import arcpy
from pathlib import Path

USFS = r"F:\GIS\DB_CONNECT\Vector.sde\SDE.Transportation\SDE.USFS_Roads"
PROTECT = r"F:\GIS\PROJECTS\Transportation\Protect\PROTECT_analysis\PROTECT_curated.gdb\Assets\Roads"
root = Path(__file__).resolve().parent.parent / "data" / "processed"
root.mkdir(parents=True, exist_ok=True)
gdb = root / "roads_merged.gdb"
if not arcpy.Exists(str(gdb)):
    arcpy.management.CreateFileGDB(str(root), gdb.name)
out = str(gdb / "roads")
arcpy.env.overwriteOutput = True
sr = arcpy.Describe(PROTECT).spatialReference
arcpy.management.CreateFeatureclass(str(gdb), "roads", "POLYLINE", spatial_reference=sr)
for name, typ, ln in [("src", "TEXT", 10), ("road_class", "TEXT", 60), ("drivable", "SHORT", None), ("name", "TEXT", 120)]:
    arcpy.management.AddField(out, name, typ, field_length=ln)

n = {"PROTECT": 0, "USFS": 0, "USFS_drivable": 0, "USFS_decommissioned_dropped": 0}
with arcpy.da.InsertCursor(out, ["SHAPE@", "src", "road_class", "drivable", "name"]) as ic:
    with arcpy.da.SearchCursor(PROTECT, ["SHAPE@", "class", "name"], spatial_reference=sr) as sc:
        for g, c, nm in sc:
            ic.insertRow([g, "PROTECT", c, 1, (nm or "")[:120]]); n["PROTECT"] += 1
    with arcpy.da.SearchCursor(USFS, ["SHAPE@", "ROUTE_STATUS", "OPER_MAINT_LEVEL", "RD_GATED", "NAME", "ID"], spatial_reference=sr) as sc:
        for g, st, ml, gated, nm, rid in sc:
            if g is None or (st or "").startswith("DE"):
                n["USFS_decommissioned_dropped"] += 1; continue
            drive = int((st or "").startswith("EX") and (ml or "")[:1] in "2345" and (ml or "") != "" and not (gated or "").upper().startswith("YES"))
            ic.insertRow([g, "USFS", ml, drive, f"{rid or ''} {nm or ''}".strip()[:120]])
            n["USFS"] += 1; n["USFS_drivable"] += drive
print(n, "->", out)
