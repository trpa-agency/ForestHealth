"""
src/design_template.py: helpers that only notebooks/00_sample_design_template.ipynb needs.

Everything that already existed stays where it is: class assignment, cell collapse,
allocation, the Python GRTS, and the installation order in src/strata.py; balance
covariates in src/covariates.py; precision arithmetic in src/sample_size.py; the hex
lattice in src/tessellation.py; QA checks in src/qa.py; reads in src/layers.py. This
module holds only what none of them had:

    SourceReader            one door to every source: real (arcpy, file, REST) or synthetic
    make_synthetic_sources  a toy Basin as rasters and vector layers, so every section of
                            the template runs the same code without F: or arcpy
    walk_sde, source_status discovery of Vector.sde and a found/missing table of config
    forest_type_array, rasterize_mask, terrain, build_units, sample_units, to_working_crs
                            the raster frame: population, exclusions, 3 by 3 units
    population_check        acres by type against report Table 1
    strata_config_for_source, proxy_columns, elevation_band
                            the rrk or lidar proxy columns strata.classify_cells expects
    hike_distance_m, access_class_mi
                            access class from hike distance to a drivable road (Oct 19 2026)
    inclusion_multiplier, selection_targets, design_ip, expected_counts
                            the one-selection design: tail and steep multipliers, per-type
                            targets and list lengths, inclusion probabilities, expected counts
    write_selection_inputs, run_rscript, python_selection, normalise_spsurvey_sites
                            the spsurvey call (scripts/grts_select.R) and the Python fallback
    assign_levels           min, full, and backup labels and one installation order
    appendix_a_tables       counts by type, access class, and owner for RFP Appendix A
    spatial_balance, vp9_class, vp10_class, hex_keys
                            evaluation and export helpers

Design as of Oct 19 2026 (Mason and Andy): one GRTS selection stratified by forest type,
unequal probability within type (1.5x tail cells, 0.5x slopes over 50 percent), a ranked
list three times the full target per type, min 40/40/40, and full 70/40/40 as the min plus
the first 30 SMC over sample sites in order.

Sampling language: the sample is selected, sites are selected sites. Config keys and
function names that already carried another word keep it.
"""
from __future__ import annotations

import copy
import math
import shutil
import subprocess
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from src import strata
from src.io import project_root
from src.layers import (arcpy_available, is_arcgis_path, read_layer, read_raster,
                        read_raster_attribute_table, resolve_source)

M2_PER_ACRE = 4046.8564224
TYPE_CODE = {"JP": 1, "SMC": 2, "RF": 3}
CODE_TYPE = {v: k for k, v in TYPE_CODE.items()}
SERAL_LABEL = {1: "early", 2: "mid", 3: "late"}
VP9_CLASSES = ["early", "mid_open", "mid_closed", "late_open", "late_closed"]


# --------------------------------------------------------------------------- discovery

def walk_sde(connection: str, keywords: Iterable[str], datatypes=("FeatureClass", "RasterDataset", "Table")) -> pd.DataFrame:
    """
    Walk an .sde connection (or a gdb) with arcpy.da.Walk and list every dataset and
    class whose name contains one of the keywords (case insensitive). Read only.
    Returns columns: dataset, name, path, matched. Requires arcpy.
    """
    import arcpy
    kws = [k.lower() for k in keywords]
    rows = []
    for dirpath, dirnames, filenames in arcpy.da.Walk(connection, datatype=list(datatypes)):
        rel = str(dirpath)[len(str(connection)):].strip("\\/")
        for name in list(dirnames) + list(filenames):
            hit = [k for k in kws if k in name.lower() or k in rel.lower()]
            if hit:
                rows.append({"dataset": rel, "name": name, "path": f"{dirpath}\\{name}", "matched": ",".join(hit)})
    return pd.DataFrame(rows, columns=["dataset", "name", "path", "matched"]).drop_duplicates("path").sort_values(["dataset", "name"]).reset_index(drop=True)


def source_status(cfg: dict, keys: Iterable[str] | None = None, check_arcpy: bool | None = None) -> pd.DataFrame:
    """
    One row per form of every `sources:` entry: key, form, path, status. Files are
    checked with Path.exists, arcpy paths with arcpy.Exists when arcpy is importable,
    URLs are not contacted. `picked` marks the form resolve_source would read.
    """
    check_arcpy = arcpy_available() if check_arcpy is None else check_arcpy
    if check_arcpy:
        import arcpy
    rows = []
    for key, entry in cfg["sources"].items():
        if keys is not None and key not in keys:
            continue
        forms = {k: v for k, v in entry.items() if k in ("rrk", "lidar", "sde", "file")} if isinstance(entry, dict) else {"path": entry}
        try:
            picked, _ = resolve_source(entry, cfg)
        except ValueError:
            picked = None
        for form, path in forms.items():
            p = str(path)
            if p.lower().startswith("http"):
                status = "url, not checked"
            elif is_arcgis_path(p):
                status = ("found" if arcpy.Exists(p) else "missing") if check_arcpy else "arcpy path, not checked (no arcpy)"
            else:
                status = "found" if (project_root() / p).exists() else "missing"
            rows.append({"key": key, "form": form, "path": p, "status": status, "picked": p == picked,
                         "confirm": "CONFIRM" if (form == "sde" and status == "missing") else ""})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- synthetic Basin

def _smooth_noise(rng: np.random.Generator, shape: tuple, sigma: float) -> np.ndarray:
    from scipy.ndimage import gaussian_filter
    z = gaussian_filter(rng.standard_normal(shape), sigma)
    return (z - z.mean()) / z.std()


