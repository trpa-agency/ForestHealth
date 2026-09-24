# Plot Data Schema and Derived Metric Calculations

**Companion to Forest Health Plot Protocol v1.0 and TRPA_ForestHealth_Plot_Survey123_v1.0.xlsx**
Tahoe Regional Planning Agency, September 19, 2026

---

## 1. Feature service structure

The Survey123 form publishes to one hosted feature service in the TRPA ArcGIS Online organization. Item ownership stays with TRPA from the day the form is created, so there is no transfer step and no dependency on a consultant account or license after any contract ends.

| Layer or table | Type | Relationship | Rows per plot visit |
|---|---|---|---|
| `FH_Plot` | point | parent | 1 |
| `FH_Tree` | table | 1 to many from `FH_Plot` | 0 to roughly 120 |
| `FH_Sapling` | table | 1 to many | 0 to 40 |
| `FH_Seedling` | table | 1 to many | 0 to 10 |
| `FH_CoverPoint` | table | 1 to many | exactly 100 |
| `FH_Transect` | table | 1 to many | exactly 4 |
| `FH_CWD` | table | 1 to many from `FH_Transect` | 0 to 30 per transect |
| `FH_VegCover` | table | 1 to many | 0 or 25 |
| `FH_VegSpecies` | table | 1 to many | 0 to 30 |
| `FH_Witness` | table | 1 to many | 3 |
| `FH_Photo` | attachment table | 1 to many | 7 |

Survey123 generates the relationship keys automatically from the repeat structure. The nested `FH_CWD` under `FH_Transect` is a two-level repeat, which Survey123 supports and which keeps each piece bound to the transect it was intercepted on.

The tree count estimate above assumes a dense Sierran mixed conifer stand at roughly 300 trees per acre above the four inch floor on a quarter acre plot, plus large trees picked up on the macroplot. Crews should expect 60 to 100 tree records on a typical plot and up to 120 on the densest.

---

## 2. Expansion factors

Every per-acre estimate comes from multiplying a tree count by the expansion factor of the unit it was tallied on. These values are exact for the specified radii and should be stored as constants rather than recomputed in each analysis.

| Sampling unit | Radius | Area (acres) | Trees per acre per tree |
|---|---|---|---|
| Microplot | 6.8 ft | 0.00333488 | 299.860 |
| Primary plot | 58.9 ft | 0.25020305 | 3.996753 |
| Large-tree macroplot | 56.4 m (185.04 ft) | 2.4693236 | 0.404970 |

A tree at or above the breakpoint diameter carries the macroplot factor regardless of where inside the 56.4 meter circle it sits, including inside the primary plot. It is never also counted at the primary plot factor. This follows the FIA database convention rather than the field manual's annular wording, and it is what prevents double counting at the breakpoint.

---

## 3. Derived metrics for VP10 and VP9

### 3.1 Trees per acre

TPA is the sum of expansion factors over the trees that qualify.

```
TPA = SUM(expansion_factor) for all live trees where dbh_in >= floor
```

The reporting floor is 4.0 inches. Because DBH is recorded to 0.1 inch on every stem, TPA can be recomputed at any other floor. Report at both 4.0 and 5.0 inches wherever the result is compared to a product built on the FIA five inch convention, and at 12.5 centimeters wherever it is compared to MSIM.

### 3.2 Basal area

```
BA_tree_sqft = 0.005454154 * dbh_in^2
BA_per_acre  = SUM(BA_tree_sqft * expansion_factor)
```

The constant is pi divided by four divided by 144, which converts square inches to square feet.

### 3.3 Quadratic mean diameter

QMD must be computed as the expansion-weighted quadratic mean, not the arithmetic mean of diameters. Using the arithmetic mean understates QMD in stands with a skewed diameter distribution, which describes most of this Basin.

```
QMD_in = SQRT( SUM(expansion_factor * dbh_in^2) / SUM(expansion_factor) )
```

Equivalently, `QMD = SQRT( BA_per_acre / (0.005454154 * TPA) )`.

### 3.4 Canopy cover

Two values are produced per plot from the 100 point intercepts, and both are reported.

```
crown_cover_pct     = 100 * COUNT(crown_cover_hit = 'hit'     AND stratum != 'below2m') / 100
effective_cover_pct = 100 * COUNT(effective_cover_hit = 'hit' AND stratum != 'below2m') / 100
definitional_gap    = crown_cover_pct - effective_cover_pct
```

Points below the two meter stratum are excluded from both values so that the field measurement matches the height threshold of the canopy cover product under validation. Hits below two meters remain in the table and are summarized separately as a shrub and regeneration layer.

