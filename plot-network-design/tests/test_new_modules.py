"""Smoke tests for the modules added September 19, 2026.
Run: python -m pytest tests/test_new_modules.py -q
"""
import math
import pandas as pd
import pytest

from src import plot_geometry as pg
from src import plot_metrics as pm
from src import sample_size as ss


def test_geometry_constants():
    assert abs(pg.PRIMARY.area_ac - 0.250203) < 1e-5
    assert abs(pg.PRIMARY.tpa_per_tree - 3.996753) < 1e-5
    assert abs(pg.MACROPLOT.area_ac - 2.4693) < 1e-3
    assert abs(pg.MICROPLOT.tpa_per_tree - 299.86) < 0.01
    assert pg.tally_unit(3.9) == "microplot"
    assert pg.tally_unit(4.0) == "primary"
    assert pg.tally_unit(23.9) == "primary"
    assert pg.tally_unit(24.0) == "macroplot"
    assert pg.tally_unit(24.0, breakpoint_in=21.0) == "macroplot"


def test_cover_points_match_form_calculation():
    pts = pg.cover_points(0.0, 0.0)
    assert len(pts) == 100
    assert pts[0]["azimuth"] == 0 and pts[0]["distance_ft"] == 3.0
    assert pts[24]["distance_ft"] == 51.0
    assert pts[25]["azimuth"] == 90 and pts[25]["distance_ft"] == 3.0
    assert pts[99]["azimuth"] == 270 and pts[99]["distance_ft"] == 51.0


def test_sample_size_tables_agree_with_review():
    assert round(100 * ss.ci_halfwidth(300, 0.5), 1) == 5.7
    assert ss.n_one_sided(0.50, 0.60) == 153
    assert ss.n_one_sided(0.50, 0.55) == 617
    assert round(ss.split_deff(0.5, 2.0), 3) == 1.111
    assert ss.n_change(0.50, 0.60, rho=0.0) == 388
    assert ss.n_change(0.50, 0.60, rho=0.9) == 39
    a = ss.allocate_by_share(300, {"SMC": 60276, "JP": 28783, "RF": 22365})
    assert sum(a.values()) == 300 and a["RF"] == 60


def _synthetic_plot():
    plot = pd.DataFrame({
        "globalid": ["P1"], "plot_id": ["T001"], "visit_date": ["2027-07-01"],
        "visit_type": ["install"], "forest_type": ["SMC"], "breakpoint_dia_in": [24.0],
        "slope_pct": [30], "aspen_flag": ["no"], "horiz_acc_m": [0.6],
    })
    # 20 live trees on the primary plot at 10 in, 2 large trees at 30 in on the macroplot
    tree = pd.DataFrame({
        "parentglobalid": ["P1"] * 22,
        "dbh_in": [10.0] * 20 + [30.0, 30.0],
        "tree_status": ["live"] * 22,
        "crown_width_long_ft": [15.0] * 22, "crown_width_perp_ft": [15.0] * 22,
        "distance_ft": [30.0] * 20 + [100.0, 150.0],
    })
    cover = pd.DataFrame({
        "parentglobalid": ["P1"] * 100,
        "crown_cover_hit": ["hit"] * 60 + ["miss"] * 40,
        "effective_cover_hit": ["hit"] * 45 + ["miss"] * 55,
        "cover_stratum": ["6to16m"] * 60 + [None] * 40,
    })
    transect = pd.DataFrame({
        "globalid": ["T1", "T2", "T3", "T4"], "parentglobalid": ["P1"] * 4,
        "fwd_small_count": [10, 12, 8, 9], "fwd_medium_count": [4, 3, 5, 4],
        "fwd_large_count": [2, 1, 2, 3],
        "duff_20ft": [1.0, 1.2, 0.8, 1.1], "duff_50ft": [1.1, 1.0, 0.9, 1.0],
        "litter_20ft": [0.5, 0.6, 0.4, 0.5], "litter_50ft": [0.5, 0.5, 0.6, 0.4],
    })
    cwd = pd.DataFrame({
        "parentglobalid": ["T1", "T1", "T3"],
        "cwd_dia_in": [6.0, 12.0, 8.0], "cwd_hollow_dia_in": [0.0, 0.0, 0.0],
        "cwd_charred_pct": [0, 20, 0],
    })
    return plot, tree, cover, transect, cwd


def test_plot_metrics_end_to_end():
    plot, tree, cover, transect, cwd = _synthetic_plot()
    m = pm.compute_all(plot, tree, cover, transect, cwd)
    r = m.iloc[0]
    # 20 trees * 3.9968 + 2 * 0.40497
    assert abs(r["tpa"] - (20 * pg.PRIMARY.tpa_per_tree + 2 * pg.MACROPLOT.tpa_per_tree)) < 1e-6
    # BA check
    ba = 20 * pg.basal_area_sqft(10.0) * pg.PRIMARY.tpa_per_tree + 2 * pg.basal_area_sqft(30.0) * pg.MACROPLOT.tpa_per_tree
    assert abs(r["ba_sqft_ac"] - ba) < 1e-6
    assert 10.0 < r["qmd_in"] < 12.0          # weighted toward the 10 in trees
    assert r["crown_cover_pct"] == 60.0
    assert r["effective_cover_pct"] == 45.0
    assert r["cover_definitional_gap"] == 15.0
    assert r["seral_class"] == "mid"
    assert r["vp9_class"] == "mid_closed"      # 60 >= 50 for SMC
    assert r["cwd_pieces"] == 3
    assert r["cwd_cuft_ac"] > 0
    assert abs(r["slope_factor"] - 1.09) < 1e-9


def test_vp10_attainment():
    plot, tree, cover, transect, cwd = _synthetic_plot()
    m = pm.compute_all(plot, tree, cover, transect, cwd)
    t = pm.vp10_attainment(m, pm.VP10_TARGETS)
    # SMC mid target is 90 TPA / 130 BA; this plot is ~80.7 TPA and ~48 BA -> attains
    assert bool(t.iloc[0]["vp10_attain"]) is True
