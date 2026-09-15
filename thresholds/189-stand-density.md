---
indicator_number: 189
indicator_name: Stand Density
url: https://thresholds.laketahoeinfo.org/threshold/indicators/189
category: Vegetation Preservation
reporting_category: Forest Structure
status: Considerably Worse Than Target   # DRAFT — see Status Rationale
trend: Insufficient Data to Determine Trend
confidence: Moderate
evaluation_year: 2023
draft_status: Draft
---

## Indicator Overview

Stand density measures how crowded a forest stand is, reported as trees per acre (TPA)
and basal area (square feet per acre). Together these two measures describe how much
growing space the trees on an acre are using and how much competition they face for
water, light, and nutrients. Overstocked stands grow more slowly, are more vulnerable
to drought stress and bark beetle mortality, and carry the continuous fuel loads that
drive uncharacteristically severe wildfire. Because the density a stand can carry
depends on what grows there and how old it is, this indicator evaluates each acre
against a target set for its forest type and seral stage rather than against a single
basin-wide number. Stand density is derived from remote sensing products produced for
the Sierra Nevada Regional Resource Kit and assessed at 30-meter resolution across all
non-urban forested land in the Tahoe Basin.

## Chart Caption

Percent of each forest type meeting its stand density and basal area target, by seral
stage, for the 2023 evaluation. Targets differ by forest type and seral stage, so the
bars compare each stratum against its own reference condition rather than against a
common value.

## Evaluation

| Field | Value |
|---|---|
| Status | Considerably Worse Than Target |
| Trend | Insufficient Data to Determine Trend |
| Confidence | Moderate |

> **TODO:** Status and confidence are drafted from the analysis in this repo. Both need
> Forest Health Working Group confirmation before publication. Trend cannot be
> evaluated until a second assessment period exists.

## Applicable Standard

> **TODO:** Standard code has not been assigned. Proposed language for review:

**VEG-? Stand Density.** Maintain stand density and basal area within the range
identified for each forest type and seral stage, as shown in the table below.

| Forest type | Seral stage | Trees per acre | Basal area (ft²/acre) |
|---|---|---|---|
| Jeffrey Pine | Early | 200 | 30 |
| Jeffrey Pine | Mid | 70 | 80 |
| Jeffrey Pine | Late | 55 | 100 |
| White Fir / Mixed Conifer | Early | 300 | 40 |
| White Fir / Mixed Conifer | Mid | 90 | 130 |
| White Fir / Mixed Conifer | Late | 75 | 180 |
| Red Fir | Early | 300 | 50 |
| Red Fir | Mid | 100 | 175 |
| Red Fir | Late | 80 | 250 |

> **Resolved — these values are maximums.** A stand is in attainment at or below the
> target and is overstocked above it. The code tests `>= min_stems` and `>= min_ba` to
> flag the pixels that *exceed* the target, writing 1 for overstocked and 0 for in
> attainment; the summarization cell then counts `Value == 0` as the attaining area. The
> pipeline was always internally consistent — only the narrative in markdown cell 9 was
> misleading, and it has been rewritten to state the convention explicitly.

## Key Points

- 115,396 acres of non-urban conifer forest were evaluated across three forest types:
  Jeffrey pine, Sierran mixed conifer, and red fir.
- 72 percent of the assessed forest (83,085 acres) exceeds the density targets and is
  considered overstocked. Only 32,311 acres meet them.
- Attainment varies sharply by forest type. Red fir is closest to its targets at 56
  percent of evaluated acres, Sierran mixed conifer follows at 28 percent, and Jeffrey
  pine is furthest off at seven percent.
- Early seral stands are the strongest stratum in every forest type, at roughly 99
  percent attainment, but early seral forest is scarce basin-wide so it contributes
  little acreage. Mid and late seral stands carry nearly all of the shortfall.
- Jeffrey pine mid and late seral stands are the weakest stratum of all, at four and
  five percent attainment, and represent the clearest opportunity for treatment.
- This is the first evaluation of stand density as a threshold indicator, so no trend
  can be reported. A second assessment period is needed before direction of change can
  be determined.

## Evaluation Map

Stand density threshold attainment across non-urban forested land in the Tahoe Basin.
Each 30-meter cell is classified as meeting or not meeting both the trees per acre and
basal area target for its forest type and seral stage. Derived from Sierra Nevada
Regional Resource Kit stand density, basal area, seral stage, and vegetation type layers.

## About the Threshold

### Relevance

Forest density is the single most manageable driver of wildfire behavior and forest
resilience in the Tahoe Basin. A century of fire exclusion allowed stands that
historically carried 50 to 100 large trees per acre to fill in with dense, small-diameter
understory, raising competition for soil moisture and creating ladder fuels that carry
fire into the canopy. Restoring density to within the range each forest type evolved
under reduces crown fire potential, lowers drought and beetle mortality, and protects
the water quality, habitat, and recreation values that depend on a living forest.

### Human and Environmental Drivers

The dominant human driver is more than a century of fire suppression, compounded by
Comstock-era clearcutting in the late 1800s that reset much of the Basin to even-aged
stands regenerating at once. Fuel reduction, mechanical thinning, and prescribed fire
move density back toward target; deferred treatment and access constraints on steep or
roadless ground hold it above target. Natural drivers include drought, bark beetle
outbreaks, and wildfire, all of which reduce density but often at a severity and pattern
that does not produce the structure the standard describes.

## Delivering and Measuring Success

### EIP Action Priorities

