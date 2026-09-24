# Lake Tahoe Basin Forest Health Plot Protocol

**Version 1.0 DRAFT, September 19, 2026**
Tahoe Regional Planning Agency, Forest Health Threshold Monitoring
Part of the Design and Protocol Package furnished under RFP 27#### (Forest Health Plot Establishment and Measurement)

---

## 1. Purpose and design basis

This protocol produces the field measurements needed to assess Threshold Standards VP10 (Stand Density) and VP9 (Seral Stage and Canopy Cover), and to validate the modeled forest structure products those indicators are currently derived from.

The protocol follows a layered construction. The core is the Forest Inventory and Analysis Phase 2 field protocol as implemented by the Pacific Northwest research station for California. On top of that core sits a LiDAR co-registration layer, which adds a small number of measurements and tightens several tolerances. Fuels and understory tiers complete the design. Roughly ninety percent of the content is standard FIA; the deviations are listed explicitly in Section 9 so that a reader familiar with FIA can find them quickly.

Three considerations drove the design.

First, the plot has to be large enough that positional error does not dominate the LiDAR comparison. The published evidence is consistent on this point. Chirici et al. (2024) found that plots below 300 square meters are not recommended for inventory at all, that a 400 to 500 square meter minimum is needed, and that above that size a co-registration error of up to four meters only marginally affects estimates in coniferous stands. Hernández-Stefanoni et al. (2018) found that a 1,000 square meter plot produced accurate biomass estimates that were robust to location errors up to ten meters, and that shrinking to 80 square meters raised RMSE by roughly a factor of four. Yang et al. (2023) recommend plots of at least 0.25 hectares for calibrating gridded products, with sharply diminishing returns above that. The quarter-acre primary plot specified here is 1,012.5 square meters, which sits at the Hernández-Stefanoni recommendation and at twice the Chirici minimum.

Second, the plot has to be readable against the other plot families in the Basin. The Lake Tahoe West LiDAR validation plots follow a CSE-based fixed-radius design, and TEON's MSIM and LTUB sites use concentric 7.3 meter, 17.6 meter, and 56.5 meter tiers. The geometry specified here keeps both readable without a crosswalk: the 7.3152 meter FIA subplot matches the TEON inner tier, the quarter-acre plot at 17.95 meters contains their 17.6 meter tier, and the 56.4 meter macroplot is their large-tree ring. TEON sites are not monumented and are not adopted as plots (their centers are tablet fixes with no accuracy record, and 44 of the 100 sites carry only DBH and a prism count). The shared geometry is there so TEON tallies can serve as a cross-check and so TEON can add wildlife stations at TRPA plots later without a schema change.

Third, canopy cover has to be measured in a way that can actually be compared to a remote sensing product. Section 5 explains why the standard FIA canopy cover value cannot serve that purpose and what replaces it. This is the largest single deviation from FIA core in the protocol and the one most likely to be questioned, so the rationale is given at length.

---

## 2. Plot geometry

Every plot is a single set of concentric fixed-radius circles sharing one center. Fixed radius is mandatory. Variable-radius sampling cannot be co-registered to a LiDAR footprint because the sampled area differs by tree, so prism and angle-gauge methods are not acceptable under this protocol for any tier.

| Sampling unit | Radius (ft) | Radius (m) | Area (ac) | Area (m²) | Tally rule | Trees per acre per tree |
|---|---|---|---|---|---|---|
| Microplot | 6.8 | 2.0726 | 0.0033349 | 13.497 | Seedlings under 1.0 in counted by species; saplings 1.0 to 3.9 in measured | 299.861 |
| Vegetation and fuels subplot | 24.0 | 7.3152 | 0.0415417 | 168.11 | Understory cover and fuels reference footprint; no separate tree tally | not applicable |
| **Primary plot** | **58.9** | **17.9527** | **0.2502030** | **1,012.54** | **All live trees and snags 4.0 in DBH and larger, up to the breakpoint** | **3.99676** |
| Large-tree macroplot | 185.0 | 56.400 | 2.469324 | 9,992.98 | All live trees and snags at or above the breakpoint diameter | 0.404969 |

