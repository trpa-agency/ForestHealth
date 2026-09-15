---
indicator_number: 192
indicator_name: Landscape Fire Dynamics
url: https://thresholds.laketahoeinfo.org/threshold/indicators/192
category: Vegetation Preservation
reporting_category: Fire Dynamics
status:              # TODO — see Status Rationale
trend: Insufficient Data to Determine Trend
confidence: Low
evaluation_year: 2023
draft_status: Draft
---

## Indicator Overview

Fire is not something that happens to Tahoe Basin forests; it is part of how they work.
Before Euro-American settlement, low- and moderate-severity fire moved through most of
the Basin every five to 30 years, thinning small trees, recycling nutrients, and creating
the patchy structure that kept any single fire from consuming the whole landscape. This
indicator measures whether the fire the Basin experiences today still performs that
function. It does so by evaluating the severity at which the landscape is likely to burn
and the size of the patches that would burn at high severity. Functional fire maintains
ecosystem processes and structure. Uncharacteristically severe fire, particularly in
large contiguous patches, kills the seed source, exposes soil to erosion, and can convert
forest to shrubland for decades or permanently.

## Chart Caption

Modeled probability of low, moderate, and high severity fire across forested acres,
summarized by management zone. Zones allow the Region to see where severity risk
concentrates and to target treatment accordingly.

## Evaluation

| Field | Value |
|---|---|
| Status | **TODO** |
| Trend | Insufficient Data to Determine Trend |
| Confidence | Low |

> **TODO:** A status call cannot be made until the standard's numeric criterion is
> adopted. See Applicable Standard below.

## Applicable Standard

> **TODO — standard is not yet complete.** Two components are proposed; the second has
> no adopted threshold value.

**Component 1 — Severity distribution.** Maintain the proportion of the forested
landscape likely to burn at high severity at or below the reference range for each
forest type.

> **TODO:** No reference range has been set. Without one, the severity-by-zone results
> in this repository describe current condition but cannot produce an attainment call.
> Adopt a reference range, or restate this component as a performance measure rather
> than a threshold standard.

**Component 2 — High severity patch size.** Limit the extent of the landscape at risk of
burning at high severity in patches larger than **40 acres**.

The 40-acre patch size criterion is implemented in the analysis: high severity cells are
smoothed with a three-by-three focal statistic, converted to polygons, and the acreage in
polygons exceeding 40 acres is summed and expressed as a percentage of total forested
area.

> **TODO:** Confirm the acceptable percentage. The method computes "percent of large
> patches at risk," but no pass/fail value has been set. Also confirm the 40-acre
> figure itself and cite the source — large patch thresholds in the literature range
> widely, and the choice drives the result.

## Key Points

> **TODO:** Populate from the executed analysis. The notebook cells that compute these
> values (`Large High Severity Patch Size`, and the fire severity by management zone
> summary) have no saved outputs in the committed notebooks, so the actual numbers are
> not recoverable from this repository. Rerun and record them. Candidates:
>
> - Total forested acres evaluated for fire severity.
> - Acres and percent likely to burn at high, moderate, and low severity.
> - Acres at risk of high severity in patches larger than 40 acres, and what percent of
>   the landscape that represents.
> - Which management zones carry the highest concentration of high severity risk.
> - How wilderness areas compare to treated and treatable ground. Note that Desolation,
>   Granite Chief, and Mt. Rose wilderness areas are combined into a single "Wilderness"
>   zone in the current analysis.

## Evaluation Map

Dominant modeled fire severity class across forested land in the Tahoe Basin, overlaid
with management zone boundaries. Each cell is assigned the severity class with the
highest modeled probability.

## About the Threshold

### Relevance

The question this indicator answers is not whether the Basin will burn but how. A fire
that burns at low and moderate severity across most of its footprint leaves a living
forest behind, thins fuel for decades, and costs far less to recover from than it would
have cost to prevent. A fire that burns at high severity across thousands of contiguous
acres removes the seed source, strips the soil that holds Lake Tahoe's clarity in place,
and can shift the site to brush for a generation. The Angora Fire in 2007 and the Caldor
Fire in 2021 both made this concrete for the Region. Tracking modeled severity and patch
size tells the Basin where it stands before the next ignition rather than after.

### Human and Environmental Drivers

