"""
src/layers.py: read a source that is a local file, a TRPA ArcGIS REST service, an SDE
feature class or raster, or a file geodatabase feature class or raster.

    resolve_source(entry, cfg, prefer=None)
        A `sources:` entry is a plain string or a mapping of alternative forms
        (rrk, lidar, sde, file) plus options (where, field). Returns (path, options).
        rrk or lidar is picked by cfg["strata"]["source"]; sde is picked when arcpy is
        importable, file otherwise; `prefer` overrides both.

    read_layer(source, cfg, where="1=1", fields="*")
        source: local path (.gpkg/.shp/.geojson), a FeatureServer/MapServer layer URL
                (https://maps.trpa.gov/server/rest/services/<Service>/FeatureServer/0),
                or an arcpy path (F:\\GIS\\DB_CONNECT\\Vector.sde\\SDE.<Dataset>\\SDE.<Class>,
                or <name>.gdb\\<class>). arcpy paths are read with arcpy.da.SearchCursor.
        Returns a GeoDataFrame in cfg["crs"]["working"]. Pages through maxRecordCount.

    read_raster(source, cfg, bbox=None, nodata_to_nan=False)
        source: local GeoTIFF path, an ImageServer URL
                (https://maps.trpa.gov/server/rest/services/<Image>/ImageServer),
                or an arcpy raster path (Raster.sde\\SDE.<Raster>, <name>.gdb\\<raster>).
        Returns (array, transform, crs). For an ImageServer, exports the bbox at the
        LiDAR grid resolution in the working CRS and caches the GeoTIFF in data/raw/.
        For an arcpy raster, reads with arcpy.RasterToNumPyArray at the raster's own
        extent and cell size (bbox, if given, is in the raster's CRS).

The file and REST behaviour is unchanged. arcpy is imported only inside the functions
that need it, so the module imports without ArcGIS Pro. SDE connections are READ ONLY.
"""
from __future__ import annotations

import hashlib
import importlib.util
import math
import re
from pathlib import Path

import geopandas as gpd
import requests

from src.io import project_root

_ARCGIS_RE = re.compile(r"\.(sde|gdb)([\\/]|$)", re.IGNORECASE)
_FORMS = ("rrk", "lidar", "sde", "rest", "file")


def _is_url(s: str) -> bool:
    return str(s).lower().startswith("http")


def is_arcgis_path(s: str) -> bool:
    """True for a path that goes through an .sde connection or a file geodatabase."""
    return bool(_ARCGIS_RE.search(str(s)))


def arcpy_available() -> bool:
    """Cheap probe: arcpy is importable in this interpreter (without importing it)."""
    try:
        return importlib.util.find_spec("arcpy") is not None
    except (ImportError, ValueError):
        return False


def resolve_source(entry, cfg: dict, prefer: str | None = None) -> tuple[str, dict]:
    """
    Pick one path from a `sources:` entry.

    A plain string is returned as is with empty options. A mapping holds alternative
    forms of the same source: `rrk` (threshold raster on F:), `lidar` (lidar-2022
    Derived product), `sde` (Vector.sde or Raster.sde feature class or raster), `rest`
    (maps.trpa.org FeatureServer or MapServer layer URL), `file` (local copy under
    data/raw). `use: <form>` on the entry pins one form. Any other key (`where`, `field`, `layer`) is an
    option returned in the second element.

    Selection order: `prefer` when present in the entry; cfg["strata"]["source"] when
    that form is present; `sde` when arcpy is importable; `rest`; `file`; else the only form.
    """
    if not isinstance(entry, dict):
        return str(entry), {}
    forms = {k: v for k, v in entry.items() if k in _FORMS and v}
    opts = {k: v for k, v in entry.items() if k not in _FORMS}
    if not forms:
        raise ValueError(f"source entry has no path form ({list(_FORMS)}): {entry}")
    if prefer and prefer in forms:
        return str(forms[prefer]), opts
    use = str(opts.pop("use", "") or "").lower()          # per-entry pin, e.g. use: rest
    if use in forms:
        return str(forms[use]), opts
    want = str(cfg.get("strata", {}).get("source", "")).lower()
    if want in forms:
        return str(forms[want]), opts
    if "sde" in forms and arcpy_available():
        return str(forms["sde"]), opts
    if "rest" in forms:
        return str(forms["rest"]), opts
    if "file" in forms:
        return str(forms["file"]), opts
    if "sde" in forms:
        return str(forms["sde"]), opts
    if len(forms) == 1:
        return str(next(iter(forms.values()))), opts
    raise ValueError(
        f"cannot pick a form from {sorted(forms)}: set strata.source to one of them or pass prefer=")