`crown_cover_pct` is the value compared to the VP9 standard, because the standard and the FIA convention it inherits both count within-crown gaps as cover. `effective_cover_pct` is the value compared to a LiDAR or satellite cover fraction, because those products see through within-crown gaps. Reporting the gap by forest type is the deliverable that tells TRPA how much of any apparent model error is definitional rather than real. Expect the gap to be widest in Jeffrey pine and red fir, which are the open-crowned types and also the types furthest from the VP9 target.

Binomial standard error on either value at 100 points is `SQRT(p * (1 - p) / 100)`, which is at most 5 percentage points at p equal to 0.5. That is the per-plot precision, and it is the reason the point count is 100 rather than the 20 some field guides allow.

### 3.5 Seral stage assignment

Seral stage is assigned from QMD using the breaks in the threshold standard, then crossed with canopy cover to produce the five VP9 classes.

```
early : QMD <  5 in
mid   : QMD >= 5 in and < 25 in
late  : QMD >= 25 in

closed : crown_cover_pct >= 50, except Jeffrey pine where the break is 40
open   : below that break
```

The five reported classes are early, mid open, mid closed, late open, and late closed. Early seral is not split by cover.

Confirm the QMD breaks against the threshold report before the October 16 freeze. They are carried here as the working values.

### 3.6 Fuel loading

Coarse woody loading follows the planar intercept estimator with the FIA slope correction.

```
c = 1 + (slope_pct / 100)^2
```

Total CWD transect length per plot is 4 transects times 58.9 feet, or 235.6 feet before slope correction. Fine woody transect lengths are 4 times 6 feet for the one hour and ten hour classes and 4 times 10 feet for the hundred hour class.

Brown's original slope correction, 1 divided by the cosine of the slope angle, is not used. The two forms diverge by roughly seventeen percent at sixty percent slope, which is common ground in this Basin, so mixing them across a dataset introduces a silent error. Record the correction form used as dataset metadata.

---

## 4. Quality assurance rules enforced in the form

These are built into the Survey123 constraints rather than applied after the fact.

| Rule | Where | Behavior |
|---|---|---|
| Occupation at least 15 minutes | `occ_minutes` | Blocks submission, prompts reoccupation |
| Raw observations logged | `raw_logged` | Must be yes, cannot be bypassed |
| Raw file name recorded | `raw_file` | Required |
| DBH at or above 4.0 in on the tree repeat | `dbh_in` | Blocks, directs stem to the sapling repeat |
| Sapling DBH between 1.0 and 3.9 in | `sap_dbh_in` | Blocks, directs stem to the tree repeat |
| Crown base below total height | `crown_base_ht_ft` | Blocks |
| Distance within the macroplot radius | `distance_ft` | Blocks above 185.1 ft |
| CWD at least 3.0 in at intersection | `cwd_dia_in` | Blocks |
| Understory species at 3 percent or more | `vs_cover_pct` | Blocks, states that values are not rounded up to reach 3 |
| Decay class required on standing dead | `decay_class` | Required when status is standing dead |
| Offset fields required when offset used | offset group | Conditional required |
| Crew minutes on plot | `crew_minutes_on_plot` | Required. This is how the next solicitation gets a real unit cost |

Two rules cannot be enforced in the form and must be caught in office review. The first is the plot center accuracy target, because the final accuracy is only known after post-processing; the office fields are completed then and any plot over one meter, or over 0.3 meters in aspen, is scheduled for reoccupation. The second is the crown ellipse cross-check described in the protocol, which compares modeled crown cover from the stem map against the point intercept result and flags disagreement beyond ten percentage points.

---

## 5. Build and deployment notes

The workbook is a standard XLSForm and opens directly in Survey123 Connect. It validates clean under pyxform with no errors and no warnings.

Two calculation patterns in the form are worth understanding before anyone edits it.

The canopy point repeat has a fixed count of 100 and derives its own geometry rather than asking the crew to enter it. `pt_index` is `position(..)`, which returns the row number inside the repeat. From that, `pt_transect` is `int((pt_index - 1) div 25) + 1`, `pt_azimuth` is `(pt_transect - 1) * 90`, and `pt_distance_ft` is `3.0 + (((pt_index - 1) mod 25) * 2.0)`. The crew sees a label reading the transect azimuth and distance and records two hit or miss determinations. This removes 200 typed values per plot and removes the error mode where a crew loses its place along a transect.

The fuels transect repeat uses the same pattern with a fixed count of 4 and an azimuth of `(tr_index - 1) * 90`.

Deployment sequence: publish from Survey123 Connect into the TRPA organization, enable offline map areas covering the Basin at a scale that supports navigation without cell service, add the plot location layer and the navigation packet layer as reference layers, and set the submission to queue when offline. Test the full form offline on a real plot before any crew training session.
