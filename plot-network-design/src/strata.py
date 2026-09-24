"""
src/strata.py — helpers for the plot network design.

Kept deliberately linear and small. The notebooks carry the flow; these are
the pieces that get reused across notebooks:

    classify_cells()        assign forest type, seral proxy, density proxy, cover class, cell id
    collapse_small_cells()  merge cells below a minimum area within forest type
    allocate()              nested allocation (Candidate A proportional, Candidate B tail-boosted floor)
    grts_draw()             compact GRTS: hierarchical addressing, reverse hierarchical order,
                            systematic selection with unequal inclusion probabilities
    installation_order()    round-robin interleave across cells so any prefix is balanced
    access_class()          Class 1-4 from distance to road and slope
    make_synthetic_frame()  toy Basin so the whole chain runs before real layers exist
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify_cells(frame: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """
    Add seral_class, density_class, cover_class, and cell_id to a frame table.

    Expects columns: forest_type (SMC / RF / JP), p95_height_m, stem_density,
    canopy_cover_pct. Breaks come from config; per-type.
    """
    st = cfg["strata"]
    th = cfg["threshold"]
    labels = st["class_labels"]
    out = frame.copy()

    out["seral_class"] = "mid"
    out["density_class"] = "moderate"
    out["cover_class"] = "open"

    for ftype in out["forest_type"].unique():
        m = out["forest_type"] == ftype

        hb = st["height_breaks_m"][ftype]
        out.loc[m, "seral_class"] = pd.cut(
            out.loc[m, "p95_height_m"], [-np.inf, hb[0], hb[1], np.inf],
            labels=labels["seral"], right=False,
        ).astype(str)

        db = st["density_breaks"][ftype]
        if st["density_classes"] == 3:
            out.loc[m, "density_class"] = pd.cut(
                out.loc[m, "stem_density"], [-np.inf, db[0], db[1], np.inf],
                labels=labels["density"], right=False,
            ).astype(str)
        else:
            out.loc[m, "density_class"] = np.where(
                out.loc[m, "stem_density"] < db[1], "low", "high"
            )

        oc = th["cover_open_closed_pct"][ftype]
        out.loc[m, "cover_class"] = pd.cut(
            out.loc[m, "canopy_cover_pct"], [-np.inf, th["cover_sparse_pct"], oc, np.inf],
            labels=labels["cover"], right=False,
        ).astype(str)

    parts = [out["forest_type"], out["seral_class"], out["density_class"]]
    if st["use_cover_axis"]:
        parts.append(out["cover_class"])
    out["cell_id"] = parts[0].str.cat(parts[1:], sep="_")
    return out


def collapse_small_cells(frame: pd.DataFrame, cfg: dict, log=None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Merge cells below strata.min_cell_acres into the nearest populated cell
    within the same forest type (nearest in seral, then density order).
    Returns (frame with cell_id updated, collapse log table).
    """
    min_ac = cfg["strata"]["min_cell_acres"]
    labels = cfg["strata"]["class_labels"]
    seral_rank = {s: i for i, s in enumerate(labels["seral"])}
    dens_rank = {d: i for i, d in enumerate(labels["density"])}

    out = frame.copy()
    out["cell_orig"] = out["cell_id"]
    acres = out.groupby("cell_id")["acres"].sum()
    small = acres[acres < min_ac].index.tolist()
    rows = []

    for cell in small:
        ftype, seral, dens = cell.split("_")[:3]
        candidates = acres[(acres.index.str.startswith(ftype + "_")) & (acres >= min_ac)]
        if candidates.empty:
            continue
        # distance in class space: seral steps count double
        def dist(c):
            _, s2, d2 = c.split("_")[:3]
            return 2 * abs(seral_rank[seral] - seral_rank[s2]) + abs(dens_rank[dens] - dens_rank[d2])
        target = min(candidates.index, key=dist)
        t_ftype, t_seral, t_dens = target.split("_")[:3]
        m = out["cell_id"] == cell
        out.loc[m, ["cell_id", "seral_class", "density_class"]] = [target, t_seral, t_dens]
        rows.append({"from_cell": cell, "acres": float(acres[cell]), "to_cell": target})
        if log:
            log.info(f"Collapsed {cell} ({acres[cell]:,.0f} ac) into {target}")

    return out, pd.DataFrame(rows, columns=["from_cell", "acres", "to_cell"])