# --------------------------------------------------------------------------- vectors

def _epsg(cfg: dict) -> int:
    return int(str(cfg["crs"]["working"]).split(":")[-1])


def _read_layer_arcpy(source: str, cfg: dict, where: str, fields, log=None) -> gpd.GeoDataFrame:
    """Read an SDE or gdb feature class with arcpy.da.SearchCursor into a GeoDataFrame."""
    import arcpy
    from shapely import wkb

    wcrs = cfg["crs"]["working"]
    sr = arcpy.SpatialReference(_epsg(cfg))
    skip = {"Geometry", "Blob", "Raster"}
    all_fields = [f for f in arcpy.ListFields(source) if f.type not in skip]
    if fields in ("*", None):
        names = [f.name for f in all_fields]
    elif isinstance(fields, str):
        names = [s.strip() for s in fields.split(",") if s.strip()]
    else:
        names = list(fields)
    where = None if where in (None, "", "1=1") else where
    rows, geoms = [], []
    with arcpy.da.SearchCursor(source, ["SHAPE@WKB"] + names, where_clause=where, spatial_reference=sr) as cur:
        for rec in cur:
            geoms.append(wkb.loads(bytes(rec[0])) if rec[0] is not None else None)
            rows.append(rec[1:])
    gdf = gpd.GeoDataFrame(gpd.pd.DataFrame(rows, columns=names), geometry=geoms, crs=wcrs)
    if log:
        log.info(f"Read {len(gdf):,} features from {source}" + (f" where {where}" if where else ""))
    return gdf


def read_layer(source, cfg: dict, where: str = "1=1", fields: str = "*", log=None,
               prefer: str | None = None) -> gpd.GeoDataFrame:
    source, opts = resolve_source(source, cfg, prefer)
    if where in (None, "", "1=1") and opts.get("where"):
        where = opts["where"]
    wcrs = cfg["crs"]["working"]

    if is_arcgis_path(source):
        return _read_layer_arcpy(source, cfg, where, fields, log)

    if not _is_url(source):
        path = project_root() / source
        kw = {"where": where} if where not in (None, "", "1=1") else {}
        gdf = gpd.read_file(path, **kw)
        if log: log.info(f"Read {len(gdf):,} features from {source} (CRS {gdf.crs})")
        return gdf.to_crs(wcrs)

    epsg = _epsg(cfg)
    base = source.rstrip("/")
    meta = requests.get(base, params={"f": "json"}, timeout=60).json()
    page = int(meta.get("maxRecordCount", 1000))
    frames, offset = [], 0
    while True:
        params = {"where": where, "outFields": fields, "outSR": epsg, "f": "geojson",
                  "resultOffset": offset, "resultRecordCount": page, "returnGeometry": "true"}
        r = requests.get(f"{base}/query", params=params, timeout=300)
        r.raise_for_status()
        gj = r.json()
        feats = gj.get("features", [])
        if not feats:
            break
        frames.append(gpd.GeoDataFrame.from_features(feats, crs=f"EPSG:{epsg}"))
        offset += len(feats)
        if not gj.get("properties", {}).get("exceededTransferLimit", len(feats) == page):
            break
    gdf = gpd.GeoDataFrame(gpd.pd.concat(frames, ignore_index=True), crs=f"EPSG:{epsg}") if frames else gpd.GeoDataFrame(geometry=[], crs=f"EPSG:{epsg}")
    if log: log.info(f"Read {len(gdf):,} features from {meta.get('name', base)}")
    return gdf


# --------------------------------------------------------------------------- rasters

MAX_ARCPY_CELLS = 250_000_000   # above this RasterToNumPyArray will not fit; resample first


def arcpy_raster_crs(sr):
    """rasterio CRS from an arcpy SpatialReference (EPSG when it has one, else WKT)."""
    from rasterio.crs import CRS
    code = getattr(sr, "factoryCode", 0) or 0
    if code:
        return CRS.from_epsg(int(code))
    return CRS.from_wkt(sr.exportToString().split(";")[0])


