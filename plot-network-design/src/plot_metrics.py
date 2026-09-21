"""
plot_metrics.py

Per-plot derived metrics from the Survey123 feature service tables, following
Plot-Data-Schema-and-Calculations.md. Input is the set of pandas DataFrames
that Survey123 publishes (FH_Plot, FH_Tree, FH_CoverPoint, FH_Transect,
FH_CWD). Output is one row per plot visit with the VP9 and VP10 inputs and the
fuels summary.

Typical use, from an exported file geodatabase or from the REST endpoints via
src/layers.read_layer:

    from src import plot_metrics as pm
    plots = pm.compute_all(plot_df, tree_df, cover_df, transect_df, cwd_df, cfg)

Field names match the XLSForm (TRPA_ForestHealth_Plot_Survey123_v1.0.xlsx).
Survey123 adds a globalid on the parent and a parentglobalid on each repeat
table; those are the join keys used here.
"""

from __future__ import annotations

import math
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .plot_geometry import (BA_CONST, DBH_FLOOR_IN, BREAKPOINT_DEFAULT_IN,
                            FT_PER_M, PRIMARY, TRANSECT_AZIMUTHS,
                            expansion_factor)

PARENT_KEY = "globalid"
CHILD_KEY = "parentglobalid"

# Working seral breaks (in QMD inches) from the threshold standard; confirm
# against the threshold report before the freeze.
SERAL_BREAKS_IN = (5.0, 25.0)
# Closed-canopy break by forest type, from VP9.
COVER_BREAK_PCT = {"JP": 40.0, "SMC": 50.0, "RF": 50.0}
COVER_BREAK_DEFAULT = 50.0


# ---------------------------------------------------------------------------
# Trees
# ---------------------------------------------------------------------------

def tree_metrics(tree: pd.DataFrame, plot: pd.DataFrame,
                 floor_in: float = DBH_FLOOR_IN) -> pd.DataFrame:
    """TPA, BA, QMD per plot visit from the tree repeat, live trees only by
    default. Uses the per-plot breakpoint recorded in FH_Plot.

    Returns columns: globalid, n_trees, tpa, ba_sqft_ac, qmd_in, tpa_snags.
    """
    bp = plot.set_index(PARENT_KEY)["breakpoint_dia_in"].fillna(BREAKPOINT_DEFAULT_IN)
    t = tree.copy()
    t["breakpoint"] = t[CHILD_KEY].map(bp).fillna(BREAKPOINT_DEFAULT_IN)
    t["ef"] = [expansion_factor(d, b) for d, b in zip(t["dbh_in"], t["breakpoint"])]
    t["ba_tree"] = BA_CONST * t["dbh_in"] ** 2
    t = t[t["dbh_in"] >= floor_in]

    live = t[t["tree_status"] == "live"]
    dead = t[t["tree_status"] == "dead_standing"]

    g = live.groupby(CHILD_KEY)
    out = pd.DataFrame({
        "n_trees": g.size(),
        "tpa": g["ef"].sum(),
        "ba_sqft_ac": g.apply(lambda d: (d["ba_tree"] * d["ef"]).sum()),
        "_sum_ef_d2": g.apply(lambda d: (d["ef"] * d["dbh_in"] ** 2).sum()),
    })
    out["qmd_in"] = np.sqrt(out["_sum_ef_d2"] / out["tpa"])
    out = out.drop(columns="_sum_ef_d2")
    out["tpa_snags"] = dead.groupby(CHILD_KEY)["ef"].sum()
    out["tpa_snags"] = out["tpa_snags"].fillna(0.0)
    return out.reset_index().rename(columns={CHILD_KEY: PARENT_KEY})


def tree_metrics_at_floors(tree: pd.DataFrame, plot: pd.DataFrame,
                           floors=(4.0, 5.0, 4.92)) -> pd.DataFrame:
    """Same metrics at several DBH floors, for the baseline bridge (4.0 in TRPA,
    5.0 in FIA, 12.5 cm = 4.92 in MSIM). Columns are suffixed by floor."""
    frames = []
    for f in floors:
        m = tree_metrics(tree, plot, floor_in=f).set_index(PARENT_KEY)
        m.columns = [f"{c}_f{str(f).replace('.', '_')}" for c in m.columns]
        frames.append(m)
    return pd.concat(frames, axis=1).reset_index()


# ---------------------------------------------------------------------------
# Canopy cover from the 100-point intercept
# ---------------------------------------------------------------------------