# ---------------------------------------------------------------------------
# Allocation
# ---------------------------------------------------------------------------

def _largest_remainder(targets: pd.Series, n: int) -> pd.Series:
    """Round a vector of real-valued targets to integers summing to n."""
    base = np.floor(targets).astype(int)
    remainder = n - int(base.sum())
    if remainder > 0:
        frac = (targets - base).sort_values(ascending=False)
        for idx in frac.index[:remainder]:
            base[idx] += 1
    return base


def allocate(cell_acres: pd.DataFrame, cfg: dict, level: str) -> pd.DataFrame:
    """
    Allocate n plots (allocation.levels[level]) across cells.

    cell_acres: DataFrame with columns cell_id, forest_type, seral_class,
                density_class, acres (one row per populated cell).
    Returns the table with columns n_A (proportional) and n_B (tail-boosted floor).
    """
    al = cfg["allocation"]
    n = al["levels"][level]
    floor = al["floor_per_cell"][level]
    tab = cell_acres.copy().set_index("cell_id")

    # Candidate A: proportional to cell area, floor of 1 so no populated cell is empty at any level
    prop = tab["acres"] / tab["acres"].sum() * n
    tab["n_A"] = _largest_remainder(prop.clip(lower=1.0), n)

    # Candidate B: floor per cell, then type shares, then seral x density shares within type, tail boost
    tab["n_B"] = floor
    remaining = n - int(tab["n_B"].sum())
    if remaining < 0:
        raise ValueError(f"{level}: floor {floor} x {len(tab)} cells exceeds n={n}; collapse cells or lower floor")

    target = pd.Series(0.0, index=tab.index)
    for ftype, share in al["type_shares"].items():
        cells = tab[tab["forest_type"] == ftype]
        if cells.empty:
            continue
        w = pd.Series(
            [al["seral_shares"][r.seral_class] * al["density_shares"][r.density_class]
             for r in cells.itertuples()],
            index=cells.index,
        )
        for cell in cells.index:
            key = f"{tab.loc[cell, 'seral_class']}_{tab.loc[cell, 'density_class']}"
            if key in al["tail_cells"]:
                w[cell] *= al["tail_boost"]
        target[cells.index] = w / w.sum() * share * remaining

    tab["n_B"] += _largest_remainder(target * (remaining / target.sum()), remaining)

    tab["acres_per_plot_A"] = tab["acres"] / tab["n_A"].replace(0, np.nan)
    tab["acres_per_plot_B"] = tab["acres"] / tab["n_B"].replace(0, np.nan)
    tab["level"] = level
    return tab.reset_index()


def apply_nevada_floor(alloc: pd.DataFrame, cell_state_acres: pd.DataFrame, cfg: dict, col: str = "n_B") -> pd.DataFrame:
    """
    Report (not enforce) whether the per-type Nevada floor is likely met, given
    the NV share of each cell's area. Enforcement happens at draw time via
    inclusion probabilities; this just flags types that need attention.
    """
    nv = cell_state_acres[cell_state_acres["state"] == "NV"].groupby("cell_id")["acres"].sum()
    tot = cell_state_acres.groupby("cell_id")["acres"].sum()
    share = (nv / tot).reindex(alloc["cell_id"]).fillna(0).values
    alloc = alloc.copy()
    alloc["expected_nv_plots"] = alloc[col] * share
    by_type = alloc.groupby("forest_type")["expected_nv_plots"].sum()
    floors = cfg["allocation"]["nevada_floor"]
    alloc["nv_floor_ok"] = alloc["forest_type"].map(lambda t: by_type.get(t, 0) >= floors.get(t, 0))
    return alloc


# ---------------------------------------------------------------------------
# GRTS (compact Python version; frozen draw uses spsurvey in scripts/grts_draw.R)
# ---------------------------------------------------------------------------