**Breakpoint diameter is 24.0 inches** and is recorded as a plot attribute, not assumed as a constant. FIA sets this value regionally: 24 inches in California under the Pacific Northwest station, and 21 inches in the Interior West region that covers the Nevada side of the Basin. Because this network spans both states, the value must travel with the record. Twenty-four inches was selected because it matches the California FIA convention and sits within half an inch of the MSIM 60 centimeter tier, which keeps both comparisons open.

Trees at or above the breakpoint are tallied on the full 56.4 meter macroplot, including the portion of it that falls inside the primary plot, and carry the macroplot expansion factor. They are not also tallied on the primary plot. This follows the FIA database rule rather than the field manual's annular wording, and it is the convention that avoids double counting.

Tally inclusion is decided by horizontal distance from plot center to the center of the bole at ground level. A tree is in if that distance is less than or equal to the plot radius. Measurement tolerances stated elsewhere in this protocol do not apply to the in-or-out decision, which must be made without error.

### 2.1 Why the quarter acre rather than 1/7 acre

Earlier drafts of this work carried a 1/7 acre fixed plot at 44.5 feet, attributed to Region 5 Common Stand Exam convention. That size does not appear in the Region 5 Field Guide, the Common Stand Exam User Guide design chapter, or the national Common Stand Exam plot size table. The standard sizes in that table nearest to it are 1/5 acre at 52.6 feet and 1/4 acre at 58.9 feet, and 1/5 acre is the size the Region 5 guide recommends for forests with widely spaced large trees. The 1/7 acre figure should be verified with its source before it is cited again, and it is not used here.

The quarter acre has three advantages beyond size. It is exactly the FIA macroplot radius, so the geometry is directly comparable to every FIA plot in the region. It is a standard Common Stand Exam plot size. And the edge effect from crown overhang, which scales as the ratio of perimeter to area, is 59 percent smaller at 17.95 meters than at the 7.32 meter FIA subplot.

---

## 3. Plot center position

Plot center position is the measurement that determines whether any of the rest of the plot data can be compared to LiDAR, and it is the measurement most often done badly.

**Standard.** Survey-grade multi-frequency multi-constellation GNSS receiver, mounted on a tripod or fixed-height rod directly over the monument, minimum fifteen minutes of static occupation, raw observations logged, post-processed against a CORS reference. Datum NAD83(2011), coordinate system UTM Zone 10 North, orthometric heights on GEOID18. This mirrors the FIA High Performance GNSS standard, which requires a survey-grade receiver on a tripod over each subplot center for a minimum fifteen minute occupation, and which exists for exactly this reason.

**Target accuracy.** Under one meter horizontal at plot center. Chirici et al. found that co-registration error up to four meters only marginally degrades estimates in coniferous stands at this plot size, so one meter provides substantial headroom. Aspen and other deciduous stands are the documented exception where sub-meter accuracy genuinely matters, so plots in aspen are flagged and held to a sub-meter requirement without exception.

**Real-time corrections are not sufficient on their own.** A 2024 evaluation of survey-grade RTK receivers under dense canopy with thirty second occupations reported horizontal RMSE of 2.03 meters, obtained no fixed solutions at all, and fell back to code-based differential positioning for roughly 97 percent of determinations. Crews must log raw observations and post-process. A real-time fixed solution, where one is achieved, is recorded alongside the post-processed position but does not replace it.

**Offsets.** Offsets are discouraged and permitted only where the canopy defeats reception entirely, or where a rock face or hazard prevents tripod setup. Where an offset is used, occupy an open-sky point, record azimuth to the monument to the nearest degree and horizontal distance to the nearest tenth of a foot with a laser rangefinder, and record the offset as its own set of fields. A traverse of more than two legs is not acceptable.

**Recorded metadata.** Receiver make and model, antenna height, occupation start and end time, number of epochs, PDOP, solution type achieved, post-processing software and base station or network used, final horizontal and vertical accuracy estimates, and offset fields where applicable. Every one of these is a field in the schema. A position without its accuracy metadata cannot be used for validation and will be rejected in quality assurance.