def make_synthetic_sources(cfg: dict, seed: int = 1, n: int = 1100, src_epsg: int = 3310) -> dict:
    """
    A toy Basin in the shape the real sources take: 30 m rasters on one grid in the
    strata CRS (California Teale Albers by default, so the reprojection to the working
    CRS is exercised) and vector layers in the working CRS.

    The veg raster has NoData under the urban polygons, like veg_type_nonurban, and its
    conifer types are assigned so the acres by TRPA type equal report Table 1 before any
    other exclusion. The Wilderness polygon overlaps about one percent of the frame, so
    both readings of the Wilderness question pass the population check here. Everything
    else (seral, cover, TPA, BA, terrain, roads, parcels, plots) is invented and means
    nothing beyond exercising the code.

    Returns {"crs": str, "transform": Affine, "rasters": {key: array}, "rat": DataFrame,
             "layers": {key: GeoDataFrame in the working CRS}}.
    """
    import geopandas as gpd
    from pyproj import Transformer
    from rasterio.transform import from_origin
    from shapely.geometry import LineString, Point, Polygon, box
    from shapely import affinity

    rng = np.random.default_rng(seed)
    g = float(cfg["crs"]["lidar_grid_m"])
    wcrs = cfg["crs"]["working"]
    scrs = f"EPSG:{src_epsg}"
    # centre the toy Basin on the real one so coordinates look right in both CRSs
    cx, cy = Transformer.from_crs("EPSG:4326", scrs, always_xy=True).transform(-120.03, 39.09)
    cx, cy = math.floor(cx / g) * g, math.floor(cy / g) * g
    half = n * g / 2
    transform = from_origin(cx - half, cy + half, g, g)
    rows, cols = np.mgrid[0:n, 0:n]
    X = cx - half + (cols + 0.5) * g
    Y = cy + half - (rows + 0.5) * g
    R = half * 0.97
    r_norm = np.hypot((X - cx) / (R * 1.0), (Y - cy) / (R * 0.90))     # ellipse, 1.0 at the rim
    inside = r_norm <= 1.0
    lake = np.hypot(X - cx, Y - cy) <= 0.33 * R

    # terrain: lake at 1897 m, rim about 2800 m, ridges from noise
    dem = 1897.0 + 900.0 * np.clip(r_norm, 0, 1.15) ** 1.6 + 70.0 * _smooth_noise(rng, (n, n), 9) + 10.0 * _smooth_noise(rng, (n, n), 2)
    dem[lake] = 1897.0

    # urban: a shore band on the south and north east, cut out of the veg raster
    urban_polys = [affinity.rotate(box(cx - 0.42 * R, cy - 0.50 * R, cx + 0.05 * R, cy - 0.38 * R), 5, origin=(cx, cy)),
                   affinity.rotate(box(cx + 0.30 * R, cy + 0.20 * R, cx + 0.48 * R, cy + 0.38 * R), -10, origin=(cx, cy))]
    from rasterio import features
    urban = features.rasterize(((p, 1) for p in urban_polys), out_shape=(n, n), transform=transform, fill=0).astype(bool)
    land = inside & ~lake & ~urban

    # forest types so acres by type match report Table 1: RF highest, JP east and low, SMC the rest
    pop = cfg["forest_types"]["population_acres"]
    px = {t: int(round(a * M2_PER_ACRE / (g * g))) for t, a in pop.items()}
    noise = _smooth_noise(rng, (n, n), 25)
    veg = np.zeros((n, n), dtype=np.int16)                     # 0 = NoData (urban, lake, outside)
    codes = {"SMC": 1, "LPN": 2, "WFR": 3, "RFR": 4, "JPN": 5, "EPN": 6, "JUN": 7, "SCN": 8, "MCP": 9, "BAR": 10, "ASP": 11}
    idx = np.flatnonzero(land)
    score_rf = (dem.ravel()[idx] + 60 * noise.ravel()[idx])
    rf = idx[np.argsort(-score_rf)[:px["RF"]]]
    rest = np.setdiff1d(idx, rf)
    score_jp = (X.ravel()[rest] - cx) / R - 0.35 * (dem.ravel()[rest] - 1897) / 900 + 0.25 * noise.ravel()[rest]
    jp = rest[np.argsort(-score_jp)[:px["JP"]]]
    rest = np.setdiff1d(rest, jp)
    smc = rest[np.argsort(-noise.ravel()[rest])[:px["SMC"]]]
    other = np.setdiff1d(rest, smc)
    sub = rng.random(len(smc))
    veg.ravel()[smc] = np.where(sub < 0.786, codes["SMC"], np.where(sub < 0.917, codes["LPN"], codes["WFR"]))
    veg.ravel()[rf] = codes["RFR"]
    sub = rng.random(len(jp))
    veg.ravel()[jp] = np.where(sub < 0.944, codes["JPN"], np.where(sub < 0.9995, codes["EPN"], codes["JUN"]))
    sub = rng.random(len(other))
    veg.ravel()[other] = np.where(dem.ravel()[other] > 2550, codes["SCN"], np.where(sub < 0.6, codes["MCP"], np.where(sub < 0.9, codes["BAR"], codes["ASP"])))
    names = {"SMC": ("Sierran Mixed Conifer", "Conifer Forest"), "LPN": ("Lodgepole Pine", "Conifer Forest"), "WFR": ("White Fir", "Conifer Forest"),
             "RFR": ("Red Fir", "Conifer Forest"), "JPN": ("Jeffrey Pine", "Conifer Forest"), "EPN": ("Eastside Pine", "Conifer Forest"),
             "JUN": ("Juniper", "Conifer Woodland"), "SCN": ("Subalpine Conifer", "Conifer Forest"), "MCP": ("Montane Chaparral", "Shrub"),
             "BAR": ("Barren", "Barren"), "ASP": ("Aspen", "Hardwood Forest")}
    vals, counts = np.unique(veg[veg > 0], return_counts=True)
    inv = {v: k for k, v in codes.items()}
    rat = pd.DataFrame({"Value": vals, "Count": counts, "WHRTYPE": [inv[v] for v in vals]})
    rat["WHRNAME"] = rat["WHRTYPE"].map(lambda t: names[t][0])
    rat["WHR13NAME"] = rat["WHRTYPE"].map(lambda t: names[t][1])

    # structure: seral by a smooth field, cover by seral and noise, TPA and BA, and the 0/1 assessment
    conifer = veg > 0
    z = _smooth_noise(rng, (n, n), 8) + 0.3 * (dem - 1897) / 900
    seral = np.where(z < -1.85, 1, np.where(z < 0.25, 2, 3)).astype(np.int16)
    seral[~conifer] = 0
    cover = np.clip(18 + 18 * seral + 14 * _smooth_noise(rng, (n, n), 5) + 8 * _smooth_noise(rng, (n, n), 1.5), 0, 96)
    cover[~conifer] = np.nan
    tpa = np.clip(rng.gamma(3.0, 45.0, (n, n)) * (1.6 - 0.3 * seral) + 40 * _smooth_noise(rng, (n, n), 6), 3, 1500)
    ba = np.clip(0.55 * tpa * (0.6 + 0.4 * seral) * rng.uniform(0.7, 1.3, (n, n)) + 10 * seral, 2, 500)
    tpa[~conifer] = np.nan
    ba[~conifer] = np.nan
    type_code = forest_type_array(veg, rat, cfg["tessellation"]["whr_to_type"])
    exceeds = np.zeros((n, n), dtype=np.int16)
    th = cfg["threshold"]
    for t, code in TYPE_CODE.items():
        for s in (1, 2, 3):
            m = (type_code == code) & (seral == s)
            exceeds[m] = ((tpa[m] >= th["tpa_max"][t][s - 1]) & (ba[m] >= th["ba_max"][t][s - 1])).astype(np.int16)
    assessment = np.where(conifer & (seral > 0), exceeds, -1).astype(np.int16)   # -1 stands in for NoData

    # vector layers, built in the raster CRS then handed over in the working CRS
    def ring(r, k=64):
        return Polygon([(cx + r * math.cos(2 * math.pi * i / k), cy + 0.90 * r * math.sin(2 * math.pi * i / k)) for i in range(k)])
    boundary = gpd.GeoDataFrame({"NAME": ["TRPA"]}, geometry=[ring(R)], crs=scrs)
    lake_g = gpd.GeoDataFrame({"NAME": ["Lake Tahoe"]}, geometry=[Point(cx, cy).buffer(0.33 * R)], crs=scrs)
    urban_g = gpd.GeoDataFrame({"Description": ["Residential", "Tourist"]}, geometry=urban_polys, crs=scrs)
    wild = affinity.rotate(box(cx - 0.86 * R, cy - 0.02 * R, cx - 0.72 * R, cy + 0.14 * R), 15, origin=(cx, cy))
    wilderness = gpd.GeoDataFrame({"Description": ["Wilderness"]}, geometry=[wild], crs=scrs)
    mgmt = gpd.GeoDataFrame({"ZONE_NAME": ["West", "East"]},
                            geometry=[box(cx - R, cy - R, cx, cy + R), box(cx, cy - R, cx + R, cy + R)], crs=scrs)
    roads = [ring(0.40 * R).exterior] + [LineString([(cx + 0.40 * R * math.cos(a), cy + 0.34 * R * math.sin(a)),
                                                     (cx + 1.05 * R * math.cos(a), cy + 0.9 * R * math.sin(a))]) for a in np.linspace(0, 2 * math.pi, 9)[:-1]]
    roads_g = gpd.GeoDataFrame({"ROAD_TYPE": ["paved"] * len(roads)}, geometry=roads, crs=scrs)
    trails = [LineString([(cx + 0.42 * R * math.cos(a), cy + 0.36 * R * math.sin(a)), (cx + 0.95 * R * math.cos(a + 0.3), cy + 0.8 * R * math.sin(a + 0.3))])
              for a in np.linspace(0.2, 2 * math.pi + 0.2, 13)[:-1]]
    trails_g = gpd.GeoDataFrame({"TRAIL": ["t"] * len(trails)}, geometry=trails, crs=scrs)
    streams = [LineString([(cx + 0.36 * R * math.cos(a), cy + 0.31 * R * math.sin(a)), (cx + 0.9 * R * math.cos(a + 0.15), cy + 0.77 * R * math.sin(a + 0.15))])
               for a in np.linspace(0.1, 2 * math.pi + 0.1, 21)[:-1]]
    streams_g = gpd.GeoDataFrame({"NAME": ["s"] * len(streams)}, geometry=streams, crs=scrs)
    sx = rng.uniform(cx - 0.9 * R, cx + 0.9 * R, 400); sy = rng.uniform(cy - 0.75 * R, cy + 0.75 * R, 400)
    structures_g = gpd.GeoDataFrame({"TYPE": ["bldg"] * 400}, geometry=[Point(x, y).buffer(12, cap_style=3) for x, y in zip(sx, sy)], crs=scrs)
    pc = []
    for i in range(-6, 7):
        for j in range(-6, 7):
            pc.append(affinity.rotate(box(cx + i * 0.16 * R, cy + j * 0.14 * R, cx + (i + 1) * 0.16 * R, cy + (j + 1) * 0.14 * R), 7, origin=(cx, cy)))
    parcels_g = gpd.GeoDataFrame({"APN": [f"{k:04d}" for k in range(len(pc))]}, geometry=pc, crs=scrs)
    # Ownership/MapServer/0 shape: OWNERSHIP_TYPE in Federal, State, Local, Private. One private strip plus scattered
    # private inholdings exercise the public frame cut and the private edge buffer.
    owners = ["Federal", "State", "Federal", "Local", "Private"]
    own_polys = [affinity.rotate(box(cx + (k - 2.5) * 0.4 * R, cy - R, cx + (k - 1.5) * 0.4 * R, cy + R), -20, origin=(cx, cy)) for k in range(5)]
    inholdings = [Point(cx + rng.uniform(-0.8, 0.8) * R, cy + rng.uniform(-0.7, 0.7) * R).buffer(rng.uniform(150, 450), cap_style=3) for _ in range(25)]
    holes = gpd.GeoSeries(inholdings, crs=scrs).union_all()
    ownership_g = gpd.GeoDataFrame({"OWNERSHIP_TYPE": owners + ["Private"] * len(inholdings)},
                                   geometry=[p.difference(holes) for p in own_polys] + inholdings, crs=scrs)
    states_g = gpd.GeoDataFrame({"STUSPS": ["CA", "NV"]},
                                geometry=[box(cx - 1.2 * R, cy - 1.2 * R, cx + 0.30 * R, cy + 1.2 * R), box(cx + 0.30 * R, cy - 1.2 * R, cx + 1.2 * R, cy + 1.2 * R)], crs=scrs)
    fire_g = gpd.GeoDataFrame({"FIRE_NAME": ["Angora", "Caldor"], "YEAR": [2007, 2021]},
                              geometry=[Point(cx - 0.45 * R, cy - 0.55 * R).buffer(0.12 * R), Point(cx - 0.55 * R, cy - 0.75 * R).buffer(0.16 * R)], crs=scrs)
    trt_g = gpd.GeoDataFrame({"UNIT": ["A", "B", "C"], "YEAR": [2027, 2028, 2030]},
                             geometry=[Point(cx + 0.55 * R, cy - 0.45 * R).buffer(0.10 * R), Point(cx - 0.35 * R, cy + 0.55 * R).buffer(0.09 * R),
                                       Point(cx + 0.62 * R, cy + 0.55 * R).buffer(0.08 * R)], crs=scrs)
    fx, fy = np.nonzero(conifer)
    pick = rng.choice(len(fx), 40, replace=False)
    ltw_g = gpd.GeoDataFrame({"PLOT": [f"LTW{k:03d}" for k in range(40)], "qmd_in": rng.uniform(4, 30, 40)},
                             geometry=[Point(X[fx[k], fy[k]] + rng.uniform(-10, 10), Y[fx[k], fy[k]] + rng.uniform(-10, 10)) for k in pick], crs=scrs)
    fire_union = fire_g.union_all()
    bp = []
    while len(bp) < 15:
        p = Point(rng.uniform(cx - 0.75 * R, cx - 0.3 * R), rng.uniform(cy - 0.9 * R, cy - 0.4 * R))
        if fire_union.contains(p):
            bp.append(p)
    burn_g = gpd.GeoDataFrame({"PLOT": [f"HS{k:02d}" for k in range(15)]}, geometry=bp, crs=scrs)

    layers = {"boundary": boundary, "water": lake_g, "urban_boundary": urban_g, "wilderness": wilderness, "mgmt_zone": mgmt,
              "roads": roads_g, "trails": trails_g, "streams": streams_g, "structures": structures_g, "parcels": parcels_g,
              "ownership": ownership_g, "state_line": states_g, "fire_severity": fire_g, "treatments_2027_2031": trt_g,
              "ltw_plots": ltw_g, "burn_plots": burn_g}
    layers = {k: v.to_crs(wcrs) for k, v in layers.items()}
    rasters = {"veg_type": veg, "rrk_seral": seral, "rrk_cover": cover, "rrk_tpa": tpa, "rrk_ba": ba,
               "rrk_density_assessment": assessment, "dem": dem,
               # lidar stand-ins on the same grid, so strata.source: lidar also runs here
               "p95_height_30m": np.where(conifer, np.clip(4 + 9 * seral + 4 * _smooth_noise(rng, (n, n), 4), 1, 60), np.nan),
               "canopy_cover_30m": cover, "stem_density_30m": np.where(conifer, tpa * rng.uniform(0.5, 0.9, (n, n)), np.nan)}
    return {"crs": scrs, "transform": transform, "rasters": rasters, "rat": rat, "layers": layers,
            "nodata": {"veg_type": 0, "rrk_seral": 0, "rrk_density_assessment": -1}}