- **Reduce Hazardous Fuels** — Reduce hazardous fuels and proactively manage forests to
  improve ecosystem resilience.

> **TODO:** Confirm whether additional EIP Action Priorities should be linked. Pull the
> canonical names and descriptions from the EIP Project Tracker rather than retyping them.

### EIP Indicators

> **TODO:** Link the acres-treated performance measure from the EIP Project Tracker.
> The fuel treatment chart and map in `index.md` draw on this data, but the indicator
> name and description must match the tracker exactly.

### Local and Regional Plans

- **Lake Tahoe Basin Multi-Jurisdictional Fuel Reduction and Wildfire Prevention
  Strategy** — Sets the basin-wide priorities and pace for the fuel reduction work that
  moves stand density toward target.
- **Tahoe Climate Resilience Action Strategy 2022** — Identifies forest resilience and
  reduced stand density as core adaptation strategies.

> **TODO:** Verify current plan titles and adoption years before publication.

### Example EIP Projects

> **TODO:** Select two or three completed fuel reduction projects from the EIP Project
> Tracker with completion years.

### Monitoring Programs

> **TODO:** Name the monitoring program of record. The current assessment is a remote
> sensing analysis built on the Sierra Nevada Regional Resource Kit rather than a
> standing field monitoring program; confirm how this should be described.

## Rationale Details

### Status Rationale

**Considerably Worse Than Target.** Across 115,396 acres of evaluated non-urban conifer
forest, 32,311 acres, or 28 percent, met both the trees per acre and basal area target
for their forest type and seral stage. The standard calls for at least 50 percent, or
57,698 acres, so the Region has achieved 56 percent of the acreage required and needs an
additional 25,387 acres to reach attainment. The shortfall is concentrated in mid and
late seral stands, which carry nearly all of the overstocked acreage, and it is large
enough in both absolute and proportional terms to support a "Considerably Worse Than
Target" call. This matches the status published in the Forest Health Threshold Standards
report.

Attainment by forest type, from `output/stand_density_forest_type_attainment_new.csv`,
was 56 percent for red fir (12,591 of 22,365 acres), 28 percent for white fir and mixed
conifer (17,173 of 60,276 acres), and seven percent for Jeffrey pine (2,040 of 28,783
acres).

> **TODO:** The by-type figures above come from a run assessing 111,424 acres, which
> predates the addition of Lodgepole Pine to the forest type crosswalk. Re-derive them
> after the next run so they sum to the 115,396-acre extent used for the basin-wide call.

> **Resolved.** `stand_density_forest_type_attainment_new.csv` is the authoritative
> table. It is the only one written by current notebook code, and at 28.5 percent it
> agrees with the 28 percent published in the report. The `_hugh` and un-suffixed tables
> were produced by code no longer in the repository and have been moved to
> `archive/superseded_outputs/`. The earlier 74 percent figure came from reading the
> `_hugh` table's counts as attainment when they are in fact the overstocked population.

### Trend Rationale

**Insufficient Data to Determine Trend.** This is the first evaluation of stand density
as a threshold indicator. Determining a trend requires a second assessment period built
from a comparable remote sensing product and an identical classification method.
Establish the assessment interval and the reference dataset version before the next
evaluation so the two periods are directly comparable.

## Confidence Details

### Confidence of Status

**Moderate.** The assessment covers the full non-urban forested extent of the Basin at
30-meter resolution rather than sampling it, which is a strength. Confidence is held at
moderate rather than high because the underlying stand density and basal area layers are
modeled from remote sensing rather than measured in the field, and because the assessed
extent is being re-derived following the addition of Lodgepole Pine to the forest type
crosswalk. The two earlier concerns on this page, the direction of the density test and
the existence of three competing result sets, have both been resolved.

### Confidence of Trend

**Low.** No second assessment period exists, so no trend statistic could be computed.

### Overall Confidence

**Low.** Where one confidence rating is moderate and the other is low, the overall
rating is low. Expect this to rise to medium once a second evaluation period is
available and the result sets are reconciled.

## Additional Figures and Resources

- **Stand Density Threshold Table** — Interactive table of targets by forest type and
  seral stage. `DataVisualizations/StandDensity_Table.html`
- **Stand Density by Forest Type** — Percent of each forest type meeting target.
  `DataVisualizations/StandDensity_Chart_ForestType_PercentTarget.html`
- **Stand Density Attainment Map** — Basin-wide map of attainment.
  `DataVisualizations/StandDensity_Map.html`
- **Analysis Notebook** — Methods, thresholds, and processing steps.
  [ForestHealth_ThreholdUpdate_Analysis.ipynb](https://github.com/trpa-agency/ForestHealth/blob/main/ForestHealth_ThreholdUpdate_Analysis.ipynb)
- **Regional Resource Kits** — Source data.
  [wildfiretaskforce.org/regional-resource-kits-page](https://wildfiretaskforce.org/regional-resource-kits-page/)

---

## Source Notes

*Internal only — not published to the indicator page.*

| Element | Source in this repo |
|---|---|
| Threshold values by forest type and seral stage | `thresholds` dict in `assess_density_targets()`, `ForestHealth_ThreholdUpdate_Analysis.ipynb` |
| Attainment acreage and percentages | `output/stand_density_forest_type_attainment_new.csv` (basin-wide call from the Forest Health Threshold Standards report) |
| Method description | Markdown cell 9, `ForestHealth_ThreholdUpdate_Analysis.ipynb` |
| Charts, table, and map | `DataVisualizations/StandDensity_*.html` |
| Narrative framing | `index.md`, Stand Density section |