---

## 4. Tree measurements

### 4.1 Tier 1 variables, collected on every tree on every plot

Recorded for all live trees and snags 4.0 inches DBH and larger on the primary plot, and at or above the breakpoint on the macroplot.

| Variable | Units and precision | Tolerance | Notes |
|---|---|---|---|
| Tree tag number | integer | no errors | Permanent aluminum tag, nail set to allow growth |
| Species | NRCS PLANTS symbol | no errors | Minimum 99 percent agreement in blind check |
| Status | live, standing dead, down | no errors | |
| DBH | inches to 0.1, round down | plus or minus 0.1 in per 20 in of diameter | Measured at 4.5 ft on the uphill side |
| Diameter measurement height | feet to 0.1 | plus or minus 0.2 ft | Recorded where DBH is taken off 4.5 ft |
| Total height | feet to 0.1 | plus or minus 5 percent under 60 ft, plus or minus 10 percent at or above 60 ft | Laser hypsometer required; tighter than the FIA flat 10 percent |
| Height to live crown base | feet to 0.1 | plus or minus 5 percent | **Added variable.** FIA Phase 2 does not carry crown base height; it records compacted crown ratio only, and crown base height is a Phase 3 variable. LiDAR canopy base height cannot be validated without it |
| Compacted crown ratio | percent, 2 digit | plus or minus 10 percent | Retained for FIA comparability |
| Crown class | dominant, codominant, intermediate, overtopped, open grown | no errors | |
| Crown width | two perpendicular diameters, feet to 0.1 | plus or minus 10 percent | **Added variable.** Long axis and the axis at 90 degrees to it at the widest point. Required for the crown cover reconciliation in Section 5 |
| Damage agents 1 to 3 | FIA damage agent codes | | Up to three per tree |
| Dwarf mistletoe rating | Hawksworth 0 to 6 | plus or minus 1 class | Required on all live conifers except juniper and incense cedar. Core Optional in FIA but a major structural driver in this Basin |
| Decay class | 1 to 5 | plus or minus 1 class | Standing dead only |
| Azimuth from plot center | degrees, 001 to 360 | see Section 4.2 | |
| Horizontal distance from plot center | feet to 0.1 | see Section 4.2 | |

DBH is recorded to 0.1 inch on every tree regardless of the 4.0 inch floor so that trees per acre, basal area, and quadratic mean diameter can be recomputed at any floor. This matters because the adopted threshold baseline may have been computed at a different floor, because FIA uses 5.0 inches, and because the MSIM network uses 12.5 centimeters. Recording the measurement rather than the class keeps every comparison available.

### 4.2 Tier 1 LiDAR co-registration layer, tree position

Per-tree position is priced as a separate line item in the solicitation and is required on the co-registration subset of plots. Where it is collected, the tolerances are tighter than FIA core and the reason is arithmetic.

FIA allows plus or minus 10 degrees of azimuth on tally trees. At the 58.9 foot plot edge that alone is 3.13 meters of lateral displacement, which exceeds the crown radius of a mature Sierra conifer. Individual tree detection cannot be validated against stem maps built to that tolerance.

**Required where per-tree position is collected:**

- Azimuth to plus or minus 2 degrees, sighting compass with declination set and verified daily against a known bearing.
- Horizontal distance to plus or minus 0.1 foot, laser rangefinder, measured to the bole center at ground level.
- Combined per-tree positional error under 0.5 meters at the plot edge.

Where the crew cannot achieve this from plot center because of intervening stems, a single offset station within the plot may be used, with its own azimuth and distance from center recorded to the same tolerance.

### 4.3 Saplings and seedlings

On the 6.8 foot microplot. Saplings 1.0 to 3.9 inches DBH receive species, status, DBH, and total height. Seedlings under 1.0 inch DBH are counted by species, with conifers counted at 0.5 feet of length or greater and hardwoods at 1.0 foot or greater.