# --------------------------------------------------------------------------- one door to every source

class SourceReader:
    """
    Reads config sources the same way whether the run is real or synthetic, so a
    notebook section has one code path.

        reader.raster(key, form=None)        (array, transform, crs); NoData as NaN
        reader.raster_on_grid(key, template) the DEM, projected and snapped to the strata grid
        reader.rat(key)                      raster attribute table (Value, Count, WHRTYPE, ...)
        reader.layer(key, form=None)         GeoDataFrame in the working CRS
        reader.option(key, name)             a config option such as `field` or `where`
        reader.available(key)                True when the picked form exists

    Real reads go through src.layers (arcpy for .sde and .gdb, rasterio for files,
    requests for REST). `scratch_gdb` is where raster_on_grid writes its projected copy.
    """

    def __init__(self, cfg: dict, log=None, synthetic: bool | None = None, scratch_gdb: str | None = None, seed: int = 1):
        self.cfg = cfg
        self.log = log
        self.synthetic = bool(cfg["run"]["synthetic"]) if synthetic is None else synthetic
        self.scratch_gdb = scratch_gdb
        self.syn = make_synthetic_sources(cfg, seed=seed) if self.synthetic else None
        self._cache: dict = {}

    # -- lookup ------------------------------------------------------------

    def path(self, key: str, form: str | None = None) -> str:
        return resolve_source(self.cfg["sources"][key], self.cfg, prefer=form)[0]

    def option(self, key: str, name: str, default=None):
        entry = self.cfg["sources"][key]
        return entry.get(name, default) if isinstance(entry, dict) else default

    def available(self, key: str, form: str | None = None) -> bool:
        if self.synthetic:
            return key in self.syn["rasters"] or key in self.syn["layers"]
        try:
            p = self.path(key, form)
        except (KeyError, ValueError):
            return False
        if p.lower().startswith("http"):
            return True
        if is_arcgis_path(p):
            if not arcpy_available():
                return False
            import arcpy
            return bool(arcpy.Exists(p))
        return (project_root() / p).exists()

    # -- rasters -----------------------------------------------------------

    def raster(self, key: str, form: str | None = None):
        """(array as float with NaN for NoData, transform, crs) for a config raster."""
        ck = (key, form)
        if ck in self._cache:
            return self._cache[ck]
        if self.synthetic:
            if key not in self.syn["rasters"]:
                raise KeyError(f"synthetic Basin has no raster for {key}")
            arr = self.syn["rasters"][key].astype("float64")
            nd = self.syn["nodata"].get(key)
            if nd is not None:
                arr[arr == nd] = np.nan
            from rasterio.crs import CRS
            out = (arr, self.syn["transform"], CRS.from_user_input(self.syn["crs"]))
        else:
            out = read_raster(self.cfg["sources"][key], self.cfg, log=self.log, nodata_to_nan=True, prefer=form)
        self._cache[ck] = out
        return out

    def raster_on_grid(self, key: str, template_key: str = "veg_type", form: str | None = None, resampling: str = "BILINEAR"):
        """
        A raster projected, resampled, and snapped to the template raster's grid, read
        as (array, transform, crs). Real runs use arcpy ProjectRaster into the scratch
        gdb (this is how the 0.7 m SDE bare earth becomes a 30 m elevation grid); the
        synthetic Basin already sits on the grid.
        """
        if self.synthetic:
            return self.raster(key)
        import arcpy
        src = self.path(key, form)
        tpl = self.path(template_key, form)
        if self.scratch_gdb is None:
            raise ValueError("raster_on_grid needs scratch_gdb (arcpy.env.workspace)")
        out = f"{self.scratch_gdb}/{key}_on_grid"
        d = arcpy.Describe(tpl)
        with arcpy.EnvManager(snapRaster=tpl, extent=tpl, cellSize=tpl, outputCoordinateSystem=d.spatialReference):
            arcpy.management.ProjectRaster(src, out, d.spatialReference, resampling, d.meanCellWidth)
        if self.log:
            self.log.info(f"{key}: projected and snapped to {Path(tpl).name} ({d.spatialReference.name}, {d.meanCellWidth} m) -> {out}")
        return read_raster(out, self.cfg, log=self.log, nodata_to_nan=True)

    def rat(self, key: str = "veg_type", form: str | None = None) -> pd.DataFrame:
        if self.synthetic:
            return self.syn["rat"].copy()
        return read_raster_attribute_table(self.cfg["sources"][key], self.cfg, prefer=form, log=self.log)

    # -- vectors -----------------------------------------------------------

    def layer(self, key: str, form: str | None = None, where: str = "1=1"):
        if self.synthetic:
            if key not in self.syn["layers"]:
                raise KeyError(f"synthetic Basin has no layer for {key}")
            return self.syn["layers"][key].copy()
        return read_layer(self.cfg["sources"][key], self.cfg, where=where, log=self.log, prefer=form)


