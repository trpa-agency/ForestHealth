"""Tests for the Oct 19 2026 design helpers in src/design_template.py.
Run: python -m pytest tests/test_design_oct19.py -q
"""
import numpy as np
import pandas as pd
import pytest

from src.io import load_config
from src import design_template as dt


@pytest.fixture(scope="module")
def cfg():
    return load_config()


def toy_frame(n=3000, seed=0):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "unit_id": np.arange(n),
        "forest_type": rng.choice(["SMC", "JP", "RF"], n, p=[0.6, 0.2, 0.2]),
        "seral_class": rng.choice(["early", "mid", "late"], n),
        "density_class": rng.choice(["low", "high"], n),
        "slope_pct": rng.uniform(0, 90, n),
        "x": rng.uniform(0, 20000, n), "y": rng.uniform(0, 30000, n), "acres": 2.0,
    })


def test_targets_match_decisions(cfg):
    t = dt.selection_targets(cfg).set_index("forest_type")
    assert t["n_min"].to_dict() == {"SMC": 40, "JP": 40, "RF": 40}
    assert t["n_full"].to_dict() == {"SMC": 70, "JP": 40, "RF": 40}
    assert t["list_len"].to_dict() == {"SMC": 210, "JP": 120, "RF": 120}
    assert (t["n_base"] + t["n_over"]).equals(t["list_len"])


def test_multiplier_values(cfg):
    f = dt.inclusion_multiplier(toy_frame(), cfg)
    assert set(np.round(f["mult"].unique(), 3)) <= {0.5, 0.75, 1.0, 1.5}
    late_low_flat = f[(f["seral_class"] == "late") & (f["density_class"] == "low") & (f["slope_pct"] <= 50)]
    assert (late_low_flat["mult"] == 1.5).all()
    mid_steep = f[(f["seral_class"] == "mid") & (f["slope_pct"] > 50)]
    assert (mid_steep["mult"] == 0.5).all()


def test_inclusion_probabilities_sum_to_n(cfg):
    f = dt.inclusion_multiplier(toy_frame(), cfg)
    n = {"SMC": 70, "JP": 40, "RF": 40}
    ip = dt.design_ip(f, n)
    sums = ip.groupby(f["forest_type"]).sum().round(6).to_dict()
    assert sums == {k: float(v) for k, v in n.items()}
    assert (ip < 1).all()


def test_levels_and_order(cfg):
    t = dt.selection_targets(cfg)
    rows = []
    for _, r in t.iterrows():
        for k in range(1, r["list_len"] + 1):
            rows.append({"unit_id": len(rows), "stratum": r["forest_type"], "forest_type": r["forest_type"], "grts_rank": k})
    sel = dt.assign_levels(pd.DataFrame(rows), t)
    counts = sel.groupby(["forest_type", "level"]).size().unstack(fill_value=0)
    assert counts.loc["SMC", "min"] == 40 and counts.loc["SMC", "full"] == 30 and counts.loc["SMC", "backup"] == 140
    assert counts.loc["JP", "full"] == 0 and counts.loc["JP", "backup"] == 80
    prim = sel[sel["level"] != "backup"].sort_values("install_order")
    assert (prim["level"].iloc[:120] == "min").all()                     # every min site is installed before any full site
    assert prim["forest_type"].iloc[:3].nunique() == 3                     # types interleave
    assert sel.loc[(sel["forest_type"] == "SMC") & (sel["level"] == "backup"), "backup_order"].min() == 1


def test_access_classes():
    mi = 1609.344
    cls = dt.access_class_mi([0, 0.49 * mi, 0.5 * mi, 1.49 * mi, 1.5 * mi, 5 * mi, np.nan], [0.5, 1.5])
    assert list(cls) == [1, 1, 2, 2, 3, 3, 3]


def test_hike_distance_counts_slope():
    pytest.importorskip("skimage")
    n = 60
    road = np.zeros((n, n), bool); road[:, 0] = True
    flat = np.zeros((n, n))
    ramp = np.tile(np.arange(n) * 30.0 * 0.6, (n, 1))                     # 60 percent slope away from the road
    d_flat = dt.hike_distance_m(road, flat, 30.0)
    d_ramp = dt.hike_distance_m(road, ramp, 30.0)
    assert abs(d_flat[10, 40] - 40 * 30.0) < 1e-6
    assert d_ramp[10, 40] == pytest.approx(40 * 30.0 * np.sqrt(1 + 0.36), rel=0.02)
    lake = flat.copy(); lake[:, 20] = np.nan; lake[5, 20] = 0.0          # a wall with one gap
    assert dt.hike_distance_m(road, lake, 30.0)[50, 40] > d_flat[50, 40]


def test_markdown_table():
    md = dt.to_markdown(pd.DataFrame({"a": [1], "b": [2]}, index=["JP"]))
    assert md.splitlines()[0] == "| index | a | b |" and md.splitlines()[2] == "| JP | 1 | 2 |"