---

## 5. Canopy cover

### 5.1 Why the standard measurements do not work here

VP9 splits open from closed canopy at 50 percent cover, and at 40 percent in Jeffrey pine. Attainment of that standard therefore turns on a number measured near the middle of the range. Three facts make the standard approaches unusable at that point on the scale.

The FIA condition-level canopy cover value carries a tolerance of plus or minus one class, where the classes are 0 to 5, 6 to 7, 8 to 9, 10 to 12, 13 to 15, 16 to 19, 20 to 24, 25 to 49, 50 to 74, and 75 to 100. The classes are tight near the ten percent forest land threshold and very wide above it. In the range that decides VP9, the tolerance is roughly plus or minus 25 percentage points. It is a land classification instrument, not a structural measurement.

Ocular estimation and the spherical densiometer both fail for different reasons. Korhonen et al. (2006), benchmarking against a 195-point control, found ocular estimates biased low by 6.4 and 16.2 percentage points for two observers. The spherical densiometer at 49 points was nearly unbiased on average, at minus 0.1 percent, but carried a standard deviation of 9.7 percent, roughly seven times that of the control method. An unbiased method with ten percent noise per plot is still poor validation data. The densiometer has a further structural problem: its angle of view is roughly 60 degrees, so it integrates canopy well outside the plot. On a plot with a twenty meter canopy, the cone it samples extends far beyond the footprint the LiDAR is clipped to.

The third and most important problem is definitional. Ma et al. (2019), working in the Sierra national forests, found that disagreement between two LiDAR-derived cover products was driven mainly by whether within-crown gaps were treated as cover. Field cover as FIA defines it, whether by the crown ellipse method or the Daubenmire vegetation profile method, includes within-crown gaps; the instruction is explicit that crown widths are not compacted regardless of how sparsely leafed the tree is. A LiDAR first-return cover fraction above a height threshold excludes them. The result is a systematic one-directional bias in which field cover exceeds LiDAR cover, and the gap widens in open-crowned species. In this Basin that means Jeffrey pine and red fir, which are precisely the types where VP9 is furthest from target. A validation campaign that ignores this will measure a definitional artifact and report it as model error.

### 5.2 What this protocol requires instead

A vertical point intercept grid, read with a moosehorn or a vertical densitometer, both of which have an effective angle of view at or near zero degrees and therefore measure vertical projection rather than closure.

**One hundred points per plot.** Twenty-five points on each of the four fuels transects, at two foot intervals from 3.0 feet to 51.0 feet from plot center. Jennings et al. (1999) argue that fewer than 100 points per plot is not meaningful; Ganey and Block (1994) set a floor of 20. The higher figure is adopted.

**At each point, two independent determinations are recorded:**

- **Crown cover.** A hit if the vertical line falls anywhere inside the outer perimeter of the natural spread of a live crown, with within-crown gaps counted as cover. This is the definition FIA and the threshold standard use.
- **Effective cover.** A hit only where foliage or woody material actually intercepts the vertical line. This is the definition a LiDAR cover fraction approximates.

Recording both costs the crew almost nothing beyond one extra judgment per point, and it converts the largest known source of field-to-LiDAR disagreement from an unknown into a measured quantity. The difference between the two totals, computed per plot and summarized by forest type, is a deliverable of this program in its own right.

**At each hit, also record the height stratum** of the intercepting material, using a 2.0 meter break to match the height threshold of the LiDAR cover product, and the strata above it defined in Section 6. Hits below 2.0 meters are recorded but excluded from the cover value compared to LiDAR.

**Projection convention.** Cover is projected to the horizontal plane, not to the ground surface. On the slopes typical of this Basin the two differ materially, and the LiDAR product is computed on the horizontal. Plot slope is recorded so that the alternative can be computed if needed.

**Crown-ellipse cross-check.** Because crown width is collected on every tree under Section 4.1, a modeled crown cover can be computed from the stem map and compared to the point intercept result on the co-registration subset. Where the two disagree by more than ten percentage points, the plot is flagged for review.