# --------------------------------------------------------------------------- frame

def forest_type_array(veg: np.ndarray, rat: pd.DataFrame, whr_to_type: dict) -> np.ndarray:
    """Raster values to TRPA type codes (1 JP, 2 SMC, 3 RF, 0 outside the frame) through the attribute table's WHRTYPE."""
    lut = {int(v): TYPE_CODE.get(whr_to_type.get(str(w).strip(), ""), 0) for v, w in zip(rat["Value"], rat["WHRTYPE"])}
    out = np.zeros(veg.shape, dtype=np.int16)
    v = np.nan_to_num(veg, nan=0).astype(np.int64)
    for val, code in lut.items():
        if code:
            out[v == val] = code
    return out


def whrtype_array(veg: np.ndarray, rat: pd.DataFrame) -> np.ndarray:
    """Raster values to WHRTYPE strings (empty outside)."""
    lut = {int(v): str(w) for v, w in zip(rat["Value"], rat["WHRTYPE"])}
    v = np.nan_to_num(veg, nan=0).astype(np.int64)
    out = np.full(veg.shape, "", dtype=object)
    for val, w in lut.items():
        out[v == val] = w
    return out


def rasterize_mask(gdfs, transform, shape: tuple, crs, buffer_m: float = 0.0, boundary_only: bool = False) -> np.ndarray:
    """
    Boolean mask of the pixels covered by any geometry in the given GeoDataFrames,
    reprojected to the raster CRS, optionally buffered (metres), optionally using only
    polygon boundaries (parcel edges). Empty input gives an all False mask.
    """
    import geopandas as gpd
    from rasterio import features
    geoms = []
    for gdf in ([gdfs] if not isinstance(gdfs, (list, tuple)) else gdfs):
        if gdf is None or len(gdf) == 0:
            continue
        g = gdf.to_crs(crs).geometry
        if boundary_only:
            g = g.boundary
        if buffer_m:
            g = g.buffer(buffer_m)
        geoms.extend([geom for geom in g if geom is not None and not geom.is_empty])
    if not geoms:
        return np.zeros(shape, dtype=bool)
    return features.rasterize(((geom, 1) for geom in geoms), out_shape=shape, transform=transform, fill=0, all_touched=False).astype(bool)


