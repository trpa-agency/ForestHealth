"""
plot_geometry.py

Fixed geometry of the TRPA Forest Health plot (Protocol v1.0, September 19, 2026)
and the helpers that derive navigation targets from a plot center.

Sampling units, all sharing one center:

    microplot        6.8 ft   1/300 ac   saplings 1.0 to 3.9 in, seedlings counted
    subplot         24.0 ft   1/24 ac    understory and fuels footprint, no tree tally
    primary        58.9 ft    1/4 ac     all trees 4.0 in to below the breakpoint
    macroplot      56.4 m     2.469 ac   all trees at or above the breakpoint

Trees at or above the breakpoint carry the macroplot expansion factor over the
full 56.4 m circle, including inside the primary plot. This follows the FIADB
rule (MACRO_BREAKPOINT_DIA applies from 0.01 ft) and prevents double counting.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

FT_PER_M = 3.28083989501312
SQFT_PER_ACRE = 43560.0
ACRES_PER_HA = 2.47105381467

DBH_FLOOR_IN = 4.0
SAPLING_MIN_IN = 1.0
BREAKPOINT_DEFAULT_IN = 24.0
BA_CONST = math.pi / 4.0 / 144.0          # 0.005454154, sq in DBH -> sq ft BA


@dataclass(frozen=True)
class SamplingUnit:
    name: str
    radius_ft: float

    @property
    def radius_m(self) -> float:
        return self.radius_ft / FT_PER_M

    @property
    def area_sqft(self) -> float:
        return math.pi * self.radius_ft ** 2

    @property
    def area_ac(self) -> float:
        return self.area_sqft / SQFT_PER_ACRE

    @property
    def area_m2(self) -> float:
        return math.pi * self.radius_m ** 2

    @property
    def tpa_per_tree(self) -> float:
        """Expansion factor: trees per acre represented by one tallied tree."""
        return 1.0 / self.area_ac


MICROPLOT = SamplingUnit("microplot", 6.8)
SUBPLOT = SamplingUnit("subplot", 24.0)
PRIMARY = SamplingUnit("primary", 58.9)
MACROPLOT = SamplingUnit("macroplot", 56.4 * FT_PER_M)     # 185.04 ft

UNITS: Dict[str, SamplingUnit] = {u.name: u for u in (MICROPLOT, SUBPLOT, PRIMARY, MACROPLOT)}

TRANSECT_AZIMUTHS = (0, 90, 180, 270)
TRANSECT_LENGTH_FT = PRIMARY.radius_ft
FWD_SMALL_MED_SEGMENT_FT = (14.0, 20.0)
FWD_LARGE_SEGMENT_FT = (14.0, 24.0)
DUFF_LITTER_POINTS_FT = (20.0, 50.0)
COVER_POINT_START_FT = 3.0
COVER_POINT_SPACING_FT = 2.0
COVER_POINTS_PER_TRANSECT = 25


def expansion_factor(dbh_in: float, breakpoint_in: float = BREAKPOINT_DEFAULT_IN) -> float:
    """Trees per acre represented by one tree of the given DBH."""
    if dbh_in < SAPLING_MIN_IN:
        raise ValueError("seedlings are counted, not expanded")
    if dbh_in < DBH_FLOOR_IN:
        return MICROPLOT.tpa_per_tree
    if dbh_in < breakpoint_in:
        return PRIMARY.tpa_per_tree
    return MACROPLOT.tpa_per_tree


def tally_unit(dbh_in: float, breakpoint_in: float = BREAKPOINT_DEFAULT_IN) -> str:
    if dbh_in < SAPLING_MIN_IN:
        return "seedling"
    if dbh_in < DBH_FLOOR_IN:
        return "microplot"
    if dbh_in < breakpoint_in:
        return "primary"
    return "macroplot"


def is_in_plot(distance_ft: float, dbh_in: float, breakpoint_in: float = BREAKPOINT_DEFAULT_IN) -> bool:
    """In-or-out decision by horizontal distance to bole center at ground level."""
    return distance_ft <= UNITS[tally_unit(dbh_in, breakpoint_in)].radius_ft


def basal_area_sqft(dbh_in: float) -> float:
    return BA_CONST * dbh_in * dbh_in


# ---------------------------------------------------------------------------
# Positions derived from plot center (projected coordinates, meters, north-up)
# ---------------------------------------------------------------------------

def offset(x: float, y: float, azimuth_deg: float, distance_m: float) -> Tuple[float, float]:
    """Point at azimuth (degrees clockwise from grid north) and distance from x, y."""
    a = math.radians(azimuth_deg)
    return x + distance_m * math.sin(a), y + distance_m * math.cos(a)


def transect_endpoints(x: float, y: float) -> List[dict]:
    return [{"azimuth": az, "x": ex, "y": ey}
            for az in TRANSECT_AZIMUTHS
            for ex, ey in [offset(x, y, az, TRANSECT_LENGTH_FT / FT_PER_M)]]


def cover_points(x: float, y: float) -> List[dict]:
    """The 100 canopy intercept points, matching the Survey123 repeat calculation."""
    pts = []
    idx = 0
    for az in TRANSECT_AZIMUTHS:
        for k in range(COVER_POINTS_PER_TRANSECT):
            idx += 1
            d_ft = COVER_POINT_START_FT + k * COVER_POINT_SPACING_FT
            px, py = offset(x, y, az, d_ft / FT_PER_M)
            pts.append({"pt_index": idx, "azimuth": az, "distance_ft": d_ft, "x": px, "y": py})
    return pts


def duff_litter_points(x: float, y: float) -> List[dict]:
    return [{"azimuth": az, "distance_ft": d, "x": px, "y": py}
            for az in TRANSECT_AZIMUTHS
            for d in DUFF_LITTER_POINTS_FT
            for px, py in [offset(x, y, az, d / FT_PER_M)]]


def stem_position(x: float, y: float, azimuth_deg: float, distance_ft: float) -> Tuple[float, float]:
    """Tree position from the recorded azimuth and horizontal distance."""
    return offset(x, y, azimuth_deg, distance_ft / FT_PER_M)


def back_azimuth(azimuth_deg: float) -> float:
    """Azimuth from a witness tree back to plot center."""
    return (azimuth_deg + 180.0) % 360.0


def ring_polygons(x: float, y: float, n_vertices: int = 72) -> Dict[str, List[Tuple[float, float]]]:
    """Vertex rings for each sampling unit, for a navigation map or clip footprint."""
    out = {}
    for name, u in UNITS.items():
        r = u.radius_m
        out[name] = [(x + r * math.sin(2 * math.pi * i / n_vertices),
                      y + r * math.cos(2 * math.pi * i / n_vertices)) for i in range(n_vertices)]
    return out


def summary_table() -> str:
    rows = ["| Unit | Radius (ft) | Radius (m) | Area (ac) | Area (m2) | TPA per tree |",
            "|---|---|---|---|---|---|"]
    for u in (MICROPLOT, SUBPLOT, PRIMARY, MACROPLOT):
        rows.append(f"| {u.name} | {u.radius_ft:.1f} | {u.radius_m:.4f} | {u.area_ac:.7f} | "
                    f"{u.area_m2:.2f} | {u.tpa_per_tree:.6f} |")
    return "\n".join(rows)


if __name__ == "__main__":
    print(summary_table())