def _hierarchical_address(x: np.ndarray, y: np.ndarray, levels: int, rng: np.random.Generator) -> np.ndarray:
    """
    Quadrant address for each point with a random permutation of the four
    quadrants at every level (the GRTS randomization). Returns an integer rank.
    """
    xmin, xmax = x.min(), x.max() + 1e-9
    ymin, ymax = y.min(), y.max() + 1e-9
    side = max(xmax - xmin, ymax - ymin)
    fx = (x - xmin) / side
    fy = (y - ymin) / side
    rank = np.zeros(len(x), dtype=np.int64)
    for _ in range(levels):
        fx *= 2
        fy *= 2
        qx = np.floor(fx).astype(int)
        qy = np.floor(fy).astype(int)
        fx -= qx
        fy -= qy
        quad = qx + 2 * qy                     # 0..3
        perm = rng.permutation(4)
        rank = rank * 4 + perm[quad]
    return rank


def _reverse_hierarchical_order(rank: np.ndarray, levels: int) -> np.ndarray:
    """Reverse the base-4 digits of the address so the ordering is spatially balanced."""
    rev = np.zeros_like(rank)
    r = rank.copy()
    for _ in range(levels):
        rev = rev * 4 + (r % 4)
        r //= 4
    return rev


def enforce_min_distance(points: pd.DataFrame, min_distance_m: float, keep_first: pd.Series | None = None) -> pd.Series:
    """
    Greedy pass in row order: a row is kept unless it is within min_distance_m of a
    row already kept. Rows flagged in keep_first (legacy sites) are kept unconditionally
    and considered first. Returns a boolean Series aligned to points.
    """
    if min_distance_m <= 0 or len(points) == 0:
        return pd.Series(True, index=points.index)
    first = (pd.Series(False, index=points.index) if keep_first is None
             else keep_first.reindex(points.index).fillna(False).astype(bool))
    order = points.index[first.values].append(points.index[~first.values])
    xy = points.loc[order, ["x", "y"]].to_numpy(float)
    kept = np.zeros(len(order), dtype=bool)
    for i in range(len(order)):
        if first.loc[order[i]]:
            kept[i] = True
            continue
        prev = xy[:i][kept[:i]]
        kept[i] = len(prev) == 0 or bool(np.hypot(prev[:, 0] - xy[i, 0], prev[:, 1] - xy[i, 1]).min() >= min_distance_m)
    return pd.Series(kept, index=order).reindex(points.index)