---

## 6. Tier 2, surface and ground fuels

Collected on every plot in the base rate.

**Transects.** Four transects originate at plot center at azimuths 0, 90, 180, and 270 degrees, each running 58.9 feet horizontal to the primary plot edge. Installation tolerance on azimuth is plus or minus 2 degrees. Total coarse woody transect length is 235.6 feet per plot, which exceeds the 192 feet an FIA plot cluster carries. The transects double as the canopy point intercept lines under Section 5.

**Coarse woody debris.** Tallied where the central axis of the piece is intersected by the transect plane, the piece is 3.0 inches or larger in diameter at the point of intersection, and it is 0.5 feet or longer. Recorded per piece: transect azimuth, slope distance along the transect, species where determinable, diameter at the point of intersection, diameter of any hollow, decay class 1 to 5, total piece length, inclination, and percent of the piece charred by fire.

Percent charred is Core Optional in FIA and is required here. It is the single most direct field record of past fire and treatment effects available on the plot and costs one ocular estimate per piece.

Piece length is recorded on every piece regardless of length. The current FIA rule admits pieces 0.5 feet and longer while the legacy protocol required 3 feet, and recording length allows either rule to be applied later.

Where a piece is intersected by two transects it is tallied on the transect with the lower azimuth.

**Fine woody debris,** counted not measured, on all four transects:

| Class | Diameter | Time lag equivalent | Segment along transect |
|---|---|---|---|
| Small | 0 to 0.24 in | 1 hour | 14.0 to 20.0 ft |
| Medium | 0.25 to 0.9 in | 10 hour | 14.0 to 20.0 ft |
| Large | 1.0 to 2.9 in | 100 hour | 14.0 to 24.0 ft |

Material higher than 6 feet above the ground is not counted. The time lag equivalents are a crosswalk stated here for fuels modeling convenience; FIA does not print them in its own manual.

**Duff and litter depth** at two points on each transect, at 20.0 feet and 50.0 feet from center, for eight points per plot. Both to the nearest 0.1 inch, tolerance plus or minus 0.5 inch. Where a log, rock, or pile occupies the point, record litter above and below it and estimate duff from the surrounding area.

**Slope correction** uses the FIA form, c = 1 + (percent slope / 100)². Brown's original 1/cos(θ) is not used. The two converge at low slope and diverge sharply on steep ground, by roughly seventeen percent at 60 percent slope, and mixing them across a dataset is a silent error. The choice is stated here so it is applied consistently.

---

## 7. Tier 3, understory composition

Collected on a subset of plots at a separate unit price. Tier 3 fields are defined in the schema for every plot so that the tier can be extended later without a schema change.

Remote sensing cannot deliver composition or surface fuel loading, which is the reason this tier exists rather than being inferred.

**Vegetation profile,** on the 24.0 foot subplot footprint, following the FIA Phase 2 vegetation profile rather than the Phase 3 quadrat indicator. Cover is estimated ocularly to the nearest one percent under the Daubenmire convention, which takes the vertical projection of the polygon around the outer edge of foliage without subtracting normal interleaf spaces, and does not double count overlapping crowns.

Five growth habits are recorded: tally tree species, non-tally tree species, shrub and subshrub and woody vine, forb, and graminoid. Each receives four height layer values plus an aerial total, for 25 cover values per condition per subplot.

Height layers are 0 to 2.0 feet, 2.1 to 6.0 feet, 6.1 to 16.0 feet, and above 16 feet. This notation is used throughout in preference to the Phase 3 notation, which differs cosmetically.

**Species composition.** Species with 3 percent or more total aerial canopy cover are recorded individually with NRCS PLANTS symbols. Cover below 3 percent is not rounded up to reach the threshold.

**Crew qualification.** A certified botanist is required for this tier and only for this tier. The evidence supports the requirement: FIA reports that its own certified crews identify roughly 75 percent of plants to species and 89 percent to genus. Woody species identification is substantially more reliable than herbaceous, so where a plot is scoped to woody composition only, a trained technician working from a regional key is acceptable and is recorded as such on the plot record.

