---
indicator_number: 190
indicator_name: Seral Stage & Canopy Cover
url: https://thresholds.laketahoeinfo.org/threshold/indicators/190
category: Vegetation Preservation
reporting_category: Forest Structure
status: Somewhat Worse Than Target   # DRAFT — see Status Rationale
trend: Insufficient Data to Determine Trend
confidence: Moderate
evaluation_year: 2023
draft_status: Draft
---

## Indicator Overview

Seral stage describes where a forest stand sits in its developmental cycle, from early
seral stands regenerating after disturbance through mid seral stands filling in to late
seral stands holding the large, old trees that define old growth. Canopy cover describes
how much of the ground that stand shades. Combined, the two measures sort the forest
into five classes — early, mid open, mid closed, late open, and late closed — that
capture both age and structure. A resilient landscape holds a mix of all five in
proportions the forest type evolved under. When one class dominates, the landscape loses
the habitat diversity that different species depend on and becomes vulnerable to a single
disturbance moving through uniform fuel. This indicator compares the current distribution
of the five classes within each major forest type against a desired range, using
vegetation, seral stage, and canopy cover layers from the Sierra Nevada Regional
Resource Kit.

## Chart Caption

Current percent of each forest type in each of the five seral stage and canopy cover
classes, compared against the desired range for that class. Classes falling below their
range are underrepresented; classes above it are overrepresented.

## Evaluation

| Field | Value |
|---|---|
| Status | Somewhat Worse Than Target |
| Trend | Insufficient Data to Determine Trend |
| Confidence | Moderate |

> **TODO:** Status drafted from the analysis in this repo. Needs Forest Health Working
> Group confirmation before publication.

## Applicable Standard

> **TODO:** Standard code has not been assigned. Proposed language for review:

**VEG-? Seral Stage and Canopy Cover.** Maintain the distribution of seral stage and
canopy cover classes within each forest type within the desired ranges shown below.

| Forest type | Early | Mid (closed) | Mid (open) | Late (open) | Late (closed) |
|---|---|---|---|---|---|
| Jeffrey Pine | 5–15% | 5–10% | 25–30% | 40–50% | 5–10% |
| White Fir / Mixed Conifer | 10–20% | 5–15% | 15–20% | 25–35% | 15–25% |
| Red Fir | 10–20% | 15–25% | 15–25% | 30–40% | 20–30% |

Closed canopy is defined as canopy cover of 50 percent or greater, except in Jeffrey
pine, where the threshold is 40 percent to reflect the more open structure that type
carries naturally.

## Key Points

- Roughly 127,000 acres across three forest types were evaluated: Jeffrey pine
  (40,800 acres), white fir and mixed conifer (64,200 acres), and red fir (22,400 acres).
- Early seral forest is severely underrepresented in every forest type. Jeffrey pine
  holds two percent against a five to 15 percent target, white fir holds three percent
  against 10 to 20 percent, and red fir holds two percent against 10 to 20 percent.
- Mid closed canopy is overrepresented in every forest type, most sharply in white fir
  and mixed conifer at 37 percent against a five to 15 percent target. This is the
  signature of fire exclusion, and it accounts for the largest single block of acreage
  out of alignment.
- Late open canopy — the large-tree, open-understory structure most associated with
  resilience and with historical conditions — is underrepresented in all three forest
  types.
- Roughly 46,800 acres, or 37 percent of evaluated forest, sit outside their desired
  range. Red fir is closest to its reference distribution; Jeffrey pine and white fir
  are furthest from it.

## Evaluation Map

Distribution of the five seral stage and canopy cover classes across non-urban forested
land in the Tahoe Basin. Classes are built by crossing the Regional Resource Kit seral
stage layer with a canopy cover layer thresholded at 50 percent, or 40 percent in
Jeffrey pine.

## About the Threshold

### Relevance

Forest age and structure determine what lives in a forest and how it responds to
disturbance. Early seral stands support shrub-nesting birds, deer forage, and the
pollinator habitat that closed forest cannot. Late open stands provide the large trees,
snags, and open understory that goshawk, spotted owl, and fisher depend on. A landscape
weighted toward mid closed canopy — which is where the Tahoe Basin sits today — offers
neither, and carries fuel arranged to move fire from the ground into the crowns across
large, continuous areas. Restoring a mix of classes is what makes a forest able to absorb
disturbance without converting to another vegetation type altogether.

### Human and Environmental Drivers

The dominant human driver is fire exclusion. Removing frequent, low-intensity fire
removed the process that created and maintained early seral openings and kept late seral
stands open beneath their canopies. Comstock-era logging in the late 1800s compounded
this by resetting large portions of the Basin to even-aged regeneration, and much of that
cohort is now aging into the mid closed class simultaneously. Prescribed fire, managed
wildfire, and mechanical treatment that creates openings move the distribution back
toward target. Natural drivers include wildfire, drought, and insect mortality, which
create early seral openings but at a severity and patch size that may not produce the
structure the standard describes.

## Delivering and Measuring Success

### EIP Action Priorities

