"""Write html/data/figures.js from the repo's own outputs.

Run: python scripts/build_html_data.py

Every number the briefing page shows comes from here, so the page can never
quietly disagree with the analysis. Sources, in order of preference:

  outputs/tessellation_summary.json     grid counts, occupancy, lattice fit (06_tessellation)
  outputs/TahoeBasin_Hex4*.gpkg         fallback for the same, from an older run
  outputs/bin_size_evaluation_*.csv     the display criterion sweep, if one was ever run
  config.yaml forest_types.population_acres   the threshold frame area
  src.sample_size / src.tessellation    derived cell sizes

Anything the repo cannot produce yet falls back to the value in FALLBACK below,
which is the only place a hand entered figure is allowed to live. Keep that
dictionary small and keep a source note beside each entry.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.io import load_config  # noqa: E402
from src import tessellation as T  # noqa: E402

OUT = ROOT / "html" / "data" / "figures.js"
OUTPUTS = ROOT / "outputs"

# Figures not yet produced by code in this repo. Each needs a source note.
FALLBACK = {
    # ForestHealth threshold analysis, stand_density_forest_type_attainment_new.csv
    "attainment": {"standard_pct": 50,
                   "types": ["Jeffrey pine", "Sierran mixed conifer", "Red fir"],
                   "pct": [7, 28, 56],
                   "source": "ForestHealth threshold analysis"},
    # Yang et al. 2023, Remote Sensing 15(14):3509; 0.10 ha interpolated
    "plotsize": {"label": ["0.04 ha", "0.10 ha", "0.25 ha", "1.0 ha"],
                 "note": ["subplot scale", "our plot", "", ""],
                 "mg_ha": [18.2, 12.5, 10.9, 10.1],
                 "highlight": 1,
                 "source": "Yang et al. 2023, Remote Sensing 15(14):3509"},
    # Budget scenarios, internal; never printed in an RFP
    "money": {"label": ["$1,000", "$2,000", "$3,000", "$5,000"],
              "plots": [163, 82, 54, 33], "highlight": 1},
}


def newest(pattern: str) -> Path | None:
    hits = sorted(OUTPUTS.glob(pattern))
    return hits[-1] if hits else None


def grid_block(cfg) -> tuple[dict, dict]:
    """Grid counts and the TEON increments, read from the exported Basin grid.

    06_tessellation writes outputs/tessellation_summary.json with every figure the
    page needs; that is the preferred source. The GeoPackage path below is the
    fallback for an older run.
    """
    summary = OUTPUTS / "tessellation_summary.json"
    if summary.exists():
        s = json.loads(summary.read_text(encoding="utf-8"))
        grid = {k: v for k, v in s["grid"].items() if not k.startswith(("file_", "anchor"))}
        grid["basin_land_km2"] = s["basin_land_km2"]
        inc = s["increments"]
        increments = {"label": [l.split(". ", 1)[-1] for l in inc["label"]], "sites": inc["sites"],
                      "cells": inc["cells"], "current": 1, "source": inc["source"]}
        return grid, increments

    gpkg = newest("TahoeBasin_Hex4*.gpkg") or newest("basin_hex_grid_*.gpkg")
    if gpkg is None:
        raise SystemExit("no Basin grid in outputs/; run notebooks/06_tessellation first")

    import geopandas as gpd

    g = gpd.read_file(gpkg)
    min_land = cfg["tessellation"]["min_land_frac"]
    land = g[g["land_frac"] > min_land]
    core = land.get("n_core99", pd.Series(0, index=land.index)).fillna(0)
    other = land.get("n_msim_other", pd.Series(0, index=land.index)).fillna(0)
    terr = core + other

    lat_csv = OUTPUTS / "owl_grid_lattice_parameters.csv"
    lat = pd.read_csv(lat_csv, index_col=0).iloc[:, 0].to_dict() if lat_csv.exists() else {}

    grid = {
        "cell_ha": round(float(g["cell_area_ha"].mean()), 1),
        "cell_acres": round(float(g["cell_area_ha"].mean()) * 2.4710538, 1),
        "spacing_m": round(float(lat.get("spacing_m", 0)) or 0, 1),
        "total_cells": int(len(g)),
        "existing_cells": int((g["source"] == "existing").sum()),
        "new_cells": int((g["source"] == "new").sum()),
        "land_cells": int(len(land)),
        "occupied_cells": int((terr > 0).sum()),
        "empty_cells": int((terr == 0).sum()),
        "anisotropy": round(float(lat.get("anisotropy", 0)) or 0, 4),
    }
    increments = {
        "label": ["Core 99 resample", "Plus remaining MSIM", "One site per land cell"],
        "sites": [int(core.sum()), int(terr.sum()), int(len(land))],
        "cells": [int((core > 0).sum()), int((terr > 0).sum()), int(len(land))],
        "current": 1,
        "source": f"{gpkg.name}",
    }
    return grid, increments


def cells_block(cfg, cell_ha: float) -> dict:
    """Cells the forested threshold frame yields at each candidate cell size."""
    frame_ac = sum(cfg["forest_types"]["population_acres"].values())
    frame_ha = frame_ac / 2.4710538
    target = int(cfg["allocation"]["levels"]["full"])
    third = cell_ha / 3.0
    at_target = T.cells_for_sample_size(frame_ha, target)["cell_area_ha"]
    sizes = sorted({100.0, round(third, 1), round(at_target, 1), 200.0, 300.0, round(cell_ha, 1), 500.0})
    return {
        "target": target,
        "cell_ha": sizes,
        "label": [f"{s:.0f}" for s in sizes],
        "n_cells": [int(round(frame_ha / s)) for s in sizes],
        "highlight_ha": [round(third, 1), round(cell_ha, 1)],
        "source": "src.tessellation.cells_for_sample_size on the threshold frame",
    }


def binsize_block() -> dict:
    csv = newest("bin_size_evaluation_*.csv")
    if csv is None:
        return {}
    df = pd.read_csv(csv)
    return {
        "cell_ha": [round(v, 1) for v in df["cell_area_ha"]],
        "score": [round(v, 3) for v in df["score"]],
        "uniformity_testable": round(float(df.get("uniformity_testable", pd.Series([0])).max()), 3),
        "warning": ("No cell holds enough points for the within cell randomness test, so the score "
                    "reduces to the entropy term and rises without limit. The sweep is uninformative "
                    "on this point pattern."),
    }


def main() -> None:
    cfg = load_config()
    grid, increments = grid_block(cfg)
    frame_ac = sum(cfg["forest_types"]["population_acres"].values())

    data = {
        "meta": {
            "generated": pd.Timestamp.today().strftime("%Y-%m-%d"),
            "boundary": str(cfg["tessellation"]["sources"]["boundary"]),
            "frame_acres": int(frame_ac),
            "frame_hectares": int(round(frame_ac / 2.4710538)),
            "target_plots": int(cfg["allocation"]["levels"]["full"]),
        },
        "attainment": FALLBACK["attainment"],
        "cells": cells_block(cfg, grid["cell_ha"]),
        "grid": grid,
        "increments": increments,
        "plotsize": FALLBACK["plotsize"],
        "money": FALLBACK["money"],
        "binsize": binsize_block(),
    }

    header = (
        "/* html/data/figures.js\n"
        " *\n"
        " * Every number the page draws, in one place. GENERATED by\n"
        " * scripts/build_html_data.py from outputs/ and config.yaml. Do not hand edit.\n"
        f" * generated: {data['meta']['generated']}\n"
        " */\n"
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(header + "window.FH_DATA = " + json.dumps(data, indent=2) + ";\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  grid: {grid['total_cells']} cells, {grid['existing_cells']} existing, {grid['new_cells']} new")
    print(f"  frame: {frame_ac:,} ac, target {data['meta']['target_plots']} plots")


if __name__ == "__main__":
    main()