def cover_metrics(cover: pd.DataFrame) -> pd.DataFrame:
    """Crown cover, effective cover, and the definitional gap, excluding hits
    below 2 m so the value matches the LiDAR height threshold. Also returns
    the below-2 m shrub and regeneration hit fraction and the binomial SE.
    """
    c = cover.copy()
    above = c["cover_stratum"].fillna("") != "below2m"
    c["crown_hit"] = ((c["crown_cover_hit"] == "hit") & above).astype(int)
    c["eff_hit"] = ((c["effective_cover_hit"] == "hit") & above).astype(int)
    c["low_hit"] = ((c["crown_cover_hit"] == "hit") & ~above).astype(int)

    g = c.groupby(CHILD_KEY)
    n = g.size()
    out = pd.DataFrame({
        "n_cover_points": n,
        "crown_cover_pct": 100.0 * g["crown_hit"].sum() / n,
        "effective_cover_pct": 100.0 * g["eff_hit"].sum() / n,
        "understory_hit_pct": 100.0 * g["low_hit"].sum() / n,
    })
    out["cover_definitional_gap"] = out["crown_cover_pct"] - out["effective_cover_pct"]
    p = out["crown_cover_pct"] / 100.0
    out["crown_cover_se_pct"] = 100.0 * np.sqrt(p * (1 - p) / out["n_cover_points"])
    return out.reset_index().rename(columns={CHILD_KEY: PARENT_KEY})


def cover_from_crown_widths(tree: pd.DataFrame, plot_area_sqft: float = PRIMARY.area_sqft) -> pd.DataFrame:
    """Modeled crown cover from measured crown widths, ellipse area per tree,
    non-overlap not corrected. Used only as the cross-check against the point
    intercept described in Protocol section 5.2."""
    t = tree[(tree["tree_status"] == "live") & tree["crown_width_long_ft"].notna()].copy()
    t["crown_area"] = math.pi * (t["crown_width_long_ft"] / 2) * (t["crown_width_perp_ft"].fillna(t["crown_width_long_ft"]) / 2)
    # only stems inside the primary plot contribute to the primary-plot footprint
    t = t[t["distance_ft"] <= PRIMARY.radius_ft]
    g = t.groupby(CHILD_KEY)["crown_area"].sum()
    out = pd.DataFrame({"crown_cover_modeled_pct": (100.0 * g / plot_area_sqft).clip(upper=100.0)})
    return out.reset_index().rename(columns={CHILD_KEY: PARENT_KEY})


# ---------------------------------------------------------------------------
# Seral stage and VP9 class
# ---------------------------------------------------------------------------

def seral_class(qmd_in: float) -> str:
    if pd.isna(qmd_in):
        return "unknown"
    if qmd_in < SERAL_BREAKS_IN[0]:
        return "early"
    if qmd_in < SERAL_BREAKS_IN[1]:
        return "mid"
    return "late"


def vp9_class(seral: str, crown_cover_pct: float, forest_type: str) -> str:
    if seral in ("early", "unknown"):
        return seral
    brk = COVER_BREAK_PCT.get(forest_type, COVER_BREAK_DEFAULT)
    return f"{seral}_{'closed' if crown_cover_pct >= brk else 'open'}"


# ---------------------------------------------------------------------------
# Fuels
# ---------------------------------------------------------------------------

def _slope_factor(slope_pct: float) -> float:
    """FIA slope correction, c = 1 + (slope/100)^2. Not Brown's 1/cos."""
    return 1.0 + (slope_pct / 100.0) ** 2