def rasterize_category(gdf, field: str, transform, shape: tuple, crs) -> tuple[np.ndarray, dict]:
    """Integer raster of a categorical field (0 = none) plus the {code: value} lookup."""
    from rasterio import features
    if gdf is None or len(gdf) == 0 or field not in gdf:
        return np.zeros(shape, dtype=np.int32), {}
    g = gdf.to_crs(crs)
    cats = {v: i + 1 for i, v in enumerate(sorted(g[field].dropna().astype(str).unique()))}
    shapes = ((geom, cats[str(v)]) for geom, v in zip(g.geometry, g[field]) if geom is not None and pd.notna(v))
    arr = features.rasterize(shapes, out_shape=shape, transform=transform, fill=0).astype(np.int32)
    return arr, {i: v for v, i in cats.items()}


def terrain(dem: np.ndarray, cell_m: float) -> tuple[np.ndarray, np.ndarray]:
    """Slope (percent) and aspect (degrees clockwise from north) from a DEM on a square grid; NaN where the DEM is NaN."""
    d = np.where(np.isnan(dem), np.nanmean(dem), dem)
    dy, dx = np.gradient(d, cell_m)
    slope = 100.0 * np.hypot(dx, dy)
    aspect = (np.degrees(np.arctan2(dx, -dy)) + 360.0) % 360.0    # dy is northward decrease of row index
    slope[np.isnan(dem)] = np.nan
    aspect[np.isnan(dem)] = np.nan
    return slope, aspect


def population_check(acres_by_type: dict, report_acres: dict, tol_pct: float) -> tuple[pd.DataFrame, bool]:
    """Acres by type against report Table 1; ok is False when the total is off by more than tol_pct."""
    rows = []
    for t, rep in report_acres.items():
        a = float(acres_by_type.get(t, 0.0))
        rows.append({"forest_type": t, "acres": round(a), "report_acres": rep, "diff_pct": round(100 * (a - rep) / rep, 2)})
    tot, rep = sum(acres_by_type.get(t, 0.0) for t in report_acres), sum(report_acres.values())
    rows.append({"forest_type": "total", "acres": round(tot), "report_acres": rep, "diff_pct": round(100 * (tot - rep) / rep, 2)})
    df = pd.DataFrame(rows)
    return df, abs(df.iloc[-1]["diff_pct"]) <= tol_pct


