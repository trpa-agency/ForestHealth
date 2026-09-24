# Plot Network Design Plan: Stratification, Allocation, and Draw

**Owner:** Mason Bindl (mbindl@trpa.gov), with Andy McClary
**Design lead and review:** Becky Estes (R5 Ecology); Shengli Huang (USFS RSL) on plot size, covariates, and the model test; Hugh Safford (UC Davis, TSAC) and Dan Segan on defensibility
**Freeze:** October 16, 2026. **Post:** November 2, 2026. **Award:** before Christmas 2026.
**Last revised:** September 5, 2026 (plain-language overview, LiDAR processing, protocol rationale, communication plan, inputs and outputs table added)

This document is the soup-to-nuts plan for producing the plot location layer, allocation table, backup list, and installation order that the field-only RFP references. It replaces the August 31 methods outline. The code that implements it lives in this repo (`notebooks/`, `src/`, `scripts/`), configured by `config.yaml`, and documented in `docs/METHODS.md`.

> **Revisions since Sept. 5.** Where this document and `config.yaml` disagree, the config is current. Three decisions postdate the text below and are not yet threaded through every section:
>
> 1. **Sept. 19, protocol v1.0.** The plot is a nested fixed-radius design with one centre: a quarter-acre primary plot (58.9 ft) for all trees 4.0 in and larger, a 56.4 m macroplot for trees at or above the breakpoint, a 1/300 acre microplot for saplings, and a 24 ft subplot for understory and fuels. It replaces the 1/7 acre plot in sections 2, 7, and 9 (`plot:` block, `src/plot_geometry.py`, `docs/CHANGES-2026-09-19.md`).
> 2. **Sept. 19, split sample.** Half A is stratified by forest type only and balanced on basin side and landform; Half B is unequal probability by structural cell. It replaces the single Candidate B draw in sections 6 and 7 (`split_sample:` block, `scripts/grts_split_draw.R`).
> 3. **Sept. 23, sampling unit.** The unit is a 3 by 3 block of 2022 LiDAR pixels (90 m, 0.81 ha), the window the imputation model trains on, with the plot on the block's centre pixel. A 30 m pixel is smaller than the primary plot and cannot be the unit. Strata attributes are block means. No two selected sites, legacy included, may be closer than 120 m (two macroplot radii), enforced with spsurvey's `mindis`, so plot footprints never overlap. It replaces "pixel" wherever sections 4, 5, and 7 use it as the sampling unit (`frame.unit_px`, `draw.min_distance_m`).

---

## 0. The plan in plain language

**What we are doing and why.** TRPA adopted new forest health standards. Two of them, seral stage and canopy cover (VP9) and stand density (VP10), say what share of the Basin's forest should look a certain way, and the 2028 evaluation has to report how close we are. Today's numbers come from a model trained on about 30 California field plots and none in Nevada; the Forest Service's own demonstration of the same model used 305. The threshold report calls its models planning-level and records TSAC's request for ground monitoring. So we are building a network of permanent field plots that measure the forest the way the standard is written, at enough places to make 2028 defensible. There is $188K for this year, the plots must go in next summer, and the field contract must be awarded before Christmas.