def grts_draw(points: pd.DataFrame, n_by_cell: dict, inclusion_weight: pd.Series | None,
              seed: int, oversample_factor: float = 2.0, levels: int = 12,
              legacy_mask: pd.Series | None = None, min_distance_m: float = 0.0) -> pd.DataFrame:
    """
    Spatially balanced draw within each cell.

    points:           DataFrame with x, y, cell_id (one row per candidate sampling unit,
                      a unit_px x unit_px block of LiDAR pixels with the plot on its centre)
    n_by_cell:        {cell_id: n primary}
    inclusion_weight: optional per-row relative inclusion probability (tail boost,
                      disturbance targeting, representativeness); None = equal
    legacy_mask:      optional boolean Series; True rows are existing plots that are
                      included first and count toward the cell's n
    min_distance_m:   minimum separation between any two selected sites across all cells
                      (spsurvey's mindis). Conflicting candidates are dropped in GRTS
                      order and the next candidate in the ordered line takes their place.
    Returns selected rows with columns: grts_rank, status (primary/backup/legacy).
    """
    rng = np.random.default_rng(seed)
    w = pd.Series(1.0, index=points.index) if inclusion_weight is None else inclusion_weight.astype(float)
    legacy = pd.Series(False, index=points.index) if legacy_mask is None else legacy_mask.astype(bool)

    picks, n_new_by_cell = [], {}
    for cell, n in n_by_cell.items():
        sub = points[points["cell_id"] == cell]
        if sub.empty or n <= 0:
            continue
        n_leg = int(legacy[sub.index].sum())
        n_new = max(n - n_leg, 0)
        n_new_by_cell[cell] = n_new
        # draw extra so the separation rule has candidates to fall back on
        n_total = int(np.ceil(n_new * oversample_factor * (1.5 if min_distance_m > 0 else 1.0)))

        cand = sub[~legacy[sub.index]]
        addr = _hierarchical_address(cand["x"].values, cand["y"].values, levels, rng)
        order = _reverse_hierarchical_order(addr, levels)
        cand = cand.assign(_ord=order, _w=w[cand.index].values).sort_values("_ord")

        # systematic selection along the ordered line, unequal probability
        p = cand["_w"].values / cand["_w"].sum() * n_total
        cum = np.cumsum(p)
        start = rng.uniform(0, 1)
        hits = np.floor(cum - start).astype(int)
        hits = np.diff(np.concatenate([[-1], hits]))
        chosen = cand[hits > 0].copy()
        chosen["grts_rank"] = np.arange(1, len(chosen) + 1)
        chosen["status"] = np.where(chosen["grts_rank"] <= n_new, "primary", "backup")

        leg = sub[legacy[sub.index]].copy()
        leg["grts_rank"] = 0
        leg["status"] = "legacy"
        picks.append(pd.concat([leg, chosen]))

    out = pd.concat(picks) if picks else points.iloc[0:0].copy()
    out = out.drop(columns=[c for c in ["_ord", "_w"] if c in out.columns])

    if min_distance_m > 0 and len(out):
        # Legacy sites first, then everything else in GRTS order; drop conflicts, then
        # re-rank within each cell so the next candidate steps up.
        pri = out["status"].map({"legacy": 0, "primary": 1, "backup": 2})
        ordered = out.assign(_pri=pri).sort_values(["_pri", "grts_rank"]).drop(columns="_pri")
        keep = enforce_min_distance(ordered, min_distance_m, keep_first=(ordered["status"] == "legacy"))
        out = ordered[keep.values].copy()
        new = out["status"] != "legacy"
        out.loc[new, "grts_rank"] = out[new].groupby("cell_id").cumcount() + 1
        n_new_s = out["cell_id"].map(n_new_by_cell).fillna(0)
        out.loc[new, "status"] = np.where(out.loc[new, "grts_rank"] <= n_new_s[new], "primary", "backup")
        cap = int(np.ceil(oversample_factor)) * pd.Series(n_new_by_cell)
        out = out[(~new) | (out["grts_rank"] <= out["cell_id"].map(cap).fillna(0))]

    out["inclusion_weight"] = w[out.index].values
    return out


def installation_order(selected: pd.DataFrame, cfg: dict, alloc: pd.DataFrame) -> pd.DataFrame:
    """
    Interleave primaries across cells round-robin: tail cells first, then the
    rest, within cell by grts_rank. Assign nested level labels using the
    allocation table's n_B at each level (min / option / full).
    """
    al = cfg["allocation"]
    prim = selected[selected["status"].isin(["primary", "legacy"])].copy()
    prim["_is_tail"] = prim.apply(
        lambda r: f"{r.seral_class}_{r.density_class}" in al["tail_cells"], axis=1)
    prim = prim.sort_values(["_is_tail", "cell_id", "grts_rank"], ascending=[False, True, True])
    prim["_within"] = prim.groupby("cell_id").cumcount()
    prim = prim.sort_values(["_within", "_is_tail", "cell_id"], ascending=[True, False, True])
    prim["install_order"] = np.arange(1, len(prim) + 1)

    # nested level by cumulative count within cell against each level's n_B
    lvl = {}
    for level in al["levels"]:
        lvl[level] = alloc[alloc["level"] == level].set_index("cell_id")["n_B"]
    def level_of(r):
        for level in al["levels"]:
            if r._within < lvl[level].get(r.cell_id, 0):
                return level
        return "beyond"
    prim["level"] = prim.apply(level_of, axis=1)
    return prim.drop(columns=["_is_tail", "_within"])


# ---------------------------------------------------------------------------
# Access class
# ---------------------------------------------------------------------------

