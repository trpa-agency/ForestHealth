# plot-network-design

Builds the sampling frame, LiDAR-based strata, nested allocation, and GRTS plot draw for TRPA's forest health plot network (VP9 seral and canopy cover, VP10 stand density). The output is the plot location layer, allocation table, backup list, and installation order that the field-only RFP references. Read `PLAN.md` first; `docs/METHODS.md` records what the code actually does.

LiDAR base products are produced by `trpa-agency/general-purpose/lidar-2022` and read from `\\vcenter2\GIS_DATA\LiDAR\2022\Derived` via `config.yaml`.

Run the notebooks in order (`01_frame` to `04_evaluate`) with `arcgispro-py3`. `config.yaml` holds every path, break, floor, and share; nothing is hardcoded. With `run.synthetic: true` the chain runs on a generated toy Basin. The frozen draw is made with `scripts/grts_draw.R` (spsurvey) using the frame and allocation exported by notebook 03.
