"""
covariates.py

Balancing covariates for site selection. These are the stable landscape
attributes GRTS balances on (via caty_var / caty_n) without stratifying on
them: basin side and topographic position. Neither changes between
remeasurement cycles, so balancing on them does not lock the design to a
current-condition snapshot the way structure strata would.

Both functions operate on numpy arrays or pandas Series aligned to the
candidate point frame written by notebooks/01_frame.ipynb.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TPI_CLASSES = ["valley", "lower_slope", "mid_slope", "upper_slope", "ridge"]


def tpi(dem: np.ndarray, radius_px: int) -> np.ndarray:
    """Topographic position index: elevation minus the mean of an annulus
    neighborhood. Positive is above surroundings (ridge), negative below
    (valley). Uses a square window for speed; a circular window changes
    little at the radii used here (Weiss 2001).
    """
    from scipy.ndimage import uniform_filter
    k = 2 * radius_px + 1
    mean = uniform_filter(dem.astype("float64"), size=k, mode="nearest")
    return dem - mean


def tpi_class(tpi_vals: np.ndarray, slope_pct: np.ndarray,
              sd: float | None = None) -> np.ndarray:
    """Five-class landform from TPI and slope, after Weiss (2001) and
    Jenness (2006). Breaks are in standard deviations of TPI over the frame.

        tpi >  1 sd                  ridge
        0.5 < tpi <= 1 sd            upper slope
       -0.5 <= tpi <= 0.5, slope>5   mid slope
       -0.5 <= tpi <= 0.5, slope<=5  flat (assigned to mid_slope here)
       -1 sd <= tpi < -0.5           lower slope
        tpi < -1 sd                  valley
    """
    sd = float(np.nanstd(tpi_vals)) if sd is None else sd
    z = tpi_vals / sd
    out = np.full(z.shape, "mid_slope", dtype=object)
    out[z > 1.0] = "ridge"
    out[(z > 0.5) & (z <= 1.0)] = "upper_slope"
    out[(z < -0.5) & (z >= -1.0)] = "lower_slope"
    out[z < -1.0] = "valley"
    return out


def basin_side(x: np.ndarray, y: np.ndarray, axis_x0: float, axis_y0: float,
               axis_azimuth_deg: float = 20.0) -> np.ndarray:
    """East or west of the lake's long axis. The axis passes through
    (axis_x0, axis_y0) at the given azimuth (degrees clockwise from north).
    Default 20 degrees approximates the Tahoe basin's NNE orientation; set
    the anchor to the lake centroid in the frame CRS.

    A climate covariate (PRISM precipitation or an aridity index) binned at
    its median is a better split where the rain shadow does not follow the
    lake axis; swap it in here if that layer is in config.
    """
    a = np.radians(axis_azimuth_deg)
    # signed distance from the axis line; positive is east of the axis
    d = (x - axis_x0) * np.cos(a) - (y - axis_y0) * np.sin(a)
    return np.where(d >= 0, "east", "west")


def balance_category(side: np.ndarray, topo: np.ndarray) -> np.ndarray:
    """The caty_var value: side crossed with topographic position, ten classes."""
    return np.char.add(np.char.add(side.astype(str), "_"), topo.astype(str))


def caty_n_by_stratum(frame: pd.DataFrame, n_by_stratum: dict,
                      stratum_col: str = "forest_type",
                      caty_col: str = "balance_caty",
                      min_per_caty: int = 2) -> dict:
    """Expected sites per balance category within each stratum, proportional
    to the category's area share in that stratum, with a floor so no
    occupied category is left empty. Returns {stratum: {caty: n}} in the
    shape spsurvey's caty_n expects when stratum_var is set.
    """
    out = {}
    for s, n in n_by_stratum.items():
        sub = frame[frame[stratum_col] == s]
        shares = sub[caty_col].value_counts(normalize=True)
        raw = (shares * n).round().astype(int)
        raw[raw < min_per_caty] = min_per_caty
        # rescale to n after flooring
        excess = raw.sum() - n
        if excess > 0:
            order = raw.sort_values(ascending=False).index
            for c in order:
                if excess == 0:
                    break
                take = min(excess, raw[c] - min_per_caty)
                raw[c] -= take
                excess -= take
        out[s] = raw.to_dict()
    return out