Fire severity is driven by fuel, weather, and topography, and only the first is
manageable. More than a century of fire exclusion built the continuous, dense fuel that
converts a surface fire into a crown fire, which is why this indicator moves in step with
stand density (indicator 189) and seral stage (indicator 190). Fuel reduction, prescribed
fire, and managed wildfire lower modeled severity; deferred treatment raises it. Climate
change raises it independently of fuel by lengthening the fire season, drying fuels
further, and increasing the frequency of the extreme weather days on which most acreage
burns. Ignition sources in the Basin are predominantly human, which means severity risk
and human use overlap geographically.

## Delivering and Measuring Success

### EIP Action Priorities

- **Reduce Hazardous Fuels** — Reduce hazardous fuels and proactively manage forests to
  improve ecosystem resilience.

> **TODO:** Confirm additional priorities and pull canonical descriptions from the EIP
> Project Tracker.

### EIP Indicators

> **TODO:** Link the acres-treated performance measure. The fuel treatment chart and map
> in `index.md` are the supporting visuals.

### Local and Regional Plans

- **Lake Tahoe Basin Multi-Jurisdictional Fuel Reduction and Wildfire Prevention
  Strategy** — Sets treatment priorities and pace.
- **Tahoe Climate Resilience Action Strategy 2022** — Addresses the climate drivers that
  raise severity independently of fuel.

> **TODO:** Add applicable Community Wildfire Protection Plans and the LTBMU land
> management plan. Verify titles and adoption years.

### Example EIP Projects

> **TODO:** Select two or three completed fuel reduction or prescribed fire projects with
> completion years.

### Monitoring Programs

> **TODO:** Name the monitoring program of record. Confirm how the modeled fire severity
> product should be attributed.

## Rationale Details

### Status Rationale

> **TODO:** Cannot be written until the standard has an adopted numeric criterion. Once
> it does, lead with the call, then state acres evaluated, the severity distribution, the
> large patch acreage and percentage, and the comparison to the criterion.

### Trend Rationale

**Insufficient Data to Determine Trend.** This is the first evaluation of landscape fire
dynamics as a threshold indicator, and the assessment reflects modeled conditions at a
single point in time rather than observed fire outcomes over a period of record. A trend
requires either a second modeling run using the same fuels and weather inputs or a shift
to measuring severity in fires that actually occurred. Decide which before the next
evaluation — the two answer different questions and are not interchangeable.

## Confidence Details

### Confidence of Status

**Low.** Three factors hold this down. The assessment models the severity at which the
landscape is *likely* to burn rather than measuring severity in fires that occurred,
which makes it a risk product rather than an outcome measurement. No reference range has
been adopted for the severity distribution component. And the executed results are not
preserved in the committed notebooks, so the numbers behind any call cannot currently be
audited. The first is inherent to the method; the second and third are fixable.

### Confidence of Trend

**Low.** No second assessment period and no period of record.

### Overall Confidence

**Low.** Both component ratings are low.

## Additional Figures and Resources

- **Fire Severity by Management Zone** — Stacked bar chart of severity by zone.
  `DataVisualizations/FireSeverityByManagementZone_Chart.html`
- **Fire Severity Map** — Dominant severity class with management zones.
  `DataVisualizations/FireSeverityByManagementZone_Map.html`
- **Fuel Treatment Chart** — Annual treatment activity over time.
  `DataVisualizations/FuelTreatment_Chart.html`
- **Fuel Treatment Map** — Spatial extent of past treatments.
  `DataVisualizations/FuelTreatment_Map.html`
- **Analysis Notebook** — Severity classification and patch size methods.
  [ForestHealth_ThreholdUpdate_Analysis.ipynb](https://github.com/trpa-agency/ForestHealth/blob/main/ForestHealth_ThreholdUpdate_Analysis.ipynb)

---

## Source Notes

*Internal only — not published to the indicator page.*

| Element | Source in this repo |
|---|---|
| Severity classification method | `dominant_fire_severity()` and `identify_fire_severity()`, `ForestHealth_ThreholdUpdate_Analysis.ipynb` |
| 40-acre patch criterion | `sum_area_by_criteria(..., area_threshold=40)` on `FocalStat_3x3_high_severity_polygon` |
| Severity by management zone | `ForestHealth_ThresholdUpdate_Results.ipynb`, cells 29–30 |
| Severity class lookup (1 = low, 2 = moderate, 3 = high) | Results notebook, cell 29 |
| Computed acreage values | **Not preserved.** Notebook outputs are empty and `fire_severity_results.csv` writes to a network path outside the repo |
| Narrative framing | `index.md`, Functional Fire section |