**Phenology and timing.** Cover is estimated when species are fully leafed out. Vegetation is not sampled when snow covers the subplot. In this Basin that constrains the window to roughly late June through September depending on elevation and snowpack, and it is the binding constraint on field season length.

---

## 8. Monumentation, relocation, and photographs

Every plot is permanently monumented so that a crew with no involvement in installation can find and remeasure it.

**Monument.** Rebar driven at plot center with an aluminum cap stamped with the plot identifier, set flush or slightly proud, with a ferrous element detectable by a metal locator.

**Witness trees.** Three trees tagged and recorded with species, DBH, azimuth to plot center, and horizontal distance. Selected for durability rather than proximity, and not selected from trees scheduled for treatment where that is known.

**Photographs.** Four photographs from plot center at 0, 90, 180, and 270 degrees, one vertical photograph of the canopy from center, one photograph of the monument in place, and one approach photograph from the direction of access with a landmark visible. All geotagged.

**Relocation record.** Access route narrative, parking or approach point coordinates, gate and road status, landowner and permission reference, hazards, and estimated travel time from the nearest maintained road. These fields exist so that the relocation packet is a data product rather than institutional memory.

---

## 9. Deviations from FIA core, stated explicitly

A reader familiar with FIA should be able to find every departure in one place.

1. **Plot geometry is a single concentric set rather than a four-subplot cluster.** The FIA cluster spreads four small plots across a 277 foot envelope, each of which independently suffers the small-plot penalty described in Section 1. One larger concentric plot at a single center is the better instrument for LiDAR validation and for permanent remeasurement.
2. **Full tree measurement extends to the entire 58.9 foot radius down to 4.0 inches DBH.** In California FIA, the 58.9 foot macroplot tallies only trees 24 inches and larger. Extending the full tally to the whole circle is the single most consequential deviation and is what makes the plot usable as LiDAR reference data.
3. **DBH floor is 4.0 inches rather than 5.0 inches**, per the TRPA decision of September 6, 2026. DBH is recorded to 0.1 inch so any floor can be recomputed.
4. **Height to live crown base is added.** FIA Phase 2 does not carry it.
5. **Crown width is added.** Required for the crown cover reconciliation.
6. **Height tolerance is tightened** to plus or minus 5 percent below 60 feet.
7. **Azimuth tolerance is tightened** from plus or minus 10 degrees to plus or minus 2 degrees where per-tree position is collected.
8. **Canopy cover is measured by 100-point vertical intercept with dual definitions** rather than taken from the FIA condition-level ocular value.
9. **Dwarf mistletoe rating and percent charred are required** rather than Core Optional.
10. **Plot center position follows the FIA High Performance GNSS standard** and additionally requires raw observation logging and post-processing, with real-time solutions recorded but not relied upon.
11. **Fuels transects run 58.9 feet from a single center** rather than 24 feet from each of four subplot centers. Total transect length per plot rises from 192 to 235.6 feet. Data collected under this protocol cannot be pooled with legacy FIA down woody data without adjusting for the design change.

---

## 10. Quality assurance

**Blind remeasurement** on 5 to 10 percent of plots by an independent crew with no access to the original data, within the same season. Measurement quality objectives are the tolerances in Section 4, met at least 90 percent of the time for continuous variables and 99 percent for species identification.

**Calibration exercise** before production measurement begins. The crew measures a set of training plots alongside TRPA staff, results are compared against tolerance, and production does not start until agreement is demonstrated.

**Digital capture with validation at entry.** All data are collected in the TRPA Survey123 form. Range checks, required-field enforcement, and cross-field logic are built into the form rather than applied after the fact. Paper is a backup only, and a paper plot is entered within 48 hours.

**Position audit.** Every plot center position is post-processed and reviewed against its accuracy metadata before the plot is accepted. Positions failing the accuracy target are reoccupied.

---

## 11. Sources

FIA and Common Stand Exam specifications in this document are drawn from the following primary sources.