def build_units(inpop: np.ndarray, type_code: np.ndarray, k: int, min_unit_fraction: float, transform) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Lay k by k blocks anchored at the raster origin over the population mask and keep a
    block when its centre pixel is in the population and at least min_unit_fraction of
    its pixels are. Returns (units table, block rows, block cols). Uses strata.block_reduce.
    """
    import rasterio
    frac = strata.block_reduce(inpop.astype(float), k, "mean")
    centre_type = strata.block_reduce(type_code.astype(float), k, "center")
    centre_in = strata.block_reduce(inpop.astype(float), k, "center")
    keep = (centre_in > 0) & (frac >= min_unit_fraction) & (centre_type > 0)
    bi, bj = np.nonzero(keep)
    rows, cols = bi * k + k // 2, bj * k + k // 2
    xs, ys = rasterio.transform.xy(transform, rows, cols)
    cell = abs(transform.a)
    unit_ac = (k * cell) ** 2 / M2_PER_ACRE
    units = pd.DataFrame({"unit_id": bi * keep.shape[1] + bj, "unit_row": bi, "unit_col": bj,
                          "x_src": np.asarray(xs, float), "y_src": np.asarray(ys, float),
                          "forest_type": [CODE_TYPE[int(c)] for c in centre_type[bi, bj]],
                          "unit_frac_in_frame": frac[bi, bj], "unit_acres": unit_ac})
    units["acres"] = units["unit_frac_in_frame"] * unit_ac
    return units, bi, bj


def sample_units(arr: np.ndarray, inpop: np.ndarray, k: int, bi: np.ndarray, bj: np.ndarray, how: str = "mean") -> np.ndarray:
    """Block statistic over population pixels ("mean") or the centre pixel value ("center") for every kept unit."""
    a = np.where(inpop, arr, np.nan) if how == "mean" else arr
    red = strata.block_reduce(a.astype(float), k, how)
    return red[bi, bj]


def to_working_crs(units: pd.DataFrame, src_crs, wcrs: str) -> pd.DataFrame:
    """Add x, y in the working CRS next to x_src, y_src in the raster CRS."""
    from pyproj import Transformer
    t = Transformer.from_crs(src_crs, wcrs, always_xy=True)
    x, y = t.transform(units["x_src"].to_numpy(), units["y_src"].to_numpy())
    out = units.copy()
    out["x"], out["y"] = x, y
    return out


def units_as_points(units: pd.DataFrame, wcrs: str):
    import geopandas as gpd
    return gpd.GeoDataFrame(units, geometry=gpd.points_from_xy(units["x"], units["y"]), crs=wcrs)


# --------------------------------------------------------------------------- strata

def strata_config_for_source(cfg: dict) -> dict:
    """
    The config strata.classify_cells should bin with, for the chosen strata.source.

    lidar: unchanged (p95 height at strata.height_breaks_m, stem density at
           strata.density_breaks, strata.density_classes).
    rrk:   the seral proxy column carries the RRK seral code (1, 2, 3), so the breaks are
           1.5 and 2.5; the density proxy column carries the stand density assessment
           (0 at or below the maxima, 1 exceeds), so there are two classes split at 0.5,
           labelled low and high. Nothing in strata.py changes.
    """
    out = copy.deepcopy(cfg)
    if str(cfg["strata"]["source"]).lower() == "rrk":
        types = list(cfg["forest_types"]["population_acres"])
        out["strata"]["height_breaks_m"] = {t: [1.5, 2.5] for t in types}
        out["strata"]["density_breaks"] = {t: [0.5, 0.5] for t in types}
        out["strata"]["density_classes"] = 2
    return out


def proxy_columns(frame: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """
    Fill p95_height_m, stem_density, and canopy_cover_pct, the columns
    strata.classify_cells reads, from the columns of the chosen source.
    """
    out = frame.copy()
    if str(cfg["strata"]["source"]).lower() == "rrk":
        out["p95_height_m"] = out["rrk_seral"]
        out["stem_density"] = out["rrk_density_exceeds"]
        out["canopy_cover_pct"] = out["rrk_cover_pct"]
    else:
        need = [c for c in ("p95_height_m", "stem_density", "canopy_cover_pct") if c not in out]
        if need:
            raise KeyError(f"strata.source is lidar but the frame has no {need}; sample the lidar rasters in section 2")
    return out


def elevation_band(elev_m, edges: Iterable[float]) -> np.ndarray:
    """Band label from elevation and ascending edges: e1 for below the first edge, e2, ..."""
    edges = list(edges)
    idx = np.searchsorted(np.asarray(edges, float), np.asarray(elev_m, float), side="right")
    return np.array([f"e{i + 1}" for i in idx], dtype=object)


# --------------------------------------------------------------------------- access

def hike_distance_m(road_mask: np.ndarray, dem: np.ndarray, cell_m: float, slope_cost: bool = True, log=None) -> np.ndarray:
    """
    Distance in metres from every pixel to the nearest drivable road pixel along the
    cheapest path over the grid (8 neighbours). With slope_cost the cost of crossing a
    pixel is its surface distance factor, sqrt(1 + slope^2), so a steep approach counts
    longer than its map distance; NaN in the DEM (the lake, outside the Basin) is
    impassable. Uses scikit-image's MCP_Geometric; when scikit-image is missing it falls
    back to planar Euclidean distance and logs a warning, because that understates steep
    approaches and moves sites toward lower access classes.
    """
    if not road_mask.any():
        if log:
            log.warning("no drivable road pixels; hike distance is undefined (NaN)")
        return np.full(road_mask.shape, np.nan)
    try:
        from skimage.graph import MCP_Geometric
    except ImportError:
        from scipy.ndimage import distance_transform_edt
        if log:
            log.warning("scikit-image not installed; access classes use planar distance. conda install -n arcgispro-py3 scikit-image")
        return distance_transform_edt(~road_mask) * cell_m
    blocked = np.isnan(dem)
    if slope_cost:
        slope, _ = terrain(dem, cell_m)
        cost = np.sqrt(1.0 + (np.nan_to_num(slope, nan=0.0) / 100.0) ** 2)
    else:
        cost = np.ones(dem.shape)
    cost = np.where(blocked & ~road_mask, np.inf, cost)
    starts = np.argwhere(road_mask)
    mcp = MCP_Geometric(cost, fully_connected=True)
    cum, _ = mcp.find_costs(starts)
    out = cum * cell_m
    out[~np.isfinite(out)] = np.nan
    return out


def access_class_mi(hike_m, breaks_mi: Iterable[float]) -> np.ndarray:
    """Access class 1, 2, 3, ... from hike distance in metres and ascending breaks in miles; NaN distance gets the last class."""
    edges = np.asarray(list(breaks_mi), float) * 1609.344
    d = np.asarray(hike_m, float)
    cls = np.searchsorted(edges, np.nan_to_num(d, nan=np.inf), side="right") + 1
    return cls.astype(int)


# --------------------------------------------------------------------------- design (Oct 19 2026)

def inclusion_multiplier(frame: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """
    Relative inclusion probability within forest type, the aux variable spsurvey's
    proportional selection reads: tail_multiplier where f"{seral_class}_{density_class}"
    is in weights.tail_cells, times steep_multiplier where the centre slope exceeds
    weights.slope_break_pct. Adds is_tail, is_steep, and mult.
    """
    w = cfg["weights"]
    out = frame.copy()
    key = out["seral_class"].astype(str) + "_" + out["density_class"].astype(str)
    out["is_tail"] = key.isin(w["tail_cells"])
    out["is_steep"] = out["slope_pct"].fillna(0) > float(w["slope_break_pct"])
    out["mult"] = np.where(out["is_tail"], float(w["tail_multiplier"]), 1.0) * np.where(out["is_steep"], float(w["steep_multiplier"]), 1.0)
    return out


def selection_targets(cfg: dict) -> pd.DataFrame:
    """
    One row per forest type: n_min, n_full, list_len (backup_multiple x n_full), and the
    spsurvey arguments n_base (= n_min) and n_over (= list_len - n_min). The full level is
    the min level plus the first n_full - n_min over sample sites in order.
    """
    a = cfg["allocation"]
    rows = []
    for t in cfg["forest_types"]["population_acres"]:
        n_min, n_full = int(a["n_by_type"]["min"][t]), int(a["n_by_type"]["full"][t])
        if n_full < n_min:
            raise ValueError(f"{t}: full ({n_full}) is below min ({n_min}); the full level must contain the min level")
        list_len = int(a["backup_multiple"]) * n_full
        rows.append({"forest_type": t, "n_min": n_min, "n_full": n_full, "list_len": list_len,
                     "n_base": n_min, "n_over": list_len - n_min})
    out = pd.DataFrame(rows)
    for lvl in ("min", "full"):
        tot = int(out[f"n_{lvl}"].sum())
        if tot != int(a["levels"][lvl]):
            raise ValueError(f"allocation.n_by_type.{lvl} sums to {tot}, allocation.levels.{lvl} says {a['levels'][lvl]}")
    return out


def design_ip(frame: pd.DataFrame, n_by_type: dict, mult_col: str = "mult") -> pd.Series:
    """First order inclusion probability of every unit for n plots per type: n_t x mult / sum(mult in type)."""
    tot = frame.groupby("forest_type")[mult_col].transform("sum")
    n = frame["forest_type"].map(n_by_type).astype(float)
    return n * frame[mult_col] / tot


def expected_counts(frame: pd.DataFrame, n_by_type: dict, by: list[str], mult_col: str = "mult") -> pd.Series:
    """Expected sample count per group under the design: the sum of inclusion probabilities over the group's units."""
    return frame.assign(_ip=design_ip(frame, n_by_type, mult_col)).groupby(by)["_ip"].sum().rename("n_expected")


# --------------------------------------------------------------------------- selection