def access_class(dist_to_road_m: pd.Series, slope_pct: pd.Series, cfg: dict) -> pd.Series:
    classes = cfg["access"]["classes"]
    out = pd.Series(4, index=dist_to_road_m.index)
    for k in sorted(classes, reverse=True):
        c = classes[k]
        if c["max_dist_m"] is None:
            continue
        ok = (dist_to_road_m <= c["max_dist_m"]) & (slope_pct <= c["max_slope_pct"])
        out[ok] = k
    return out.astype(int)


# ---------------------------------------------------------------------------
# Synthetic Basin (exercise the chain before real layers exist)
# ---------------------------------------------------------------------------

def block_reduce(arr: np.ndarray, k: int, how: str = "mean") -> np.ndarray:
    """
    Reduce a 2-D raster array to k x k blocks anchored at the array origin. NaN-aware.
    how: "mean" or "sum" over the block, or "center" for the centre pixel's value.
    Partial blocks at the right and bottom edges are padded with NaN.
    """
    a = arr.astype(float)
    pr, pc = (-a.shape[0]) % k, (-a.shape[1]) % k
    if pr or pc:
        a = np.pad(a, ((0, pr), (0, pc)), constant_values=np.nan)
    if how == "center":
        return a[k // 2::k, k // 2::k]
    b = a.reshape(a.shape[0] // k, k, a.shape[1] // k, k)
    with np.errstate(all="ignore"):
        return np.nanmean(b, axis=(1, 3)) if how == "mean" else np.nansum(b, axis=(1, 3))


def make_synthetic_frame(cfg: dict, seed: int = 1) -> pd.DataFrame:
    """
    A toy Basin of sampling units on the block lattice (frame.unit_px LiDAR pixels
    on a side) with the real forest type acreages, plausible LiDAR metrics, a state
    line, slope, road distance, fire and treatment flags. Enough to run every
    notebook end to end, including the minimum-distance rule in the draw.
    """
    rng = np.random.default_rng(seed)
    g = cfg["crs"]["lidar_grid_m"]
    k = cfg["frame"].get("unit_px", 1)
    B = g * k
    unit_ac = (B * B) / 4046.86
    pop = cfg["forest_types"]["population_acres"]
    rows = []
    for ftype, acres in pop.items():
        n = int(acres / unit_ac)
        # give each type a blob of space, then snap to the block lattice and drop collisions
        cx = {"SMC": 0.0, "RF": 12000.0, "JP": 24000.0}[ftype]
        x = np.round((rng.normal(cx, 3500, n) + 745000) / B) * B + B / 2
        y = np.round((rng.normal(0, 9000, n) + 4315000) / B) * B + B / 2
        xy = pd.DataFrame({"x": x, "y": y}).drop_duplicates()
        x, y = xy["x"].to_numpy(), xy["y"].to_numpy()
        n = len(x)
        h = rng.gamma(4, {"SMC": 6, "RF": 6.5, "JP": 4.5}[ftype], n)
        dens = np.clip(rng.gamma(3, {"SMC": 90, "RF": 100, "JP": 60}[ftype], n), 5, 1200)
        cover = np.clip(20 + 2.2 * h + rng.normal(0, 12, n), 0, 98)
        rows.append(pd.DataFrame({
            "x": x, "y": y, "forest_type": ftype,
            "p95_height_m": h, "stem_density": dens, "canopy_cover_pct": cover,
            "acres": unit_ac, "unit_acres": unit_ac, "unit_frac_in_frame": 1.0,
            "slope_pct": np.clip(rng.gamma(2, 12, n), 0, 120),
            "dist_road_m": rng.exponential(700, n),
            "state": np.where(x > 760000, "NV", "CA"),
            "elev_m": 1900 + rng.gamma(2, 150, n),
            "aspect_deg": rng.uniform(0, 360, n),
            "post_fire": rng.random(n) < 0.08,
            "treatment_2027_2031": rng.random(n) < 0.10,
            "owner": rng.choice(["USFS", "CSP", "NDF", "CTC", "Private"], n, p=[0.7, 0.08, 0.05, 0.07, 0.10]),
        }))
    frame = pd.concat(rows, ignore_index=True).drop_duplicates(subset=["x", "y"]).reset_index(drop=True)
    frame["unit_id"] = np.arange(len(frame))
    return frame