**Working with TEON (Pat Manley and Shale Hunter).** TEON was funded by TRPA and the Forest Service to design a Basin monitoring system. Its report recommends a spatially balanced network and says plainly it was not designed to meet agency reporting needs. Shale picked 100 of 195 historical wildlife-habitat sites as a backbone with GRTS. Our position: TRPA implements the forest tier of TEON with a protocol that can answer the thresholds; every plot is open data tagged with TEON's site and grid IDs so Pat gets our structure data back at her sites; her team can bid on the field work. What we do not do is adopt her plot design or let TEON own strata, plot size, or protocol, because the MSIM habitat plot only tallies every tree inside a 7 m circle and cannot produce the standard's numbers. If Pat might bid, she gets a briefing and the published design package rather than a seat in design meetings. Update September 23, 2026: Shale confirmed the TEON sites have no monuments and their centers are phone fixes, the first 30 were hand-picked, and the 2025 and 2026 selections ran over a finite list of legacy sites filtered by bird data. TEON sites are therefore out of the sample entirely, as legacy sites or otherwise. What remains with TEON is the shared frame (Pat's extended owl grid with our conifer domain and per-type counts) and co-location in reverse: TEON adds bird stations at TRPA plots once they are installed. See section 8 and 2026-09-23-Meeting-Notes-Shale-Hunter-and-Survey123-Review.md in the project folder.

**Processing the 2022 LiDAR first.** The strata come from the LiDAR and the plots are placed to line up with its pixels, so nothing downstream starts until it exists. The archive is about 2 TB of LAZ on an external drive on the network, and that drive's read speed is the limit. `00a` inventories the drive without opening files, reads tile headers to keep only Basin tiles, samples a few to confirm ground is classified, then on the 32 GB server copies one tile at a time to local disk, builds a bare-earth surface, converts every return to height above ground, and writes a 1 m canopy height tile, a 1 m bare-earth tile, a height-normalized copy of the tile back to the drive, and per-cell counts. Three tiles run at once, every tile is resumable, and the log projects total runtime early. The merge produces 30 m rasters: canopy cover, 95th percentile height, the 2 to 8 m ladder-fuel fraction, densities, and a solid-surface flag that separates roofs and rock from canopy. `00_lidar` adds tree tops per acre and rumple. See section 3.

**Where the plots go.** The standard defines seral stage by tree diameter and density by trees and basal area per acre. Neither exists wall-to-wall except as the model output we are checking, so we cannot place plots on them. LiDAR stands in: height for seral stage, tree-top count or the ladder-fuel fraction for density, with breaks set on the standard's decision points and calibrated against plots that have both diameter and LiDAR height. Cross those with forest type (the exact CWHR mapping from the threshold report) for about 25 cells over the same 115,396 acres the report assessed. Every cell gets at least two plots even at the minimum; rare conditions get extra; mixed conifer gets the most because it is 61 percent of the forest. Fire and treatment areas are targeted at about 15 percent each but flagged, not made strata. Plots are drawn with GRTS, the same tool Shale used, so any prefix of the list is a valid sample and 60 plots this year, 100 next, and 300 eventually are one design. Existing marked plots enter as legacy sites. Shengli tests the design in his model before the October 16 freeze. See sections 5 to 7.

**The protocol, and why not the others.** Fixed radius, 1/7 acre, monumented, survey-grade GPS, every tree above a set diameter, canopy cover as vertical projection, on Becky's LiDAR validation protocol. Fixed radius rather than the Forest Service's variable-radius stand exam because a variable-radius plot has no footprint to line up with a pixel, and the Plumas comparison shows the means agree anyway. One size at 1/7 acre because it sits inside the 30 m pixel Shengli models on. Monuments and survey-grade GPS because position error is the largest noise source at 30 m, which is why 5 to 20 m FIA plots are weak training data. Every tree above a DBH floor plus a small-stem subplot because seral and density are computed from the full tree list, and the small-stem ladder is where density fails today. Not TEON's habitat plot (above). Not Brian's CSE plots: unmonumented, sited where treatments are imminent, and the Forest Service will not maintain them. Stem mapping and scanning stay optional bid items. See section 9.

**The RFP.** The August 31 pivot turned it from "design us a network" into "install these plots this way." TRPA and Becky design in house; the solicitation is a short scope plus boilerplate referencing the furnished plot layer, protocol, allocation table, access classes for pricing, and backup rule. Bidders price a minimum plot count plus a unit price with add-ons if money remains; the budget never appears. Optional modules matching TEON's transects and understory work can be priced at co-located sites, which is Pat's lane. Backward from award before Christmas: post November 2, freeze October 16, model test early October, first draw and Becky regroup mid-September, LiDAR and frame the week of September 8. See section 14.

**This week.** Send the Shale email. Run the LiDAR pre-flight on the server. Get Shengli's grid origin, his TPA definition, and his density metric, since all three must be set before the heavy LiDAR pass. Wire the TRPA REST service URLs into `config.yaml` so the frame runs on real layers.

## 1. Purpose and what the plots must deliver

The plots train and validate a Basin-wide imputed forest structure product and put real precision on VP9 (seral stage and canopy cover, 75 percent target) and VP10 (stand density, 50 percent target) for the 2028 evaluation. The adopted baseline was modeled from about 30 California-side FIA plots; the Forest Service's own demonstration of the same method used 305 plots on the Tahoe National Forest. The threshold report itself calls the models planning-level rather than stand-specific and records TSAC's recommendation to follow with ground monitoring.

Every plot therefore has to produce, exactly as the standard defines them:

| Standard element | Definition in the threshold report | What the plot must measure |
|---|---|---|
| Forest type | CWHR types mapped to SMC, red fir, Jeffrey pine (Table 1 mapping, verbatim) | Assigned from the layer; recorded in the field for QA |
| Seral stage | QMD: early 0 to 5 in, mid 5 to 25 in, late over 25 in | Every tree above the DBH floor, so QMD is computed, not estimated |
| Canopy cover | Vertical projection of crowns; open/closed at 40 percent (JP) and 50 percent (SMC, RF) | Vertical projection method, not densiometer closure |
| Density | TPA and BA maxima by type and seral (JP 200/30, 70/80, 55/100; SMC 300/40, 90/130, 75/180; RF 300/50, 100/175, 80/250) | TPA and BA per plot with the DBH floor fixed to match how RRK/F3 computes TPA |
| Position | Plot co-registered to the 2022 LiDAR | Monumented center, survey-grade GPS, design and field coordinates both recorded |

The DBH floor for TPA is not stated in the threshold report. It is fixed in the protocol before the first plot, matched to the RRK/F3 definition (Shengli to confirm), and written into `config.yaml` so the classification code and the protocol agree.

## 2. Design principles

1. **Strata reach every structural class the model has to predict, including the rare ones.** FastEmap assigns each pixel the mean of the plots in its covariate group and loses variance where groups are thin. VP9 and VP10 are "percent of area inside a range," so variance loss moves attainment for reasons unrelated to the forest. The first plots bought buy coverage; proportional filling comes later.
2. **Strata are allocation-time covariate bins, not analysis strata.** Inference is model-based and refit against each LiDAR epoch; design-based status estimates are post-stratified to the current epoch and carry the GRTS weights. A plot that moves class between epochs is the signal. This is the answer to TEON's "do not pre-stratify."
3. **Any stratum needs a wall-to-wall layer at design time that is not the product under validation.** Seral (QMD) and TPA exist Basin-wide only as RRK rasters. The classes are defined in the standard's units, mapped by 2022 LiDAR proxies, and verified by the plots. RRK rasters are evaluation only.
4. **Cross only the structure axes.** Forest type by seral proxy by density proxy. Disturbance is a flagged sub-allocation; aspect, soils, ownership, access, and treatment status are attributes, checks, or inclusion weights, never strata.
5. **Fixed radius, one plot design, co-registered, on a plot-sized sampling unit.** Nested quarter-acre primary plot with a 56.4 m macroplot (protocol v1.0). The sampling unit is the 3 by 3 LiDAR pixel block Shengli trains on, and the plot centre is that block's centre pixel, so the unit the draw selects, the footprint the crew measures, and the window the model reads are the same piece of ground. Variable-radius plots cannot be co-registered and are not adopted.
6. **Design independently, then fold in existing plots.** Existing permanently marked plots (Lake Tahoe West LiDAR validation plots, Hugh's burned-area plots) enter as legacy sites in the selection or as adopted replacements inside a cell, never by changing the strata. TEON sites are not permanently marked and do not enter (September 23, 2026).
7. **Any prefix of the installation order is a coherent sample.** The minimum authorized quantity, the option task, and future seasons are the same design.

## 3. LiDAR processing (`00a_las_to_chm.ipynb`, `00_lidar.ipynb`)

Source is `\\vcenter2\GIS_DATA\LiDAR\2022\LAZ`, about 2 TB of LAZ on an external drive attached to the network, processed on the 32 GB server. The read speed of that drive sets the pace, so the design is one network read per tile, parallel workers, and per-tile partials so the run can be stopped and resumed. `docs/SERVER_RUN.md` is the runbook.

Steps: drive inventory by folder and extension with no file opens; header-only tile index; AOI filter by header bounds then polygon; classification sample on random tiles to confirm ground (class 2) and CRS; per tile in a pool of three workers, copy to `C:\lidar_scratch`, decompress once in memory (chunked two-pass above 40 M points), DTM from ground returns (mean per 1 m cell, nearest-fill, 3 by 3 smooth), height above ground for every return, 1 m CHM tile (max first-return height, pits filled), 1 m DTM tile, height-normalized LAZ copy to the drive's free space, and a partial with 30 m counts and a 0.5 m height histogram; then an exact merge into 30 m rasters snapped to Shengli's grid origin. Building, water, and bridge classes are dropped from canopy metrics; a solid-fraction raster (single-return share above 2 m) catches roofs and rock the frame layers missed. `00_lidar` reads the CHM tiles for individual tree detection and rumple. Products publish to `\\vcenter2\GIS_DATA\LiDAR\2022\Derived`. Must be set before the heavy pass: `lidar.grid_origin` (Shengli), `lidar.aoi`, `run.synthetic: false`.

### 3.1 Tree approximate objects (TAOs) and LITIDA

**What they are.** A TAO is one LiDAR-detected tree: a top (x, y, height) and a crown polygon segmented from the canopy height model. LITIDA is Shengli Huang's system that takes those detected trees and imputes what LiDAR cannot see for each one (DBH, species probability, site index, age) by learning from field-measured trees that have been matched to their crowns. Like F3, LITIDA is his, not ours to run; our job is to produce the two inputs it needs, the TAO layer and the matched-tree training set, and to validate what comes back.

**Where we are.** `00_lidar` already finds tree tops (local maxima on a smoothed CHM with a height-dependent window) but only counts them per 30 m cell. Producing TAOs is the same detection carried one step further: keep every top as a point and grow a crown around it by watershed segmentation on the CHM. The height-normalized LAZ written by `00a` exists for exactly this: point-cloud segmentation (lidR, `segment_trees` with Dalponte or Silva) is the standard method and starts from normalized returns, not a CHM.

**Plan.**

1. **First pass, in house, from the CHM (`00b_taos.ipynb`, built and tested).** Per CHM tile: smooth, detect tops with the same windows as `00_lidar`, watershed-segment crowns, and write a tree table (tree ID, x, y, height, crown area, crown diameter, max and mean crown height, tile, TEON hex IDs) as GeoParquet plus crown polygons as GeoPackage per tile. Basin-wide this is on the order of 10 to 35 million trees (115,396 acres at 100 to 300 detected trees per acre), which is fine as tiled points and manageable as tiled polygons. Runs on the server from the published CHM tiles; resumable per tile like `00a`.
2. **Second pass, point-cloud segmentation where it matters.** lidR on `LAZ_Basin_HAG` for the plot footprints and a validation sample, because CHM watershed merges crowns in dense fir and splits big pines. Compare the two; if lidR is clearly better, run it Basin-wide on the server (R, `future` multisession, same tile loop). The TAO layer that ships is whichever validates better against plots.
3. **Match measured trees to TAOs.** This is why the protocol needs per-tree position: azimuth and distance from a survey-grade plot center, or a terrestrial scan, at least on a calibration subset. Each measured tree gets the TAO ID whose crown contains its stem (or nearest top within a height-scaled radius), which yields the training pairs LITIDA needs: LiDAR height and crown metrics on one side, DBH, species, and status on the other. Unmatched measured trees (suppressed, under canopy) are recorded as such; their share per plot is the omission rate the imputation has to account for.
4. **Hand Shengli the TAO layer and the matched-tree table; he runs LITIDA.** Outputs come back as per-tree attributes on our TAO IDs. We keep the blind remeasurement subset and a holdout of plots out of the training set and score LITIDA's DBH, species, and derived TPA and BA against them, by forest type and density class.
5. **Use the TAOs ourselves regardless of LITIDA.** Detected-tree TPA per 30 m cell (already the `itd_per_ac` proxy), crown cover from polygon union as a check on the point-based cover, clump and gap metrics for the VP9 open/closed discussion, and, when a 2026 acquisition exists, tree-level change (growth, mortality, removal) by matching TAOs across epochs.

**What TAOs are not.** A TAO count is detected-tree density, not the standard's TPA: it misses suppressed stems under closed canopy, which is the VP10 failure mode. The plots measure that gap and LITIDA models it. TAO tops need the same solid-surface and class screens as the rasters so roofs and rock do not become trees.

**Decisions.** Shengli: LITIDA input format (tree table fields, crown geometry or top only), which detection he prefers to train on, minimum matched trees per plot. Becky: per-tree position in the base protocol or the calibration subset only. Internal: CHM watershed first pass now, lidR second pass after the plots exist.

## 4. Sampling frame

Population = the threshold report's assessment population, 115,396 acres of CWHR conifer types outside TRPA urban areas (mixed-use, residential, tourist) and designated wilderness, excluding montane chaparral, meadow, and water.

| TRPA type | CWHR types included | Acres | Share |
|---|---|---|---|
| Sierran mixed conifer | SMC 55,779; Lodgepole 9,253; White fir 5,877 | 70,909 | 61.4 |
| Red fir | Red fir | 23,037 | 20.0 |
| Jeffrey pine | Jeffrey pine 20,249; Eastside pine 1,192; Juniper 9 | 21,450 | 18.6 |

Frame construction (`01_frame.ipynb`) starts from that population and removes, with area accounting at each step:

- units whose centre is within one primary-plot radius plus the positional tolerance of a road, trail, stream, structure, or parcel boundary where access is not assured (the macroplot may cross an edge; it only tallies trees at or above the breakpoint);
- slope above the safety cutoff (`frame.max_slope_pct`, default 70), recorded so the design report states what the network cannot represent;
- existing plot footprints with a buffer, unless adopted;
- optionally, areas beyond the realistic access distance, or kept and priced as access class 4.

Lodgepole and white fir stay inside SMC. They are not separate strata; they are a reporting attribute.

## 5. Strata

Three crossed axes, each mapped from a layer that exists today.

**5.1 Forest type (3 classes).** From the CWHR layer using the Table 1 mapping.

**5.2 Seral proxy (3 classes).** p95 canopy height from the 2022 LiDAR CHM, cut at breaks calibrated per forest type to the QMD 5 and 25 inch definitions. Initial breaks in `config.yaml` are placeholders (`strata.height_breaks_m`); they are calibrated in `02_strata.ipynb` against plots with both QMD and LiDAR height (Lake Tahoe West validation plots, FIA where coordinates are available), by forest type, and the calibration is written into the design report. Classes: early, mid, late.

**5.3 Density proxy (3 classes).** A 2022 LiDAR stem-density metric, either an individual-tree-detection count per acre from CHM local maxima or a mid-canopy return fraction, cut at breaks that sit on the standard's TPA decision points by type rather than one Basin-wide 80 and 200. Shengli names the metric he trains TPA on; that metric is the proxy. Classes: low, moderate, high. Where the proxy cannot separate three classes in a forest type, collapse to two (`strata.density_classes`).

**5.4 Canopy cover.** Vertical projection above 2 m from the CHM, cut at 40 or 50 percent by type, and a sparse class below 15 percent. Carried as an attribute and used in the evaluation cross-tab; it becomes a fourth axis only if the seral by density cross leaves the open/closed split unrepresented at the minimum quantity (`strata.use_cover_axis`).

Up to 27 cells. Cells below `strata.min_cell_acres` are collapsed into their nearest neighbor within forest type and the collapse is documented. Expect 18 to 24 populated cells. Not strata: aspect, soil, climate zone, ownership, management unit, treatment status, slope, access class, elevation band, ecoregion. Elevation band and TEON's 2/4/8 km hex IDs are carried as attributes.

## 6. Allocation

Total plot counts are nested: the statistical minimum per cell becomes the RFP's authorized floor (`[N MIN]`), the full network (about 300) sits behind it, and the installation order makes any prefix coherent.

**Rule (Candidate B, tail-boosted floor):**

1. Every populated cell gets a floor (`allocation.floor_per_cell`, default 2 at the minimum quantity, 3 to 5 in the full design).
2. Forest type shares are set near-proportional (`allocation.type_shares`, default 0.60 SMC, 0.20 RF, 0.20 JP).
3. Within type, the remainder is distributed toward equal shares across seral and density classes, with early seral held to roughly 20 percent of the type (`allocation.seral_shares`) because it is a small, mostly post-fire and plantation area and the standard only wants 5 to 20 percent of the landscape there.
4. Tail cells (late by high density, late closed, sparse or low density in the late class) are boosted 1.5 times (`allocation.tail_boost`).
5. A Nevada floor is applied within forest type (`allocation.nevada_floor`).
6. A disturbance sub-allocation of about 15 percent post-fire (2007 and later fire perimeters, by severity class) and 15 percent scheduled treatment (TFFT and Lake Tahoe West units 2027 to 2031, so pre-treatment measurements exist) is drawn from the same cells and flagged (`allocation.disturbance_shares`). It is not a stratum.

**Candidate A (proportional to cell area)** is computed alongside for comparison. At 60 plots the two differ sharply; at 300 they converge. Shengli's imputation test arbitrates.

First numbers at three nested levels, forest type shares 0.60/0.20/0.20, nine cells per type, floor of 2:

| Type | Cells | n = 60 | n = 100 | n = 300 |
|---|---|---|---|---|
| SMC | 9 | 36 | 60 | 180 |
| Red fir | 9 | 12 | 20 | 60 |
| Jeffrey pine | 9 | 12 | 20 | 60 |

The R5 LiDAR verification booklet's rule of at least 20 plots per LiDAR stratum is the full-network check: 18 to 24 cells at 15 to 20 each lands in the same 300 range as the statistical calculation and the Tahoe National Forest precedent.

## 7. Drawing the sample

**7.1 Method.** Generalized Random Tessellation Stratified (GRTS) sampling, stratified by cell, with unequal inclusion probabilities carrying the tail boost and the disturbance sub-allocation, and with existing permanently marked plots supplied as legacy sites so new plots balance spatially around them. The reverse hierarchical order is the native installation order.

Two implementations, deliberately:

- `src/strata.py::grts_draw` is a compact Python GRTS (hierarchical quadrant addressing, random permutation at each level, reverse hierarchical ordering, systematic selection along the ordered line with unequal probabilities). It is for iterating in the notebooks.
- `scripts/grts_draw.R` calls `spsurvey::grts()` with the same frame, strata, inclusion probabilities, legacy sites, and seed. The **frozen** draw is the spsurvey draw, because Shale Hunter built TEON's backbone in spsurvey and parity with that tool is what makes "one draw, two networks" defensible.

**7.2 Oversample.** Two to three times the allocation per cell (`draw.oversample_factor`). Extras are the backup list (plot A/B) in GRTS order.

**7.3 Installation order.** Interleave cells round-robin, floor and tail cells first, then proportional fill; within a cell, GRTS rank (or representativeness rank if Shengli's raster arrives and `draw.weight_by_representativeness` is on). Levels are labeled `min`, `option`, `full`.

**7.4 Backup rule.** A backup replaces a primary only with TRPA's written concurrence for access denial, safety, or site not as mapped, and the replacement is recorded with the reason.

**7.5 Point placement.** The draw selects sampling units, 3 by 3 blocks of 2022 LiDAR pixels; the plot centre is the centre pixel's centre. No two selected sites, legacy included, are closer than 120 m (`draw.min_distance_m`, spsurvey `mindis`), so no two macroplots overlap. The centre is never moved within the unit: a random location inside the block would break co-registration with the model grid, and access problems are what the backup list is for. Design coordinates and field-established coordinates are recorded separately.

## 8. Existing plots, TEON, and the communication plan

Order of operations: select independently first, then overlay. Updated September 23, 2026: TEON sites removed from the legacy list (no monuments, phone-fixed centers, cannot be re-occupied; see the Sept 23 meeting notes in the project folder).

1. **Lake Tahoe West LiDAR validation plots (~60, Becky).** Same protocol family. Each that falls in a cell and can be re-GPSed to the positional standard replaces a drawn plot in that cell.
2. **Hugh's burned-area permanent plots.** Same rule, and they satisfy part of the post-fire sub-allocation.
3. **TEON's 100 GRTS sites (Shale).** Not adopted. No monument at any site, centers are tablet fixes with no accuracy record, and the 2026 protocol on 44 of the 100 sites recorded DBH and a prism count only. A plot installed at the coordinate would be a new plot next to an unmarked point with nothing to co-register. TEON keeps the frame relationship: Pat's extended owl grid is the all-lands frame, our conifer area is a domain inside it, and TEON can add bird stations at TRPA plots after installation. The 2024 and 2025 tree tables are a site-scale cross-check at most.
4. Variable-radius CSE, ecology, and meadow plots are not adopted.

All plots are tagged with TEON's 2, 4, and 8 km hex IDs and published open on LTInfo and Tahoe Open Data under a schema that joins to TEON site IDs. That is what "TRPA implements TEON's forest tier" means operationally.

**Communication plan.**

| Step | Who | What | When |
|---|---|---|---|
| Email Shale | Mason | Done Sept 9 and answered Sept 23: no monuments, phone-fixed centers, protocol by year in the Survey123 forms. Remaining ask is only the grts() call, frame, and seed for the 2026 selection, because the frame agreement depends on the ranking | Sept 24 |
| Summary to Andy and Beth | Mason | What TRPA holds from Pat and Shale so far (report, appendices, shapefile, what the 100 sites are, what the MSIM plot measures) | Before the Tuesday or Wednesday strategy session |
| Note to Pat and Shale | Mason | Withdraw the position and tree table asks; confirm TRPA selects on the shared frame with its conifer domain counts; offer bird stations at TRPA plots after installation; plot coordinates published at the freeze | Sept 24 |
| Frame agreement Pat, Shale, Andy, Mason | Mason | One frame, conifer domain, per-type counts, seed. Settled by Sept 30 or TRPA selects its own Oct 16 | Sept 30 |
| Briefing package to PSW | Mason | Published design and protocol package at posting, same as every bidder; no design-group seat if PSW may bid | November 2 |

## 9. Protocol, and why not the alternatives

| Choice | Why | Alternative rejected | Why rejected |
|---|---|---|---|
| Fixed radius, 1/7 acre (13.6 m) | Sits inside the 30 m pixel; co-registers to the LiDAR; one size for every plot | Variable-radius CSE (prism) | No footprint to align with a pixel; the Plumas 57-plot comparison shows means agree, so nothing is gained |
| Every tree above a DBH floor matched to how RRK/F3 computes TPA, plus a nested small-stem subplot | QMD, TPA, and BA are computed from the full tree list exactly as VP9 and VP10 define them; small stems are the ladder that fails VP10 | Size-class nested subplots (MSIM: all trees only inside 7.3 m) | Cannot produce plot-level QMD, TPA, or BA at a co-registrable size |
| Monumented center, survey-grade GPS, design and field coordinates both recorded | Position error is the dominant noise at 30 m; a new survey-grade plot is worth more per plot than an old one | FIA plots (5 to 20 m accuracy), unmonumented CSE | Weak training data; cannot be revisited |
| Canopy cover as vertical projection | The standard defines it that way, with the 40 and 50 percent cutoffs | Densiometer or moosehorn closure | Different quantity; TEON's own results show the instruments disagree |
| Becky's LiDAR validation protocol (CSE/FIA hybrid) as the base | Built for exactly this use; ~60 Lake Tahoe West plots already on it; R5 booklet precedent | Vanilla R5 CSE; TEON MSIM; Brian's CSE plots | CSE is variable-radius; MSIM is a habitat plot; Brian's plots are unmonumented, sit where treatments are imminent, and will not be maintained |
| Tiered variables: T1 threshold metrics, T2 fuels, T3 understory | The first plots bought buy the threshold answer; extras only if unit cost allows | Full TEON transect suite as a requirement | Doubles field time; optional add-on module instead |
| Stem mapping or scanning as optional bid items | Enables LITIDA training and archived point clouds if affordable | Requiring it | Cost and governance (equipment and affiliation neutrality) |

## 10. Access class and cost

Every primary and backup plot gets an access class for unit pricing (`access.classes`): Class 1 within 400 m of a drivable road and slope under 30 percent; Class 2 within 1.5 km or slope 30 to 50; Class 3 beyond that or slope 50 to 70; Class 4 overnight or special access. Definitions and counts go in RFP Appendix A. Unit costs (Forest Service CSE contracts, North Yuba fixed-radius contract via Kristen Wilson at TNC) convert the budget into `[N MIN]` by class mix. Budget never appears in the RFP.

## 11. Blind remeasurement subset

Five to ten percent of the minimum quantity, spread across cells and access classes, weighted to tail cells, kept internal (`draw.remeasure_share`). Stripped from every published layer.

## 12. Evaluation before freeze (`04_evaluate.ipynb`)

1. Class coverage: plots per cell at each nested level under both candidates; cells below floor flagged.
2. Threshold class check: cross-tab the sample against RRK seral, canopy, and density classes by forest type; every VP9 and VP10 class, attaining and non-attaining, represented at the minimum quantity.
3. Covariate balance: sample versus frame distributions for elevation, heat load, TPI, slope, aspect, soils, and any covariate Shengli names, overall and by type (Kolmogorov-Smirnov and standardized mean difference).
4. Representativeness: distribution of Shengli's F3 representativeness raster at sample points versus the frame.
5. Model test: Shengli runs imputation plus LOOCV against both candidates at `min` and `full`; one iteration, then freeze.
6. Practicality: counts by landowner and access class against unit costs; NF monumentation feasibility by unit (Brian Garrett); crew-days against a May to August season.
7. Review: Becky on strata and protocol fit; Brian on NF monumentation; Dan and TSAC on defensibility.

## 13. Inputs and outputs

All paths are in `config.yaml` (`sources:` for inputs, `lidar:` and `paths:` for outputs). Nothing is hardcoded. Resolution is native unless stated; every 30 m product shares one grid snapped to `lidar.grid_origin`, CRS EPSG:26910.

### Inputs

| Input | Resolution or type | Purpose | Source | Status |
|---|---|---|---|---|
| 2022 LiDAR LAZ tiles | Point cloud, 8 to 30 pts per m2 expected | DTM, CHM, all structure metrics | `\\vcenter2\GIS_DATA\LiDAR\2022\LAZ` | In hand, about 2 TB |
| CWHR vegetation (threshold assessment layer) | Polygon | Frame population and forest type stratum via Table 1 mapping; AOI for the LiDAR pass | TRPA (file or REST) | In hand |
| TRPA urban boundary (mixed-use, residential, tourist) | Polygon | Frame exclusion | TRPA | In hand |
| Designated wilderness | Polygon | Frame exclusion | LTBMU / TRPA | In hand |
| Roads, trails, streams, structures, parcels | Line and polygon | Edge buffers (15 m), road distance for access class | TRPA, LTBMU | In hand |
| DEM (or the 1 m DTM produced here) | 10 m (or 1 m) | Slope cutoff, aspect, heat load, TPI, elevation for covariate checks | TRPA / `00a` | In hand |
| Ownership, state line | Polygon | Nevada floor, landowner counts | TRPA | In hand |
| TFFT and Lake Tahoe West treatment units 2027 to 2031 | Polygon | Treatment sub-allocation (pre-treatment plots) | TFFT, LTBMU (Brian) | Requested |
| Fire perimeters and severity 2007 to present | Polygon or 30 m raster | Post-fire sub-allocation | MTBS / CAL FIRE / LTBMU | In hand |
| Soils (SSURGO), climate zones | Polygon / raster | Covariate balance only, never strata | NRCS, Shengli | In hand / requested |
| Shengli's covariate stack | 30 m | Weighting, balance checks, and the grid origin everything snaps to | USFS RSL | Requested |
| F3 representativeness raster | 30 m | Optional inclusion weighting; evaluation | USFS RSL | Requested |
| RRK Sierra rasters: seral (v4.3), canopy cover, TPA, BA, SDI, VP9 and VP10 attainment | 30 m | Evaluation cross-tabs only, never strata | RRK Sierra | In hand |
| Lake Tahoe West LiDAR validation plots (~60) | Points with tree lists | Height-to-QMD calibration; legacy sites | Becky Estes | Requested |
| Hugh Safford burned-area plots | Points | Legacy sites; post-fire sub-allocation | UC Davis | Requested |
| TEON 100-site GRTS layer, 195-site pool, 2/4/8 km hex grids | Points, polygons | Hex ID attribute and frame; not legacy sites (no monuments) | Shale Hunter (PSW) | Pool and site tables in hand |
| FIA plots with true coordinates | Points | Calibration; evaluation | RSL / PNW / RMRS | Access requested |
| Threshold definitions (QMD breaks, cover cutoffs, TPA and BA maxima, CWHR mapping) | Table | Class definitions and frame | Threshold report, in `config.yaml` `threshold:` | In hand; DBH floor pending Shengli |

### Outputs

| Output | Resolution | Purpose | Written by | Lands in |
|---|---|---|---|---|
| Drive inventory (`drive_inventory.csv`) | Table | What the 2 TB actually is, by folder and extension | 00a | outputs, Derived |
| LAS tile index (`las_tile_index.gpkg`, `.csv`) | One record per tile | Extent, count, density, ground share, CRS; AOI selection; QA map | 00a | outputs, Derived |
| Height-normalized LAZ (`<tile>_hag.laz`) | Native point cloud | Reusable base for any future metric, scan calibration, 2026 change | 00a | `LAZ_Basin_HAG` on the drive |
| Bare-earth DTM tiles plus VRT | 1 m | Slope, aspect, TPI, heat load; frame cutoff; navigation | 00a | Derived `dtm_1m_tiles` |
| Canopy height model tiles plus VRT | 1 m | Individual tree detection, rumple, visualization, plot navigation packets | 00a | Derived `chm_1m_tiles` |
| Per-tile partials (`.npz`) | 30 m counts and 0.5 m height histogram | Resume state; exact merge | 00a | server local only |
| Canopy cover (`lidar2022_cover_30m.tif`) | 30 m | Cover class (sparse under 15, open/closed at 40 or 50 percent); primary strata input | 00a | Derived `metrics_30m` |
| Canopy cover above 5 m (`_cover5m_`) | 30 m | Becky's second break; evaluation | 00a | Derived `metrics_30m` |
| p95 height (`lidar2022_p95_30m.tif`) | 30 m | Seral proxy, calibrated to QMD 5 and 25 in | 00a | Derived `metrics_30m` |
| Mid-canopy fraction 2 to 8 m (`_midcanopy_`) | 30 m | Ladder-fuel proxy; candidate density proxy | 00a | Derived `metrics_30m` |
| Return density, ground density | 30 m | Data quality flags for the tile index and the frame | 00a | Derived `metrics_30m` |
| Solid fraction (`_solid_frac_`) | 30 m | Roof and rock screen; cells above 0.85 dropped from the frame | 00a | Derived `metrics_30m` |
| Tree tops per acre (`_itd_per_ac_`) | 30 m from 1 m CHM | Candidate density proxy for the TPA classes | 00_lidar | Derived `metrics_30m` |
| TAO tree table (`taos_trees_2022.parquet`) and crown polygons per tile | Per tree, from 1 m CHM (first pass) or normalized LAZ (lidR second pass) | LITIDA input; detected-tree density; crown cover, clump and gap metrics; 2022 to 2026 tree-level change | 00b_taos, `segment_trees_lidr.R` | Derived `taos` |
| TAO density (`lidar2022_tao_per_ac_30m.tif`) | 30 m | Detected trees per acre on the shared grid; cross-check of the ITD proxy | 00b_taos | Derived `taos` |
| Matched-tree training table (planned) | Per measured tree with TAO ID | LITIDA training and validation; omission rate per plot | after field season | outputs, to Shengli |
| Rumple (`_rumple_`) | 30 m from 1 m CHM | Heterogeneity attribute | 00_lidar | Derived `metrics_30m` |
| CHM-based cover and p95 (`_chm_` names) | 30 m | Comparison to point-based versions; stand-in when 00a did not run | 00_lidar | Derived `metrics_30m` |
| Sanity figures (`las_checks.png`, `lidar_checks.png`) | Figures | Cover versus height, ITD versus cover, mid-canopy versus cover | 00a, 00_lidar | outputs |
| Frame (`frame.parquet`) and `frame_accounting.csv` | One row per 30 m pixel | Sampling frame with LiDAR metrics, slope, road distance, state, owner, disturbance flags, access class; acres removed per exclusion step | 01 | processed, outputs |
| Cell table (`cells.csv`, `cells_by_cover.csv`, `cell_collapse_log.csv`) | One row per stratum cell | Acres per cell; collapse decisions; cover distribution per cell | 02 | outputs |
| Classified frame (`frame_classified.parquet`) | Per pixel | Seral, density, cover class and cell ID per pixel | 02 | processed |
| Allocation table (`allocation_table.csv`) | Per cell and level | Candidates A and B at min, option, full; Nevada floor check; RFP Appendix A | 03 | outputs |
| Plot design layer (`plots_design_<date>.gpkg`, plus `_internal`) | Points, design coordinates on pixel centers | Primary, backup, legacy plots with cell, level, installation order, GRTS weight, access class, flags; internal copy carries the blind remeasurement flag | 03 | outputs; published to Tahoe Open Data at posting |
| spsurvey inputs (`frame_points.gpkg`, `allocation_full.csv`, `legacy_sites.gpkg`) and frozen draw (`grts_draw_spsurvey.gpkg`) | Points | The frozen design drawn with the same tool as TEON's backbone | 03, `grts_draw.R` | processed, outputs |
| Evaluation tables (`eval_class_coverage.csv`, `eval_vp9_crosstab.csv`, `eval_vp10_crosstab.csv`, `eval_covariate_balance.csv`, `eval_practicality.csv`) and `qa_report.csv` | Tables | Coverage by cell and level; threshold-class representation; sample versus frame balance; owner, access, crew-day counts; QA | 04 | outputs |
| Design summary (`docs/DESIGN_SUMMARY.md`) | Document | Objective, inputs, frame, strata and calibration, allocation, draw method and seed, evaluation, what the network cannot represent, backup rule text; attached to the RFP | Mason | docs |
| Run logs and dated config snapshots | Text | Reproducibility; every run records its parameters | all | logs, Derived |

## 14. Schedule

| Window | Work | Notebook |
|---|---|---|
| Sept 8 to 12 | LiDAR pre-flight and heavy pass on the server; frame, forest type, exclusions, access classes; Shale email; request Shengli's grid origin, stack, and raster; receive Becky's plots and the North Yuba contract | 00a, 00, 01, 02 |
| Sept 14 to 18 | First draw at three nested levels under both candidates; mid-September regroup with Becky on strata, protocol, and RFP draft | 03 |
| Sept 21 to Oct 2 | Shengli review of plot size, proxies, and candidates; overlay LTW, burned-area, and TEON plots; protocol adaptation; Survey123 forms start | 03, 04 |
| Oct 5 to 16 | Model test result, one iteration, final spsurvey draw, allocation table, `[N MIN]` set against unit costs, Dan and TSAC review; **freeze October 16** | 03, 04 |
| Oct 19 to 30 | Design and Protocol Package assembled and attached to the RFP for approval routing | docs |

## 15. Decisions to settle

- **Shengli:** DBH floor for TPA as RRK computes it; 1/7 acre rationale and plot-to-pixel rule; pixel versus 3 by 3 window training; which LiDAR metric predicts TPA; which candidate allocation; whether the model test can turn around by early October.
- **Becky:** height and density breaks per forest type; cell floor and tail boost; Nevada floor; disturbance sub-allocation size; which of the ~60 LTW plots qualify; Tier 2 fuels in or out of the required set; per-tree position as an optional item.
- **Shale:** the grts() call, frame, and seed for the 2026 selection, and which site_order (2025 or 2026 table) is the ranking of record. Monument status answered Sept 23: none.
- **Brian:** NF monumentation authorization lead time, started before posting; TFFT polygons 2027 to 2031.
- **Internal:** minimum quantity once unit cost benchmarks arrive; slope cutoff and access class thresholds; whether cover becomes a fourth axis; how Pat and PSW are briefed if they may bid (briefing and published package, not a design-group seat).

## 16. How to run

```
conda activate arcgispro-py3           # or use the ArcGIS Pro Python directly
pip install pyyaml python-dotenv       # if missing; see environment.md
jupyter lab
```

Run `notebooks/00a_las_to_chm.ipynb` (raw 2022 LAS tiles to DTM, 1 m CHM tiles, and point-based 30 m metrics), then `00_lidar.ipynb` (ITD and rumple from the CHM), optionally `00b_taos.ipynb` (tree objects), then `01_frame.ipynb` through `04_evaluate.ipynb` in order. Each notebook loads `config.yaml`, logs to `logs/`, writes intermediates to `data/processed/`, and review files to `outputs/`. Set `run.synthetic: true` to exercise the whole chain on a generated toy Basin before real layers are wired in. For the frozen draw, export the frame and allocation from notebook 03 and run `Rscript scripts/grts_draw.R`.
