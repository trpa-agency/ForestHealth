# Sample Design, October 19, 2026

**Decided by:** Mason Bindl and Andy McClary, working session October 19, 2026.
**Supersedes:** the split sample (Sept 19), the caty_n balance and Half B weights (Sept 21), the two-stage hex selection (Sept 25), the disturbance weights (Sept 5), and the slope cut, edge buffer, access classes, and oversample factor in `config.yaml` before this date.
**Implemented in:** `config.yaml`, `src/design_template.py`, `scripts/grts_select.R`, `scripts/build_sample_design_template.py` (notebook `00_sample_design_template`), `tests/test_design_oct19.py`.

## What the design has to do

Report VP9 (seral stage and canopy cover, 75 percent standard) and VP10 (stand density, 50 percent standard) by forest type in the 2027 evaluation, from status plots the RFP buys: 120 at the minimum, 150 at the full design.

## Decisions

| Item | Decision |
|---|---|
| Estimator | Model-assisted, with 2022 LiDAR as the auxiliary variable. Plots correct the LiDAR model. |
| Population | The threshold report frame: CWHR conifer types mapped to SMC, JP, and RF, outside the Urban Area and designated wilderness (115,396 acres). |
| Sampling frame | Public land only: `OWNERSHIP_TYPE` Federal, State, or Local. Private and unmapped ground is out. |
| Buffers | 30 m from private parcels, roads, trails, streams, and structures, cut from the frame before selection. |
| Slope | No slope cut. Slopes over 50 percent stay in the frame at half the inclusion probability. Unsafe sites are rejected in the field and logged. |
| Sampling unit | 3 by 3 block of 30 m pixels; the plot is on the centre pixel. |
| Strata | Forest type only. |
| Selection | One GRTS selection in `spsurvey` 5.x, stratified by forest type, `seltype = "proportional"` on a multiplier. |
| Multiplier | 1.5 on RRK tail cells (late seral at or above the VP10 maxima, late seral below them, early seral above them), times 0.5 where centre slope is over 50 percent. Possible values are 0.5, 0.75, 1.0, and 1.5. |
| Tail source | RRK seral stage and stand density assessment rasters on F: (`strata.source: rrk`). |
| Disturbance | No disturbance weights. Disturbance is recorded on every plot under the protocol. |
| Counts | Minimum: 40 SMC, 40 JP, 40 RF. Full: 70 SMC, 40 JP, 40 RF. The full level is the minimum plus the next 30 SMC sites in GRTS order. |
| Backups | The ranked list is 3 times the full target per type: SMC 210, JP 120, RF 120. |
| Replacement rule | A site is rejected only for a logged reason on a fixed list (unsafe, no legal access, not forest on the ground, a feature the buffers missed), with TRPA written concurrence. It is replaced by the next unused rank in the same type. Coordinates are never moved. |
| Access classes | Hike distance from the nearest drivable road along the cheapest path over the terrain, costed as surface distance. Class 1 is under 0.5 mile, class 2 is 0.5 to 1.5 miles, and class 3 is over 1.5 miles. |
| Separation | 100 m minimum between any two sites (spsurvey `mindis`). |
| Legacy sites | None. |
| Freeze | At contract execution in December. The seed (`draw.seed`) is recorded then. Appendix A posts counts by type, access class, and owner with the RFP; coordinates are furnished at execution. |

## Why

**One selection instead of the split sample.** At 120 plots, each half would have held 20 plots per type. The weighted half bought tail coverage, and so does a 1.5 multiplier applied across the whole sample. The single selection costs about 4 to 8 percent of effective sample size (Kish design effect 1.04 to 1.08), and it keeps one ranked list and one weight per site.

**Weights instead of strata on structure.** Structure changes between cycles. Inclusion probabilities fixed at selection keep the estimator unbiased however the forest changes later. Weighting on RRK classes costs efficiency, not validity.

**Balance is reported, not forced.** spsurvey's `caty_n` sets expected counts, not fixed counts. In a test on Oct 19, 2026 (spsurvey 5.7.0, 30 seeds, 40 sites, 10 categories, 4 expected per category), realized counts per category ran from 0 to 9. An area-proportional `caty_n` is therefore the same design as equal probability. The Sept 21 claim that it guaranteed side and landform coverage was wrong. GRTS spatial balance does the spreading. Section 6 of the notebook reports realized against expected counts by side, TPI class, tail, steep, state, and access class.

**Nesting works.** spsurvey orders the over sample so that any prefix, taken in order, stays spatially balanced. In the same test, the east share of the first 30 over sample sites had a standard deviation of 0.04 across 30 seeds, against 0.09 for simple random sampling. So the 30 SMC sites that turn 120 into 150 are a balanced add-on, not a second design.

**Keep steep ground in.** A slope cut would shrink the population the standards are assessed on. It would also leave the LiDAR model with no plot correction on ground that is not a random slice of the forest.

## Precision

All 95 percent confidence interval half widths below are at p = 0.5, the worst case.

| | Design-based | Model-assisted, relative efficiency 1.5 | Model-assisted, relative efficiency 2.0 |
|---|---|---|---|
| 40 per type | plus or minus 15.5 points | about 12.7 points | about 11.0 points |
| 70 SMC | plus or minus 11.7 points | about 9.6 points | about 8.3 points |

[Certain] The design-based numbers are arithmetic. The weights add a design effect of about 1.07 on the synthetic Basin; the notebook reports the real value in section 4.

[Likely] Relative efficiency of 1.5 to 2.0 is the planning range from the Sept 19 sample size review (McRoberts, Liknes and Domke 2014, area proportions).

Forty per type sits below the 55 to 60 plots per type the Sept 19 review set as a floor for honest confidence intervals. That works only because the reporting estimator is model-assisted.

## Stated assumptions

1. **Private land.** Private land is in the population the standards report on but not in the sampling frame. The 2027 estimate for private conifer acres rests on the LiDAR model alone, with no plot correction there. The assumption is that model error on private land behaves like model error on public land. Report the private share of each type's population next to every estimate.
2. **Tail classes.** Tail cells are RRK classes, the product under validation. That is acceptable for weights, because they set inclusion probabilities, not the estimate.

## Open for Andy before the real run

1. Fill in the `# CONFIRM` SDE class names for roads, trails, streams, and structures.
2. Write `access.drivable_where` so it excludes gated, closed, and OHV-only routes.
3. Check that the ownership layer's `OWNERSHIP_TYPE` values match `frame.public_owner_values`, and see where CTC and NDSL parcels fall.
4. Set `balance.tpi_radius_px` and `balance.lake_axis_anchor_xy`.
5. Run `06_tessellation` once so the hex keys come from the real lattice and not the placeholder.
6. Install scikit-image in arcgispro-py3 if it is missing (the access classes fall back to planar distance without it), and install R 4.x with `sf` and `spsurvey`.
7. Run the notebook with `run.synthetic: false` and read section 6. Reseed before the freeze only for a stated, recorded reason. Never move sites.

## Synthetic check (Oct 19, 2026)

The notebook runs end to end with spsurvey 5.7.0 on the toy Basin and produces the following:

- 120 and 150 sites at the two levels, with ranked lists of 210, 120, and 120
- No pairs under 100 m
- spsurvey inclusion probabilities equal to n x mult / sum(mult) within each type, to machine precision
- Mean steep-site count across 25 seeds of 4.1, against 4.3 expected

The frozen-seed selection drew 10 steep sites against 4.3 expected. Section 6 flags results like that one, and it was chance, not a bug. The synthetic numbers mean nothing beyond proving the chain.