def write_selection_inputs(frame: pd.DataFrame, targets: pd.DataFrame, cfg: dict, processed: Path, log=None) -> dict:
    """The two files scripts/grts_select.R reads: frame_points.gpkg and selection_targets.csv. Returns their paths."""
    import geopandas as gpd
    wcrs = cfg["crs"]["working"]
    processed.mkdir(parents=True, exist_ok=True)
    keep = [c for c in ["unit_id", "forest_type", "mult", "basin_side", "tpi_class", "x", "y"] if c in frame]
    pts = gpd.GeoDataFrame(frame[keep].copy(), geometry=gpd.points_from_xy(frame["x"], frame["y"]), crs=wcrs)
    paths = {"frame_points": processed / "frame_points.gpkg", "selection_targets": processed / "selection_targets.csv"}
    pts.to_file(paths["frame_points"], driver="GPKG")
    targets[["forest_type", "n_base", "n_over"]].to_csv(paths["selection_targets"], index=False)
    if log:
        log.info(f"selection inputs: {len(pts):,} units; n_base {targets.set_index('forest_type')['n_base'].to_dict()}, "
                 f"n_over {targets.set_index('forest_type')['n_over'].to_dict()} -> {processed}")
    return paths


def run_rscript(cfg: dict, script: str, args: list, cwd: Path, log=None) -> subprocess.CompletedProcess | None:
    """Run an R script through run.rscript. Returns None when Rscript is not on the machine."""
    rscript = str(cfg["run"].get("rscript", "Rscript"))
    exe = shutil.which(rscript) or (rscript if Path(rscript).exists() else None)
    if exe is None:
        if log:
            log.warning(f"Rscript not found ({rscript}); set run.rscript to the R 4.x Rscript path")
        return None
    cmd = [exe, str(script)] + [str(a) for a in args]
    if log:
        log.info("running " + " ".join(cmd))
    res = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if log:
        for line in (res.stdout + res.stderr).strip().splitlines()[-30:]:
            log.info(f"R | {line}")
        if res.returncode:
            log.error(f"Rscript exited {res.returncode}")
    return res


def python_selection(frame: pd.DataFrame, targets: pd.DataFrame, cfg: dict, log=None) -> pd.DataFrame:
    """
    The same design with strata.grts_draw, for iteration or when R is absent: stratified
    by forest type, unequal probability on mult, a ranked list of list_len sites per type.
    Returns unit rows with stratum, status (base or over), and grts_rank within type.
    Not the frozen selection.
    """
    d = cfg["draw"]
    fa = frame.assign(cell_id=frame["forest_type"])
    t = targets.set_index("forest_type")
    factor = float((t["list_len"] / t["n_base"]).max())
    sel = strata.grts_draw(fa, t["n_base"].to_dict(), fa["mult"], seed=int(d["seed"]), oversample_factor=factor,
                           legacy_mask=None, min_distance_m=float(d["min_distance_m"]))
    sel = sel[sel["grts_rank"] <= sel["cell_id"].map(t["list_len"])].copy()
    short = (sel.groupby("cell_id").size() - t["list_len"]).loc[lambda s: s < 0]
    if len(short) and log:
        log.warning(f"Python GRTS returned fewer sites than the list length for {short.to_dict()}")
    sel["stratum"] = sel["cell_id"]
    sel["status"] = np.where(sel["status"] == "primary", "base", "over")
    sel["ip"] = design_ip(frame, t["n_base"].to_dict()).reindex(sel.index).values
    sel["wgt"] = 1.0 / sel["ip"]
    return sel.drop(columns=["cell_id", "inclusion_weight"], errors="ignore").reset_index(drop=True)


def normalise_spsurvey_sites(sites, frame: pd.DataFrame) -> pd.DataFrame:
    """
    outputs/grts_select.gpkg (spsurvey) to the schema python_selection returns: unit_id,
    stratum, status (base or over), grts_rank within stratum (base first, then over, each in
    spsurvey's order), siteID, wgt, ip, plus every frame column joined back on unit_id.
    """
    s = pd.DataFrame(sites.drop(columns="geometry", errors="ignore"))
    s["status"] = s["siteuse"].str.lower().map({"base": "base", "over": "over"})
    s["_ord"] = np.arange(len(s))
    s["_b"] = (s["status"] != "base").astype(int)
    s = s.sort_values(["stratum", "_b", "_ord"])
    s["grts_rank"] = s.groupby("stratum").cumcount() + 1
    keep = [c for c in ["unit_id", "stratum", "status", "grts_rank", "siteID", "wgt", "ip"] if c in s]
    out = s[keep].merge(frame, on="unit_id", how="left", suffixes=("", "_frame"))
    return out.reset_index(drop=True)


