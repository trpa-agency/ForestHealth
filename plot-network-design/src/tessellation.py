"""
src/tessellation.py

Tessellation utilities for the forest health plot network: fit the lattice of
an existing cell layer, regenerate and extend it, build new hexagonal or
square grids at a target cell size, evaluate candidate cell sizes against a
point pattern, and account for which cells a set of sites already occupies.

Three different questions get asked with the word "grid" and they have
different answers. Keep them apart:

  1. Display binning. What cell size shows the structure in a point pattern
     without being noisy or washed out. This is what ArcGIS Pro's Evaluate Bin
     Sizes for Point Aggregation answers, and what `evaluate_bin_sizes`
     reimplements so the result is reproducible outside Pro 3.6 and so the
     candidate sizes can be the ones the design cares about.

  2. Sampling frame cell size. What cell size, sampled at one point per cell,
     produces the sample size and spatial coverage the program needs. That is
     a sample size question, answered in src/sample_size.py; the cell size
     follows from it. `cells_for_sample_size` inverts it.

  3. Reporting or stratum cell size. What cell size holds enough plots to
     report on, driven by the per stratum floors in src/sample_size.py.

A cell size that is right for one of these is usually wrong for the other two,
so notebooks/06_tessellation.ipynb reports all three side by side.

Lattice model
-------------
A cell lattice is two basis vectors and an origin: every cell centre sits at
origin + i * a1 + j * a2. A regular hexagonal grid has |a1| = |a2| and 60
degrees between them; a regular square grid has |a1| = |a2| at 90 degrees. A
grid that was generated in one projection and delivered in another is no
longer regular, but it is still affine, so `fit_lattice` fits the general
affine form by least squares and `build_lattice` reproduces it exactly. That
is what lets a partial grid, such as the California spotted owl grid, be
extended over Nevada without redrawing the part that already exists.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np
import pandas as pd

SQM_PER_ACRE = 4046.8564224
SQM_PER_HA = 10_000.0


# ---------------------------------------------------------------- geometry helpers


def hex_area_from_spacing(spacing_m: float) -> float:
    """Area of a regular hexagon whose flat to flat width (centre spacing) is `spacing_m`."""
    return spacing_m ** 2 * math.sqrt(3) / 2.0


def hex_spacing_from_area(area_m2: float) -> float:
    """Centre to centre spacing of a regular hexagon of the given area."""
    return math.sqrt(2.0 * area_m2 / math.sqrt(3))


def hex_circumradius(spacing_m: float) -> float:
    """Centre to vertex distance for a regular hexagon of the given centre spacing."""
    return spacing_m / math.sqrt(3)


@dataclass(frozen=True)
class Lattice:
    """Cell lattice defined by two basis vectors and an origin, in a projected CRS.

    a1, a2      lattice vectors as (dx, dy) in metres
    origin_x/y  coordinates of the cell whose indices are (0, 0)
    shape       "hex" or "square"
    crs         the CRS the numbers are expressed in; nothing here is valid in
                any other CRS
    """

    a1: tuple[float, float]
    a2: tuple[float, float]
    origin_x: float
    origin_y: float
    shape: str = "hex"
    crs: str = "EPSG:3310"

    # -- constructors -------------------------------------------------

    @classmethod
    def regular(cls, spacing_m: float, rotation_deg: float = 0.0, origin_x: float = 0.0,
                origin_y: float = 0.0, shape: str = "hex", crs: str = "EPSG:3310") -> "Lattice":
        t = math.radians(rotation_deg)
        a1 = (spacing_m * math.cos(t), spacing_m * math.sin(t))
        step = math.pi / 3 if shape == "hex" else math.pi / 2
        a2 = (spacing_m * math.cos(t + step), spacing_m * math.sin(t + step))
        return cls(a1=a1, a2=a2, origin_x=origin_x, origin_y=origin_y, shape=shape, crs=crs)

    @classmethod
    def for_cell_area(cls, area_ha: float, shape: str = "hex", **kw) -> "Lattice":
        area = area_ha * SQM_PER_HA
        spacing = hex_spacing_from_area(area) if shape == "hex" else math.sqrt(area)
        return cls.regular(spacing_m=spacing, shape=shape, **kw)

    # -- derived quantities -------------------------------------------

    @property
    def M(self) -> np.ndarray:
        """Column matrix [a1 a2]; maps lattice indices to map coordinates."""
        return np.column_stack([np.asarray(self.a1, float), np.asarray(self.a2, float)])

    @property
    def cell_area_m2(self) -> float:
        return abs(float(np.linalg.det(self.M)))

    @property
    def cell_area_ha(self) -> float:
        return self.cell_area_m2 / SQM_PER_HA

    @property
    def cell_area_acres(self) -> float:
        return self.cell_area_m2 / SQM_PER_ACRE

    @property
    def spacing_m(self) -> float:
        """Mean centre to centre spacing; equals |a1| exactly when the lattice is regular."""
        return float((np.hypot(*self.a1) + np.hypot(*self.a2)) / 2)

    @property
    def rotation_deg(self) -> float:
        """Direction of a1, modulo 60 degrees for hex and 90 for square."""
        mod = 60.0 if self.shape == "hex" else 90.0
        return math.degrees(math.atan2(self.a1[1], self.a1[0])) % mod

    @property
    def anisotropy(self) -> float:
        """Departure from a regular lattice: 0.0 is regular, 0.01 is one percent off.

        Nonzero means the layer was generated in a different projection. The
        affine form still reproduces it; the number is here so the notebook can
        say so out loud rather than silently drawing slightly wrong cells.
        """
        l1, l2 = np.hypot(*self.a1), np.hypot(*self.a2)
        ang = abs(math.degrees(math.atan2(self.a2[1], self.a2[0]) - math.atan2(self.a1[1], self.a1[0])))
        target = 60.0 if self.shape == "hex" else 90.0
        return float(max(abs(l1 - l2) / max(l1, l2), abs(ang - target) / target))

    def summary(self) -> dict:
        return {
            "shape": self.shape, "crs": self.crs,
            "spacing_m": round(self.spacing_m, 3),
            "rotation_deg": round(self.rotation_deg, 5),
            "cell_area_ha": round(self.cell_area_ha, 3),
            "cell_area_acres": round(self.cell_area_acres, 2),
            "anisotropy": round(self.anisotropy, 6),
            "origin_x": round(self.origin_x, 3), "origin_y": round(self.origin_y, 3),
            "a1": (round(self.a1[0], 4), round(self.a1[1], 4)),
            "a2": (round(self.a2[0], 4), round(self.a2[1], 4)),
        }

    # -- index and coordinate conversion --------------------------------

    def centres(self, ij: np.ndarray) -> np.ndarray:
        return np.array([self.origin_x, self.origin_y]) + ij @ self.M.T

    def indices(self, xy: np.ndarray) -> np.ndarray:
        return (np.linalg.inv(self.M) @ (np.asarray(xy, float) - np.array([self.origin_x, self.origin_y])).T).T

    def cell_vertices(self, ij) -> np.ndarray:
        """Vertices of one cell, in map coordinates, ordered counterclockwise."""
        a1 = np.asarray(self.a1, float)
        a2 = np.asarray(self.a2, float)
        if self.shape == "hex":
            offs = [(a1 + a2) / 3, (2 * a2 - a1) / 3, (a2 - 2 * a1) / 3,
                    -(a1 + a2) / 3, (a1 - 2 * a2) / 3, (2 * a1 - a2) / 3]
        else:
            offs = [(-a1 - a2) / 2, (a1 - a2) / 2, (a1 + a2) / 2, (a2 - a1) / 2]
        c = self.centres(np.atleast_2d(np.asarray(ij, float)))[0]
        v = np.array([c + o for o in offs])
        ang = np.arctan2(v[:, 1] - c[1], v[:, 0] - c[0])
        return v[np.argsort(ang)]


def fit_lattice_xy(pts: np.ndarray, spacing_m: Optional[float] = None, area_m2: Optional[float] = None,
                   rotation_deg: float = 0.0, shape: str = "hex", crs: str = "EPSG:26910",
                   n_iter: int = 3) -> Lattice:
    """Fit a lattice to cell centres when the construction is already known.

    `pts` is an (n, 2) array of centre coordinates in `crs`. Give either the
    centre spacing or the cell area, plus the direction of the first lattice
    vector: 30 degrees for a flat-top hexagon grid such as ArcGIS
    GenerateTessellation produces, 0 for a pointy-top (transverse) one. The
    first point seeds the origin, every point is assigned integer indices, and
    a least squares solve for the affine map from indices to coordinates
    refines the basis and origin. No spatial library is needed, so this is the
    fit to use from arcpy: read the centres with a cursor and pass the array.

    Check `residuals_xy` afterwards. Millimetres means the layer is one exact
    lattice in `crs`; metres means it was built somewhere else and reprojected.
    """
    pts = np.asarray(pts, float)
    if pts.ndim != 2 or pts.shape[1] != 2 or len(pts) < 4:
        raise ValueError("pts must be an (n, 2) array with at least four centres")
    if spacing_m is None:
        if area_m2 is None:
            raise ValueError("give spacing_m or area_m2")
        spacing_m = hex_spacing_from_area(area_m2) if shape == "hex" else math.sqrt(area_m2)
    lat = Lattice.regular(spacing_m=spacing_m, rotation_deg=rotation_deg, origin_x=float(pts[0, 0]),
                          origin_y=float(pts[0, 1]), shape=shape, crs=crs)
    for _ in range(n_iter):
        ij = np.round(lat.indices(pts))
        A = np.c_[ij, np.ones(len(ij))]
        sol, *_ = np.linalg.lstsq(A, pts, rcond=None)
        lat = Lattice(a1=(float(sol[0][0]), float(sol[0][1])), a2=(float(sol[1][0]), float(sol[1][1])),
                      origin_x=float(sol[2][0]), origin_y=float(sol[2][1]), shape=shape, crs=crs)
    return lat


def residuals_xy(pts: np.ndarray, lat: Lattice) -> np.ndarray:
    """Distance in metres from each centre to the nearest lattice point of `lat`."""
    pts = np.asarray(pts, float)
    rebuilt = lat.centres(np.round(lat.indices(pts)))
    return np.hypot(*(pts - rebuilt).T)


def fit_lattice(gdf, shape: str = "hex", crs: str = "EPSG:3310", tol_frac: float = 0.05,
                refine: bool = True) -> Lattice:
    """Recover the lattice of an existing cell layer.

    A nearest neighbour pass gives the approximate spacing and orientation,
    cells are assigned integer indices from it, and a least squares solve for
    the affine map from indices to coordinates fixes the basis and origin.
    Check the fit with `regenerate_residuals` before extending anything: a
    median residual of a few metres means the lattice is recovered; tens of
    metres means the layer is not one lattice, usually because it was built in
    pieces or spans enough of the globe that one projection cannot hold it.
    Fit over a local subset in that case, which is all an extension needs.
    """
    from scipy.spatial import cKDTree

    g = gdf.to_crs(crs)
    cent = g.geometry if g.geom_type.iloc[0] == "Point" else g.geometry.centroid
    pts = np.c_[cent.x.values, cent.y.values]
    if len(pts) < 4:
        raise ValueError("need at least four cells to fit a lattice")

    tree = cKDTree(pts)
    k = min(7 if shape == "hex" else 5, len(pts))
    dist, idx = tree.query(pts, k=k)
    nn = float(np.median(dist[:, 1]))

    mod = 60.0 if shape == "hex" else 90.0
    vecs = []
    for c in range(1, k):
        keep = np.abs(dist[:, c] - nn) < tol_frac * nn
        if keep.any():
            vecs.append(pts[idx[keep, c]] - pts[keep])
    V = np.vstack(vecs)
    ang = np.degrees(np.arctan2(V[:, 1], V[:, 0])) % mod
    w = np.radians(ang * (360.0 / mod))
    rot = float((math.degrees(math.atan2(np.sin(w).mean(), np.cos(w).mean())) % 360) * (mod / 360.0))

    lat = Lattice.regular(spacing_m=nn, rotation_deg=rot, origin_x=float(pts[0, 0]),
                          origin_y=float(pts[0, 1]), shape=shape, crs=crs)
    if not refine:
        return lat

    for _ in range(3):
        ij = np.round(lat.indices(pts))
        A = np.c_[ij, np.ones(len(ij))]
        sol, *_ = np.linalg.lstsq(A, pts, rcond=None)
        lat = Lattice(a1=tuple(sol[0]), a2=tuple(sol[1]),
                      origin_x=float(sol[2][0]), origin_y=float(sol[2][1]), shape=shape, crs=crs)
    return lat


def regenerate_residuals(gdf, lat: Lattice) -> pd.Series:
    """Distance from each original cell centre to the nearest regenerated centre, in metres."""
    g = gdf.to_crs(lat.crs)
    cent = g.geometry if g.geom_type.iloc[0] == "Point" else g.geometry.centroid
    pts = np.c_[cent.x.values, cent.y.values]
    rebuilt = lat.centres(np.round(lat.indices(pts)))
    return pd.Series(np.hypot(*(pts - rebuilt).T), name="residual_m")


def build_lattice(lat: Lattice, boundary, pad_cells: int = 1, id_prefix: str = "C",
                  min_overlap_frac: float = 0.0):
    """Generate every cell of `lat` that intersects `boundary`.

    `boundary` is a shapely geometry or a GeoDataFrame in any CRS. Returns a
    GeoDataFrame in `lat.crs` carrying the lattice indices i and j, the centre
    coordinates as x_coord and y_coord (matching the owl grid schema), the cell area, the fraction of the cell inside the boundary,
    and a deterministic `cell_key` from the indices, so the same lattice always
    gives the same key for the same ground position.

    `min_overlap_frac` drops slivers along the boundary: 0.0 keeps every cell
    that touches, 0.5 keeps cells at least half inside.
    """
    import geopandas as gpd
    from shapely.geometry import Polygon

    geom = boundary.to_crs(lat.crs).union_all() if hasattr(boundary, "geometry") else boundary
    minx, miny, maxx, maxy = geom.bounds
    corners = np.array([[minx, miny], [maxx, miny], [minx, maxy], [maxx, maxy]])
    ij = lat.indices(corners)
    i0, i1 = int(np.floor(ij[:, 0].min())) - pad_cells, int(np.ceil(ij[:, 0].max())) + pad_cells
    j0, j1 = int(np.floor(ij[:, 1].min())) - pad_cells, int(np.ceil(ij[:, 1].max())) + pad_cells

    I, J = np.meshgrid(np.arange(i0, i1 + 1), np.arange(j0, j1 + 1))
    IJ = np.c_[I.ravel(), J.ravel()]
    C = lat.centres(IJ)
    pad = lat.spacing_m
    keep = (C[:, 0] > minx - pad) & (C[:, 0] < maxx + pad) & (C[:, 1] > miny - pad) & (C[:, 1] < maxy + pad)
    IJ, C = IJ[keep], C[keep]

    a1 = np.asarray(lat.a1, float)
    a2 = np.asarray(lat.a2, float)
    if lat.shape == "hex":
        offs = np.array([(a1 + a2) / 3, (2 * a2 - a1) / 3, (a2 - 2 * a1) / 3,
                         -(a1 + a2) / 3, (a1 - 2 * a2) / 3, (2 * a1 - a2) / 3])
    else:
        offs = np.array([(-a1 - a2) / 2, (a1 - a2) / 2, (a1 + a2) / 2, (a2 - a1) / 2])
    ang = np.arctan2(offs[:, 1], offs[:, 0])
    offs = offs[np.argsort(ang)]

    polys = [Polygon(c + offs) for c in C]
    out = gpd.GeoDataFrame({"i": IJ[:, 0], "j": IJ[:, 1], "x_coord": C[:, 0], "y_coord": C[:, 1]},
                           geometry=polys, crs=lat.crs)
    out = out[out.intersects(geom)].reset_index(drop=True)
    out["cell_area_ha"] = out.geometry.area / SQM_PER_HA
    out["inside_frac"] = out.geometry.intersection(geom).area / out.geometry.area
    if min_overlap_frac > 0:
        out = out[out.inside_frac >= min_overlap_frac].reset_index(drop=True)
    out["cell_key"] = [f"{id_prefix}{i:+06d}{j:+06d}" for i, j in zip(out.i, out.j)]
    return out


def match_existing(new_cells, old_cells, lat: Lattice, old_id_field: str = "cell_id",
                   tol_m: Optional[float] = None):
    """Carry original cell ids onto a regenerated grid and flag which cells are new.

    Cells whose centre falls within `tol_m` (default a tenth of the spacing) of
    an original cell centre keep the original id and are marked
    `source = "existing"`. Everything else is `"new"`, which is the count that
    answers how much of a grid an extension actually adds.
    """
    from scipy.spatial import cKDTree

    tol = tol_m if tol_m is not None else lat.spacing_m / 10.0
    old = old_cells.to_crs(lat.crs)
    oc = old.geometry if old.geom_type.iloc[0] == "Point" else old.geometry.centroid
    tree = cKDTree(np.c_[oc.x.values, oc.y.values])
    d, i = tree.query(np.c_[new_cells["x_coord"].values, new_cells["y_coord"].values], k=1)
    hit = d < tol
    out = new_cells.copy()
    ids = np.asarray(old[old_id_field].values, dtype=object)[i]
    out[old_id_field] = np.where(hit, ids, None)
    out["source"] = np.where(hit, "existing", "new")
    out["match_dist_m"] = np.where(hit, d, np.nan)
    return out


# ---------------------------------------------------------------- occupancy


def occupancy(cells, points, group_field: Optional[str] = None, cell_key: str = "cell_key"):
    """Count points per cell, optionally split by a grouping field.

    Returns (cells_with_counts, summary). The summary counts how many cells
    hold 0, 1, 2, ... points, which is what decides how many new sites a one
    point per cell design has to add, and reports how many points fell outside
    every cell.
    """
    import geopandas as gpd

    pts = points.to_crs(cells.crs)
    j = gpd.sjoin(pts, cells[[cell_key, "geometry"]], how="left", predicate="within")
    out = cells.merge(j.groupby(cell_key).size().rename("n_points"),
                      left_on=cell_key, right_index=True, how="left")
    out["n_points"] = out["n_points"].fillna(0).astype(int)
    if group_field is not None:
        wide = j.pivot_table(index=cell_key, columns=group_field, aggfunc="size", fill_value=0)
        wide.columns = [f"n_{c}" for c in wide.columns]
        out = out.merge(wide, left_on=cell_key, right_index=True, how="left")
        for c in wide.columns:
            out[c] = out[c].fillna(0).astype(int)
    summary = out["n_points"].value_counts().sort_index().rename("cells").to_frame()
    summary.index.name = "points_in_cell"
    summary.attrs["unmatched_points"] = int(j[cell_key].isna().sum())
    return out, summary


def cells_for_sample_size(frame_area_ha: float, n_target: int, shape: str = "hex") -> dict:
    """Invert the sampling question: what cell size puts `n_target` cells on the frame.

    One point per cell is the usual systematic design, so the cell count is the
    sample size and the cell size is a consequence of it, not a free choice.
    """
    area = frame_area_ha * SQM_PER_HA / n_target
    spacing = hex_spacing_from_area(area) if shape == "hex" else math.sqrt(area)
    return {"n_cells": n_target, "cell_area_ha": area / SQM_PER_HA,
            "cell_area_acres": area / SQM_PER_ACRE, "spacing_m": spacing, "shape": shape}


def nested_lattice(lat: Lattice, ratio: int) -> Lattice:
    """A coarser hex lattice sharing lattice points with `lat`, `ratio` times the cell area.

    Hexagons do not subdivide into hexagons, so "nested hex grids" never nest as
    exact unions of child cells. What does hold, and what a design actually
    needs, is that the centres nest: at area ratios 3, 4, 7, 9, 12 and 13 there
    is a coarser hex lattice every one of whose centres is also a centre of the
    finer lattice. Sample points therefore nest exactly and the two grids never
    drift, even though cell boundaries cut across each other.

    Pass 1 / ratio via `fine_lattice` for the opposite direction.
    """
    turn = {1: 0.0, 3: 30.0, 4: 0.0, 7: 19.106605, 9: 0.0, 12: 30.0, 13: 13.897886}
    if ratio not in turn:
        raise ValueError(f"ratio {ratio} does not admit a hex superlattice; use 3, 4, 7, 9, 12 or 13")
    return Lattice.regular(spacing_m=lat.spacing_m * math.sqrt(ratio),
                           rotation_deg=lat.rotation_deg + turn[ratio],
                           origin_x=lat.origin_x, origin_y=lat.origin_y,
                           shape="hex", crs=lat.crs)


def fine_lattice(lat: Lattice, ratio: int) -> Lattice:
    """A finer hex lattice sharing lattice points with `lat`, one `ratio`th of the cell area."""
    turn = {1: 0.0, 3: 30.0, 4: 0.0, 7: 19.106605, 9: 0.0, 12: 30.0, 13: 13.897886}
    if ratio not in turn:
        raise ValueError(f"ratio {ratio} does not admit a hex sublattice; use 3, 4, 7, 9, 12 or 13")
    return Lattice.regular(spacing_m=lat.spacing_m / math.sqrt(ratio),
                           rotation_deg=lat.rotation_deg - turn[ratio],
                           origin_x=lat.origin_x, origin_y=lat.origin_y,
                           shape="hex", crs=lat.crs)


# ---------------------------------------------------------------- bin size evaluation


def _internal_uniformity(cells, xy: np.ndarray, cell_index: np.ndarray, n_sub: int = 4) -> tuple[float, float]:
    """Proportion of occupied cells whose points pass a within cell randomness test.

    Each occupied cell's bounding box is split into an n_sub by n_sub grid and
    a chi square goodness of fit against a uniform expectation is run on cells
    holding enough points to support the test; cells with too few points count
    as passing. Bigger cells contain more internal structure, so this falls as
    cell size grows. This is the criterion that prefers small cells.
    """
    from scipy.stats import chisquare

    if len(cell_index) == 0:
        return float("nan"), 0.0
    bounds = cells.geometry.bounds.values
    order = np.argsort(cell_index, kind="stable")
    ci, pxy = cell_index[order], xy[order]
    edges = np.searchsorted(ci, np.arange(len(cells) + 1))
    tested = passed = testable = 0
    for c in range(len(cells)):
        s, e = edges[c], edges[c + 1]
        n = e - s
        if n == 0:
            continue
        tested += 1
        if n < 2 * n_sub * n_sub:
            passed += 1
            continue
        testable += 1
        minx, miny, maxx, maxy = bounds[c]
        gx = np.clip(((pxy[s:e, 0] - minx) / (maxx - minx) * n_sub).astype(int), 0, n_sub - 1)
        gy = np.clip(((pxy[s:e, 1] - miny) / (maxy - miny) * n_sub).astype(int), 0, n_sub - 1)
        obs = np.bincount(gy * n_sub + gx, minlength=n_sub * n_sub)
        if chisquare(obs).pvalue > 0.05:
            passed += 1
    return (passed / tested if tested else float("nan"),
            testable / tested if tested else 0.0)


def _count_variety(counts: np.ndarray) -> float:
    """Normalised Shannon entropy of the distribution of per cell counts, 0 to 1.

    Computed over the frequency of each distinct count value. A grid where
    every cell holds the same number of points scores 0; a grid with a wide,
    even spread of counts scores near 1. Very small cells are nearly all empty
    or hold exactly one point, so this criterion prefers larger cells.
    """
    vals, freq = np.unique(counts, return_counts=True)
    if len(vals) < 2:
        return 0.0
    p = freq / freq.sum()
    return float(-(p * np.log(p)).sum() / math.log(len(vals)))


def evaluate_bin_sizes(points, boundary, shape: str = "hex", crs: str = "EPSG:3310",
                       spacings_m: Optional[Sequence[float]] = None, n_candidates: int = 20,
                       rotation_deg: float = 0.0, n_boot: int = 200, seed: int = 42,
                       log=None) -> pd.DataFrame:
    """Score candidate cell sizes against a point pattern.

    Reimplements the two criteria behind ArcGIS Pro's Evaluate Bin Sizes for
    Point Aggregation so the result is reproducible here, on any Pro version,
    over candidate sizes chosen by the design rather than by the tool's
    automatic sweep:

        internal_uniformity  proportion of occupied cells whose points are
                             indistinguishable from randomness inside the cell
                             (prefers small cells)
        count_variety        normalised Shannon entropy of per cell counts
                             (prefers large cells)
        score                the product of the two

    Also returns the quantities that score ignores and a sampling design needs:
    cell count, percent empty, and mean count in occupied cells. Read those
    next to the score. A size that maximises the score can still put too few
    cells on the frame to sample from, and the bootstrap interval says how many
    other sizes are statistically indistinguishable from the best, which is
    usually a wide range and is the honest answer to "is this the right scale".
    """
    import geopandas as gpd

    rng = np.random.default_rng(seed)
    pts = points.to_crs(crs)[["geometry"]].reset_index(drop=True)
    bnd = boundary.to_crs(crs).union_all() if hasattr(boundary, "geometry") else boundary
    minx, miny, maxx, maxy = bnd.bounds

    if spacings_m is None:
        lo = hex_spacing_from_area(bnd.area / (20.0 * max(len(pts), 1)))
        hi = 0.25 * max(maxx - minx, maxy - miny)
        spacings_m = np.geomspace(lo, hi, n_candidates)

    rows = []
    for s in spacings_m:
        lat = Lattice.regular(spacing_m=float(s), rotation_deg=rotation_deg,
                              origin_x=float(minx), origin_y=float(miny), shape=shape, crs=crs)
        cells = build_lattice(lat, bnd)
        if len(cells) < 4:
            continue
        j = gpd.sjoin(pts, cells[["geometry"]], how="inner", predicate="within")
        idx = j.index_right.values
        counts = np.bincount(idx, minlength=len(cells))
        iu, testable = _internal_uniformity(cells, np.c_[j.geometry.x.values, j.geometry.y.values], idx)
        cv = _count_variety(counts)
        boot = [iu * _count_variety(counts[rng.integers(0, len(counts), len(counts))]) for _ in range(n_boot)]
        rows.append({
            "spacing_m": float(s),
            "cell_area_ha": lat.cell_area_ha,
            "cell_area_acres": lat.cell_area_acres,
            "n_cells": int(len(cells)),
            "pct_empty": 100.0 * float((counts == 0).mean()),
            "mean_count_occupied": float(counts[counts > 0].mean()) if (counts > 0).any() else 0.0,
            "internal_uniformity": iu,
            "uniformity_testable": testable,
            "count_variety": cv,
            "score": iu * cv,
            "score_lo": float(np.percentile(boot, 2.5)),
            "score_hi": float(np.percentile(boot, 97.5)),
        })
        if log:
            log.info(f"spacing {s:8.0f} m  {lat.cell_area_ha:9.1f} ha  cells {len(cells):7d}  score {iu * cv:.3f}")

    df = pd.DataFrame(rows)
    if len(df) and (df["uniformity_testable"] < 0.05).all():
        msg = ("internal_uniformity is untestable at every candidate size: the point pattern is too "
               "sparse for a within cell randomness test, so the score reduces to count_variety, "
               "which always prefers the largest cell. Treat the recommendation as uninformative and "
               "use a dense point pattern (TAO tops, EcObject centroids) or the sample size criterion.")
        if log:
            log.warning(msg)
        else:
            import warnings; warnings.warn(msg)
    if len(df):
        best = df.loc[df.score.idxmax()]
        df["recommended"] = df.spacing_m == best.spacing_m
        df["within_ci_of_best"] = df.score >= best.score_lo
    return df