def _read_raster_arcpy(source: str, cfg: dict, bbox: tuple | None, nodata_to_nan: bool, log=None):
    """Read an SDE or gdb raster with arcpy.RasterToNumPyArray; (array, transform, crs)."""
    import arcpy
    import numpy as np
    from rasterio.transform import from_origin

    r = arcpy.Raster(source)
    cw, ch = float(r.meanCellWidth), float(r.meanCellHeight)
    ext = r.extent
    if bbox is None:
        col0, row0 = 0, 0
        ncols, nrows = int(r.width), int(r.height)
    else:
        xmin, ymin, xmax, ymax = bbox
        col0 = max(int(math.floor((xmin - ext.XMin) / cw)), 0)
        col1 = min(int(math.ceil((xmax - ext.XMin) / cw)), int(r.width))
        row0 = max(int(math.floor((ext.YMax - ymax) / ch)), 0)
        row1 = min(int(math.ceil((ext.YMax - ymin) / ch)), int(r.height))
        ncols, nrows = col1 - col0, row1 - row0
    if ncols * nrows > MAX_ARCPY_CELLS:
        raise MemoryError(
            f"{source}: {ncols:,} x {nrows:,} cells at {cw} m will not fit in memory; project or "
            f"resample it to the design grid first (design_template.SourceReader.raster_on_grid)")
    x0 = ext.XMin + col0 * cw
    y1 = ext.YMax - row0 * ch
    y0 = y1 - nrows * ch
    arr = arcpy.RasterToNumPyArray(r, arcpy.Point(x0, y0), ncols, nrows)
    nodata = r.noDataValue
    if nodata_to_nan:
        arr = arr.astype("float64")
        if nodata is not None:
            arr[arr == nodata] = np.nan
    transform = from_origin(x0, y1, cw, ch)
    crs = arcpy_raster_crs(r.spatialReference)
    if log:
        log.info(f"Read raster {source}: {arr.shape}, cell {cw} m, CRS {crs.to_string()}, nodata {nodata}")
    return arr, transform, crs


def read_raster(source, cfg: dict, bbox: tuple | None = None, log=None,
                nodata_to_nan: bool = False, prefer: str | None = None):
    import rasterio
    source, _ = resolve_source(source, cfg, prefer)
    wcrs = cfg["crs"]["working"]

    if is_arcgis_path(source):
        return _read_raster_arcpy(source, cfg, bbox, nodata_to_nan, log)

    if not _is_url(source):
        with rasterio.open(project_root() / source) as r:
            if log: log.info(f"Read raster {source}: {r.shape}, res {r.res}, CRS {r.crs}")
            if nodata_to_nan:
                return r.read(1, masked=True).astype("float64").filled(float("nan")), r.transform, r.crs
            return r.read(1), r.transform, r.crs

    epsg = _epsg(cfg)
    g = cfg["crs"]["lidar_grid_m"]
    if bbox is None:
        raise ValueError("bbox (xmin, ymin, xmax, ymax) in working CRS is required for an ImageServer source")
    xmin, ymin, xmax, ymax = bbox
    size = f"{int((xmax - xmin) / g)},{int((ymax - ymin) / g)}"
    cache = project_root() / cfg["paths"]["raw"] / ("imgsvc_" + hashlib.md5(f"{source}{bbox}{g}".encode()).hexdigest()[:10] + ".tif")
    if not cache.exists():
        params = {"bbox": ",".join(map(str, bbox)), "bboxSR": epsg, "imageSR": epsg, "size": size,
                  "format": "tiff", "pixelType": "F32", "interpolation": "RSP_BilinearInterpolation", "f": "image"}
        r = requests.get(f"{source.rstrip('/')}/exportImage", params=params, timeout=600)
        r.raise_for_status()
        cache.write_bytes(r.content)
        if log: log.info(f"Exported {source} to {cache.name} ({size} px at {g} m)")
    with rasterio.open(cache) as r:
        if nodata_to_nan:
            return r.read(1, masked=True).astype("float64").filled(float("nan")), r.transform, r.crs
        return r.read(1), r.transform, r.crs


def read_raster_attribute_table(source, cfg: dict, prefer: str | None = None, log=None):
    """
    The attribute table of an arcpy raster (Value, Count, and any joined fields such as
    WHRTYPE) as a DataFrame. This is how the forest type crosswalk is read from
    veg_type_nonurban, the same way the threshold rerun does it.
    """
    import arcpy
    import pandas as pd
    source, _ = resolve_source(source, cfg, prefer)
    fields = [f.name for f in arcpy.ListFields(source)]
    with arcpy.da.SearchCursor(source, fields) as cur:
        df = pd.DataFrame([list(r) for r in cur], columns=fields)
    if log: log.info(f"Attribute table of {source}: {len(df)} rows, fields {fields}")
    return df