- Pacific Northwest FIA Field Manual version 9.5 (2026), the operative manual for California: https://research.fs.usda.gov/sites/default/files/2026-03/pnw-2026_v9-5_or_wa_ca_fia_field_manual.pdf
- FIA National Core Field Guide version 9.3 (September 2023): https://research.fs.usda.gov/sites/default/files/2024-02/wo-v9-3_sep2023_fg_nfi_natl.pdf
- FIA Database Description version 9.2 (April 2024): https://research.fs.usda.gov/sites/default/files/2024-05/wo-v9-2_apr2024_ug_fiadb_database_description_nfi.pdf
- Region 5 Common Stand Exam Field Guide: https://www.fs.usda.gov/nrm/documents/fsveg/cse_user_guides/R5FG.pdf
- Common Stand Exam User Guide Chapter 2, Preparation and Design: https://www.fs.usda.gov/nrm/documents/fsveg/cse_user_guides/userguide_fsveg_ch2_prep-design.docx
- Schulz, Bechtold and Zarnoch, Sampling and Estimation Procedures for the Vegetation Diversity and Structure Indicator, PNW-GTR-781: https://www.fs.usda.gov/pnw/pubs/pnw_gtr781.pdf
- Brown, Handbook for Inventorying Downed Woody Material, GTR INT-16 (1974): https://research.fs.usda.gov/treesearch/download/28647.pdf

Supporting literature on plot size, co-registration, and canopy cover.

- Chirici et al. (2024), The Influence of the Spatial Co-Registration Error on the Estimation of Growing Stock Volume Based on Airborne Laser Scanning Metrics, Remote Sensing 16(24):4709: https://doi.org/10.3390/rs16244709
- Hernández-Stefanoni et al. (2018), Effects of Sample Plot Size and GPS Location Errors on Aboveground Biomass Estimates from LiDAR in Tropical Dry Forests, Remote Sensing 10(10):1586: https://doi.org/10.3390/rs10101586
- Yang et al. (2023), Small Field Plots Can Cause Substantial Uncertainty in Gridded Aboveground Biomass Products from Airborne Lidar Data, Remote Sensing 15(14):3509: https://doi.org/10.3390/rs15143509
- Wulder et al. (2012), Lidar sampling for large-area forest characterization: A review, Remote Sensing of Environment 121:196-209: https://doi.org/10.1016/j.rse.2012.02.001
- Ma et al. (2019), Definition and measurement of tree cover: A comparative analysis of field-, lidar- and Landsat-based tree cover estimations in the Sierra national forests, USA, Agricultural and Forest Meteorology 256-257: https://doi.org/10.1016/j.agrformet.2019.01.001
- Korhonen, Korhonen, Rautiainen and Stenberg (2006), Estimation of forest canopy cover: a comparison of field measurement techniques, Silva Fennica 40(4):577-588
- Jennings, Brown and Sheil (1999), Assessing forest canopies and understorey illumination: canopy closure, canopy cover and other measures, Forestry 72(1):59-73
- Performance Evaluation of Real-Time Kinematic GNSS with Survey-Grade Receivers and Short Observation Times in Forested Areas, Sensors (2024) 24(19):6404: https://doi.org/10.3390/s24196404

---

## Open items before the October 16 freeze

- Confirm the breakpoint diameter choice of 24.0 inches with Becky Estes and Shengli Huang, and confirm that the Nevada side will use the same value rather than the Interior West 21 inch convention.
- Verify the origin of the 1/7 acre figure with its source and retire it if it cannot be substantiated.
- Confirm with Shengli whether the adopted 2023 baseline computed trees per acre, basal area, and quadratic mean diameter at a 4.0 inch or 5.0 inch floor. If the floors differ, the baseline bridge is reported at both.
- Confirm the height stratum break used by the canopy cover product under validation, currently assumed to be 2.0 meters.
- Decide whether per-tree position is collected on all plots or on the co-registration subset only, which sets the cost form.
- Settle the treatment of plots in aspen, which require sub-meter positioning and are a targeted stratum.