def assign_levels(sel: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    """
    Level and order for every selected site, within forest type by grts_rank:
      rank 1 to n_min                      level "min"   (the RFP minimum)
      rank n_min + 1 to n_full             level "full"  (added when the full design is funded)
      rank above n_full                    level "backup", backup_order 1, 2, ... in rank order
    Backups replace a rejected site in order, starting at the first unused rank in the type:
    at the min level that is rank n_min + 1, so the full level's sites double as the min
    level's first backups. install_order interleaves types by rank so any prefix of the
    order is balanced across types and space; min sites come before full sites.
    """
    t = targets.set_index("forest_type")
    out = sel.copy()
    n_min = out["stratum"].map(t["n_min"])
    n_full = out["stratum"].map(t["n_full"])
    out["level"] = np.where(out["grts_rank"] <= n_min, "min", np.where(out["grts_rank"] <= n_full, "full", "backup"))
    out["backup_order"] = np.where(out["level"] == "backup", out["grts_rank"] - n_full, np.nan)
    prim = out[out["level"] != "backup"].sort_values(["level", "grts_rank", "stratum"], key=lambda c: c.map({"min": 0, "full": 1}) if c.name == "level" else c)
    out["install_order"] = np.nan
    out.loc[prim.index, "install_order"] = np.arange(1, len(prim) + 1)
    out["plot_id"] = "FH-" + out["stratum"].astype(str) + "-" + out["grts_rank"].astype(int).astype(str).str.zfill(3)
    return out.sort_values(["install_order", "stratum", "grts_rank"], na_position="last").reset_index(drop=True)


def to_markdown(df: pd.DataFrame) -> str:
    """A pipe table without the tabulate dependency (not in arcgispro-py3 by default)."""
    d = df.reset_index()
    head = "| " + " | ".join(str(c) for c in d.columns) + " |"
    rule = "|" + "|".join("---" for _ in d.columns) + "|"
    body = ["| " + " | ".join(str(v) for v in row) + " |" for row in d.itertuples(index=False)]
    return "\n".join([head, rule] + body)


def appendix_a_tables(sel: pd.DataFrame) -> dict:
    """
    RFP Appendix A: plots by forest type and access class, and by forest type and owner,
    at the min and full levels (cumulative), plus list depth per type. Coordinates are not
    in these tables; they are furnished at contract execution.
    """
    prim = sel[sel["level"].isin(["min", "full"])]
    out = {}
    for lvl, rows in (("min", prim[prim["level"] == "min"]), ("full", prim)):
        acc = pd.crosstab(rows["forest_type"], rows["access_class"], margins=True, margins_name="total")
        acc.columns = [f"class_{c}" if c != "total" else c for c in acc.columns]
        out[f"access_{lvl}"] = acc
        out[f"owner_{lvl}"] = pd.crosstab(rows["forest_type"], rows["owner"].fillna("unknown"), margins=True, margins_name="total")
    depth = sel.groupby(["forest_type", "level"]).size().unstack(fill_value=0)
    out["list_depth"] = depth.reindex(columns=[c for c in ["min", "full", "backup"] if c in depth.columns])
    return out


# --------------------------------------------------------------------------- evaluation

def spatial_balance(sample_xy: np.ndarray, frame_xy: np.ndarray, nq: int = 4) -> dict:
    """
    A crude spatial balance statistic when spsurvey's sp_balance is not available: the
    frame extent is cut into nq by nq quadrants, the expected sample per quadrant is
    proportional to the frame count there, and the statistic is the chi-square over
    occupied quadrants divided by its degrees of freedom (1 is what simple random
    sampling gives; a balanced sample sits well below 1).
    """
    if len(sample_xy) == 0 or len(frame_xy) == 0:
        return {"chi2_per_df": None, "quadrants": 0, "n": int(len(sample_xy))}
    xmin, ymin = frame_xy.min(axis=0)
    xmax, ymax = frame_xy.max(axis=0) + 1e-9
    def cellidx(xy):
        qx = np.clip(((xy[:, 0] - xmin) / (xmax - xmin) * nq).astype(int), 0, nq - 1)
        qy = np.clip(((xy[:, 1] - ymin) / (ymax - ymin) * nq).astype(int), 0, nq - 1)
        return qx * nq + qy
    fc = np.bincount(cellidx(np.asarray(frame_xy, float)), minlength=nq * nq)
    sc = np.bincount(cellidx(np.asarray(sample_xy, float)), minlength=nq * nq)
    n = len(sample_xy)
    exp = fc / fc.sum() * n
    occ = exp > 0
    chi2 = float(((sc[occ] - exp[occ]) ** 2 / exp[occ]).sum())
    df = int(occ.sum()) - 1
    return {"chi2_per_df": round(chi2 / df, 3) if df > 0 else None, "quadrants": int(occ.sum()), "n": int(n)}


def vp9_class(seral, cover_pct, forest_type, cutoffs: dict) -> np.ndarray:
    """VP9 class label from RRK seral code and cover: early, mid_open, mid_closed, late_open, late_closed."""
    s = np.asarray(seral, float)
    c = np.asarray(cover_pct, float)
    cut = np.array([cutoffs[t] for t in forest_type], float)
    closed = np.nan_to_num(c, nan=0.0) >= cut
    out = np.full(len(s), "", dtype=object)
    out[s == 1] = "early"
    out[(s == 2) & ~closed] = "mid_open"
    out[(s == 2) & closed] = "mid_closed"
    out[(s == 3) & ~closed] = "late_open"
    out[(s == 3) & closed] = "late_closed"
    return out


def vp10_class(seral, exceeds) -> np.ndarray:
    """VP10 class: seral stage crossed with the density assessment (meets or exceeds the maxima)."""
    s = np.asarray(seral, float)
    e = np.asarray(exceeds, float)
    lab = np.array([SERAL_LABEL.get(int(v), "") if not np.isnan(v) else "" for v in s], dtype=object)
    dens = np.where(np.isnan(e), "", np.where(e >= 0.5, "exceeds", "meets"))
    return np.array([f"{a}_{b}" if a and b else "" for a, b in zip(lab, dens)], dtype=object)


def coverage_table(frame: pd.DataFrame, sample: pd.DataFrame, col: str, by: str = "forest_type") -> pd.DataFrame:
    """Frame share and sample count of every class of `col` within `by`; empty classes show a zero."""
    f = frame.groupby([by, col])["acres"].sum().rename("frame_acres")
    fshare = (f / f.groupby(level=0).transform("sum") * 100).rename("frame_pct")
    s = sample.groupby([by, col]).size().rename("sample_n")
    out = pd.concat([f, fshare, s], axis=1).fillna({"sample_n": 0})
    out["sample_n"] = out["sample_n"].astype(int)
    return out.round(1)


# --------------------------------------------------------------------------- export

def hex_keys(x, y, cfg: dict, lattice_csv: Path | None = None, log=None) -> tuple[np.ndarray, np.ndarray, str]:
    """
    Owl (400 ha) and sample design (133 ha) hex cell keys for points in the working CRS,
    from the lattice 06_tessellation fitted (outputs/tessellation_lattice_parameters.csv).
    Without that file a placeholder lattice with the configured cell area is used and
    the returned source says so; keys from it do not match the delivered grid.
    Key format matches 06_tessellation: C+iiiii+jjjjj and TF+iiiii+jjjjj.
    """
    from src import tessellation as T
    tc = cfg["tessellation"]
    crs = f"EPSG:{int(tc['epsg'])}"
    src = "placeholder lattice (06_tessellation has not run)"
    lat = None
    if lattice_csv is not None and Path(lattice_csv).exists():
        rows = pd.read_csv(lattice_csv)
        r = rows.iloc[0]
        try:
            a1 = tuple(float(v) for v in str(r["a1"]).strip("()").split(","))
            a2 = tuple(float(v) for v in str(r["a2"]).strip("()").split(","))
            lat = T.Lattice(a1=a1, a2=a2, origin_x=float(r["origin_x"]), origin_y=float(r["origin_y"]), shape="hex", crs=crs)
            src = f"{lattice_csv}"
        except (KeyError, ValueError) as e:
            if log:
                log.warning(f"could not rebuild the lattice from {lattice_csv}: {e}")
    if lat is None:
        lat = T.Lattice.for_cell_area(float(tc["cell_area_ha"]), shape="hex", rotation_deg=float(tc["hex_orientation_deg"]),
                                      origin_x=0.0, origin_y=0.0, crs=crs)
    fine = T.fine_lattice(lat, int(tc["fine_ratio"]))
    xy = np.c_[np.asarray(x, float), np.asarray(y, float)]
    ij = np.round(lat.indices(xy)).astype(int)
    fij = np.round(fine.indices(xy)).astype(int)
    owl = np.array([f"C{i:+05d}{j:+05d}" for i, j in ij], dtype=object)
    fine_keys = np.array([f"{tc['fine_id_prefix']}{i:+05d}{j:+05d}" for i, j in fij], dtype=object)
    if log:
        log.info(f"hex keys from {src}")
    return owl, fine_keys, src