- **Reduce Hazardous Fuels** — Reduce hazardous fuels and proactively manage forests to
  improve ecosystem resilience.

> **TODO:** Confirm additional EIP Action Priorities and pull canonical descriptions
> from the EIP Project Tracker.

### EIP Indicators

> **TODO:** Link the acres-treated performance measure from the EIP Project Tracker.

### Local and Regional Plans

- **Lake Tahoe Basin Multi-Jurisdictional Fuel Reduction and Wildfire Prevention
  Strategy** — Directs the treatment program that shifts stands out of the
  overrepresented mid closed class.
- **Tahoe Climate Resilience Action Strategy 2022** — Identifies structural diversity
  as a core element of forest resilience.

> **TODO:** Verify current plan titles and adoption years.

### Example EIP Projects

> **TODO:** Select two or three projects that created early seral openings or restored
> late open structure, with completion years.

### Monitoring Programs

> **TODO:** Name the monitoring program of record. Current assessment is remote sensing
> based rather than a standing field program.

## Rationale Details

### Status Rationale

**Somewhat Worse Than Target.** Analysis of the five seral stage and canopy cover classes
across three forest types shows consistent underrepresentation of early seral and late
open canopy stands and consistent overrepresentation of mid closed canopy. Of roughly
127,000 evaluated acres, about 46,800 acres sit outside their desired range, leaving
approximately 63 percent of the landscape in alignment with reference conditions. The
pattern is consistent in direction across all three forest types, and the largest single
departure — white fir and mixed conifer mid closed canopy at 37 percent against a five to
15 percent target — is also the most treatable. The shortfall is systematic but not
extreme, which supports a "Somewhat Worse Than Target" call.

> **TODO — reconcile with the figure published in `index.md`.** The results page states
> that "only ~55% of area is within desired conditions," but
> `output/composition_results_updated.csv` yields 63 percent when computed as total
> acreage less the absolute acreage off target. The two figures appear to use different
> weighting. Confirm which definition is intended, state it explicitly here, and correct
> whichever artifact is wrong.

### Trend Rationale

**Insufficient Data to Determine Trend.** This is the first evaluation of seral stage and
canopy cover as a threshold indicator. A trend requires a second assessment period built
from a comparable product and an identical classification method. Note that seral stage
classification is sensitive to the vintage of the input imagery, so the reference dataset
version should be fixed before the next evaluation.

## Confidence Details

### Confidence of Status

**Moderate.** The assessment is wall-to-wall across the non-urban forested Basin rather
than sampled, and the direction of departure is consistent across all three forest types,
which is a strong signal. Confidence is held at moderate because the desired ranges are
drawn from literature and expert judgment rather than from Basin-specific reference
conditions, because seral stage is modeled from remote sensing rather than measured, and
because the basin-wide summary figure is stated two different ways across repo artifacts.

### Confidence of Trend

**Low.** No second assessment period exists, so no trend statistic could be computed.

### Overall Confidence

**Low.** Where one confidence rating is moderate and the other is low, the overall
rating is low.

## Additional Figures and Resources

- **Seral Stage Composition Table** — Current versus desired distribution by forest type.
  `DataVisualizations/CompositionAge_Table_Updated.html`
- **Actions Needed Table** — Acres from target by class.
  `DataVisualizations/Composition_Action_Table.html`
- **Composition Chart** — Current versus reference distribution.
  `DataVisualizations/CompositionAge_Chart.html`
- **Composition Map** — Basin-wide class distribution.
  `DataVisualizations/CompositionAge_Map.html`
- **Analysis Notebook** — Classification logic and desired conditions.
  [ForestHealth_ThreholdUpdate_Analysis.ipynb](https://github.com/trpa-agency/ForestHealth/blob/main/ForestHealth_ThreholdUpdate_Analysis.ipynb)
- **Regional Resource Kits** — Source data.
  [wildfiretaskforce.org/regional-resource-kits-page](https://wildfiretaskforce.org/regional-resource-kits-page/)

---

## Open Question Carried Forward

`index.md` flags an unresolved question that belongs on this page or in the methods
documentation: why the Angora Fire footprint is not classified as early seral. Because
early seral underrepresentation is the headline finding, a reader will reasonably ask
whether the classification is missing recent disturbance. Answer it before publication.

---

## Source Notes

*Internal only — not published to the indicator page.*

| Element | Source in this repo |
|---|---|
| Desired percent ranges by class | `output/composition_results_updated.csv`, `Desired % Range` column |
| Current percent and acres by class | `output/composition_results_updated.csv` |
| Canopy cover thresholds (50%, 40% for Jeffrey pine) | `classify_seral_stage()`, `ForestHealth_ThreholdUpdate_Analysis.ipynb` |
| Five-class construction logic | Markdown cell 13, `ForestHealth_ThreholdUpdate_Analysis.ipynb` |
| Charts, tables, and map | `DataVisualizations/CompositionAge_*.html`, `Composition_Action_Table.html` |
| 2023 attainment call framing | `index.md`, Composition section |
