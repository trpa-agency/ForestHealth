# Archive: split sample chain, Sept 5 to Oct 18, 2026

Superseded by the Oct 19, 2026 design (`docs/SAMPLE-DESIGN-2026-10-19.md`) and the template notebook `notebooks/00_sample_design_template.ipynb`. Kept for the record and for one piece of logic that may come back.

| File | What it was |
|---|---|
| `notebooks/01_frame.ipynb` | Frame from the CWHR layer and LiDAR metrics, 3 by 3 units, exclusions. Now section 2 of the template. |
| `notebooks/02_strata.ipynb` | LiDAR p95 height and density proxy breaks per type, calibrated to QMD 5 and 25 in. **Still the reference for the height to QMD calibration** if `strata.source` moves to `lidar`. |
| `notebooks/03_allocate_draw.ipynb` | Candidate A and B allocation by structural cell and the split sample selection. Replaced by weights within forest type. |
| `notebooks/04_evaluate.ipynb` | Class coverage, cross tabs, and caty_n checks. Now section 6 of the template. |
| `scripts/build_notebooks.py` | Builder for the four notebooks above. Its paths point at `notebooks/`, so regenerating from here would write into the live folder; do not run it. |
| `scripts/grts_draw.R` | spsurvey selection by structural cell (Sept 5). |
| `scripts/grts_split_draw.R` | spsurvey split sample, Half A by forest type with caty_n, Half B by cell (Sept 19 and 21). |

These read config keys that no longer exist (`split_sample`, `allocation.floor_per_cell`, `allocation.tail_cells`, `draw.oversample_factor`). To run them, check out commit `be76d4c`, the last commit with the matching `config.yaml`.

Why the split sample was dropped: at 120 plots each half would hold 20 per type, and spsurvey's `caty_n` sets expected rather than fixed counts, so Half A's balance was equal probability in practice. See the design record.