def fuel_metrics(transect: pd.DataFrame, cwd: pd.DataFrame, plot: pd.DataFrame,
                 transect_key: str = "globalid") -> pd.DataFrame:
    """Coarse and fine woody counts per plot, duff and litter means, and CWD
    volume per acre by the planar intercept estimator.

    CWD volume (cu ft per acre) per Van Wagner / Brown:
        V = (pi^2 / (8 L)) * sum(d^2) * c
    with d in feet, L the total transect length in feet after slope
    correction, and c the slope factor applied to L. Reported in cubic feet
    per acre; convert to tons per acre with a species-and-decay-class density
    table downstream.
    """
    slope = plot.set_index(PARENT_KEY)["slope_pct"].fillna(0.0)
    tr = transect.copy()
    tr["c"] = tr[CHILD_KEY].map(slope).fillna(0.0).map(_slope_factor)

    g = tr.groupby(CHILD_KEY)
    out = pd.DataFrame({
        "n_transects": g.size(),
        "fwd_1hr_count": g["fwd_small_count"].sum(),
        "fwd_10hr_count": g["fwd_medium_count"].sum(),
        "fwd_100hr_count": g["fwd_large_count"].sum(),
        "duff_in_mean": g[["duff_20ft", "duff_50ft"]].mean().mean(axis=1),
        "litter_in_mean": g[["litter_20ft", "litter_50ft"]].mean().mean(axis=1),
        "slope_factor": g["c"].first(),
    })

    # CWD: sum d^2 over pieces per plot, join through the transect table
    if len(cwd):
        piece = cwd.merge(tr[[transect_key, CHILD_KEY, "c"]].rename(columns={CHILD_KEY: "plot_gid"}),
                          left_on=CHILD_KEY, right_on=transect_key, how="left")
        piece["d_ft2"] = (piece["cwd_dia_in"] / 12.0) ** 2
        # hollow correction: subtract hollow cross-section
        piece["d_ft2"] -= (piece["cwd_hollow_dia_in"].fillna(0.0) / 12.0) ** 2
        pg = piece.groupby("plot_gid")
        sum_d2 = pg["d_ft2"].sum()
        n_pieces = pg.size()
        charred = pg["cwd_charred_pct"].mean()
        L_ft = len(TRANSECT_AZIMUTHS) * PRIMARY.radius_ft  # 235.6 ft nominal
        c = out["slope_factor"]
        vol_cuft_ac = (math.pi ** 2 / (8.0 * L_ft * c)) * sum_d2.reindex(out.index).fillna(0.0) * 43560.0
        out["cwd_pieces"] = n_pieces.reindex(out.index).fillna(0).astype(int)
        out["cwd_cuft_ac"] = vol_cuft_ac
        out["cwd_charred_pct_mean"] = charred.reindex(out.index)
    else:
        out["cwd_pieces"] = 0
        out["cwd_cuft_ac"] = 0.0
        out["cwd_charred_pct_mean"] = np.nan
    return out.reset_index().rename(columns={CHILD_KEY: PARENT_KEY})


# ---------------------------------------------------------------------------
# Assemble
# ---------------------------------------------------------------------------

def compute_all(plot: pd.DataFrame, tree: pd.DataFrame, cover: pd.DataFrame,
                transect: pd.DataFrame, cwd: pd.DataFrame,
                cfg: Optional[Dict] = None) -> pd.DataFrame:
    """One row per plot visit with the VP9 and VP10 inputs and the fuels summary."""
    base = plot[[PARENT_KEY, "plot_id", "visit_date", "visit_type", "forest_type",
                 "breakpoint_dia_in", "slope_pct", "aspen_flag", "horiz_acc_m"]].copy()
    m = base.merge(tree_metrics(tree, plot), on=PARENT_KEY, how="left")
    m = m.merge(cover_metrics(cover), on=PARENT_KEY, how="left")
    m = m.merge(cover_from_crown_widths(tree), on=PARENT_KEY, how="left")
    m = m.merge(fuel_metrics(transect, cwd, plot), on=PARENT_KEY, how="left")

    m["seral_class"] = m["qmd_in"].map(seral_class)
    m["vp9_class"] = [vp9_class(s, c, f) for s, c, f in zip(m["seral_class"], m["crown_cover_pct"], m["forest_type"])]
    m["cover_crosscheck_flag"] = (m["crown_cover_pct"] - m["crown_cover_modeled_pct"]).abs() > 10.0
    m["position_flag"] = np.where(m["aspen_flag"] == "yes", m["horiz_acc_m"] > 0.3, m["horiz_acc_m"] > 1.0)
    return m


def vp10_attainment(metrics: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    """Flag each plot against the VP10 density table.

    targets: columns forest_type, seral_class, tpa_max, ba_max (values are maximums;
    a plot attains when both tpa and ba are at or below target).
    """
    t = metrics.merge(targets, on=["forest_type", "seral_class"], how="left")
    t["vp10_attain"] = (t["tpa"] <= t["tpa_max"]) & (t["ba_sqft_ac"] <= t["ba_max"])
    return t


VP10_TARGETS = pd.DataFrame([
    # from thresholds/189-stand-density.md, values are maximums
    ("JP", "early", 200, 30), ("JP", "mid", 70, 80), ("JP", "late", 55, 100),
    ("SMC", "early", 300, 40), ("SMC", "mid", 90, 130), ("SMC", "late", 75, 180),
    ("RF", "early", 300, 50), ("RF", "mid", 100, 175), ("RF", "late", 80, 250),
], columns=["forest_type", "seral_class", "tpa_max", "ba_max"])
