---
indicator_number: 193
indicator_name: Wildland Urban Interface Defense Zone Fire Dynamics
url: https://thresholds.laketahoeinfo.org/threshold/indicators/193
category: Vegetation Preservation
reporting_category: Fire Dynamics
status:              # TODO — see Status Rationale
trend: Insufficient Data to Determine Trend
confidence: Low
evaluation_year: 2023
draft_status: Draft
---

## Indicator Overview

The Wildland Urban Interface, or WUI, is where homes and communities meet undeveloped
wildland. Nearly half of the Tahoe Region falls within it. The WUI is divided into two
parts: the Defense Zone, the immediate buffer around structures and evacuation routes
where firefighters must be able to work safely, and the surrounding Threat Zone, where
the objective is to keep fires from starting and from building intensity before they
reach the Defense Zone. This indicator evaluates the Defense Zone specifically. It asks
whether fuels there have been reduced enough that a fire arriving under severe weather
would burn with flames short enough for crews to engage it directly and stop it before it
reaches structures. Four feet is the operational break point — above it, direct attack by
hand crews is no longer effective.

## Chart Caption

> **TODO:** Write once the summary figure exists. State the percent of Defense Zone
> acreage below the four-foot flame length criterion, the weather scenario modeled, and
> the vintage of the fuels data.

## Evaluation

| Field | Value |
|---|---|
| Status | **TODO** |
| Trend | Insufficient Data to Determine Trend |
| Confidence | Low |

## Applicable Standard

> **TODO:** Standard code has not been assigned. Proposed language, drawn from
> `index.md`, for review:

**VEG-? Wildland Urban Interface Defense Zone Fire Dynamics.** Predicted flame lengths
under 90th percentile fire weather conditions shall be less than four feet across
90 percent of the WUI Defense Zone.

Areas exceeding four-foot flame lengths shall additionally be:

- Well distributed across the Defense Zone rather than concentrated;
- Contained in patches smaller than one acre; and
- Located more than 100 feet from structures and critical infrastructure.

> **TODO:** The three distribution criteria are stated qualitatively for the first and
> quantitatively for the second and third. "Well distributed" needs either a measurable
> definition or removal — as written it cannot be evaluated consistently between
> evaluation cycles.

## Key Points

> **TODO:** Populate from the FSim modeling results. No WUI Defense Zone results are
> committed to this repository — `index.md` describes the method and the standard but
> reports no current condition, and the results notebook's WUI section contains the
> basin-wide severity analysis rather than a Defense Zone specific assessment.
> Candidates once the analysis exists:
>
> - Total Defense Zone acreage in the Region and how the zone was delineated.
> - Percent of Defense Zone acreage below four-foot modeled flame length, against the
>   90 percent standard.
> - Acres exceeding four feet, and how much of that is in patches larger than one acre.
> - Acres exceeding four feet within 100 feet of structures or critical infrastructure —
>   the highest priority subset for treatment.
> - How Defense Zone condition varies by jurisdiction or fire district.

## Evaluation Map

Modeled flame length in the WUI Defense Zone under 90th percentile fire weather
conditions, classified above and below the four-foot criterion.

> **TODO:** Confirm the map exists and describe its source layer and resolution.

## About the Threshold

### Relevance

This is the indicator most directly tied to whether people and homes survive a fire in
the Tahoe Basin. The Defense Zone is where suppression either works or does not.
Flame lengths under four feet can be attacked directly by hand crews with hand tools;
between four and eight feet, direct attack fails and equipment is required; above eight
feet, crown fire and spotting make control unlikely under any resource level. Reducing
Defense Zone fuels to keep flame lengths below four feet is what converts an
uncontrollable event into a defensible one, and it is the single highest-return fuel
investment the Region makes because it protects both structures and the evacuation
routes people depend on.

### Human and Environmental Drivers

Defense Zone condition is almost entirely human-controlled, which distinguishes this
indicator from the others in the Fire Dynamics category. Defensible space work, hazardous
fuel reduction, and pile burning lower modeled flame lengths directly. Parcel-level
compliance matters as much as agency treatment because the Defense Zone is largely
private land interspersed with public parcels, and untreated parcels create the gaps that
carry fire through an otherwise treated neighborhood. Regrowth means treatment is not
permanent — Defense Zone acreage must be re-entered on a cycle to hold condition.
Environmental drivers include the extreme weather days the standard models against, the
frequency of which climate change is increasing.

## Delivering and Measuring Success

### EIP Action Priorities

- **Reduce Hazardous Fuels** — Reduce hazardous fuels and proactively manage forests to
  improve ecosystem resilience.

> **TODO:** Confirm whether a defensible space or community protection priority exists
> separately in the EIP. Pull canonical names from the EIP Project Tracker.

### EIP Indicators

> **TODO:** Link the acres-treated performance measure, and the defensible space
> inspection or parcel compliance measure if one is tracked.

### Local and Regional Plans

- **Lake Tahoe Basin Multi-Jurisdictional Fuel Reduction and Wildfire Prevention
  Strategy** — Defines the Defense Zone and Threat Zone and sets treatment priorities.
- **Community Wildfire Protection Plans** — Local plans that direct Defense Zone work
  at the community scale.

> **TODO:** Verify titles and adoption years, and list the specific CWPPs that cover the
> Basin.

### Example EIP Projects

> **TODO:** Select two or three completed Defense Zone or defensible space projects with
> completion years.

### Monitoring Programs

> **TODO:** Name the monitoring program of record and confirm how FSim outputs should be
> attributed.

## Rationale Details

### Status Rationale

> **TODO:** Cannot be written until the Defense Zone assessment is run. When it is, lead
> with the call, then state total Defense Zone acreage, the percent below four-foot
> modeled flame length, the comparison to the 90 percent standard, and results against
> each of the three distribution criteria separately.
>
> Note that the standard has four separate tests. Decide and document how they combine
> into one status call before running the evaluation — whether all four must pass, or
> whether the 90 percent flame length test governs and the distribution criteria act as
> qualifiers.

### Trend Rationale

**Insufficient Data to Determine Trend.** This is the first evaluation of WUI Defense
Zone fire dynamics as a threshold indicator. Because Defense Zone condition responds
directly and relatively quickly to treatment and regrowth, this indicator is a good
candidate for a shorter evaluation interval than the structural indicators. Fix the
modeling inputs — fuels vintage, weather percentile, and Defense Zone boundary — so
successive runs are comparable.

## Confidence Details

### Confidence of Status

**Low.** No current-condition results are committed to this repository, so no status can
be supported. Beyond that, the assessment is a modeled prediction of fire behavior rather
than a measurement, it depends on a fuels layer whose vintage determines how much recent
treatment and regrowth it captures, and one of the four standard criteria is not
quantitatively defined. Expect this to rise once results exist and the fuels vintage is
documented.

### Confidence of Trend

**Low.** No second assessment period.

### Overall Confidence

**Low.** Both component ratings are low.

## Additional Figures and Resources

> **TODO:** Attach the FSim modeling documentation, the Defense Zone boundary layer
> documentation, and the flame length results figure once produced.

- **Fuel Treatment Chart** — Annual treatment activity over time.
  `DataVisualizations/FuelTreatment_Chart.html`
- **Fuel Treatment Map** — Spatial extent of past treatments.
  `DataVisualizations/FuelTreatment_Map.html`

---

## Source Notes

*Internal only — not published to the indicator page.*

| Element | Source in this repo |
|---|---|
| Standard language and the three distribution criteria | `index.md`, WUI Wildfire Protection section |
| Defense Zone and Threat Zone definitions | `index.md` |
| FSim as the modeling tool | `index.md`, Current Condition subsection |
| Current condition results | **Missing.** `index.md` describes the method but reports no values, and the results notebook's "WUI Standard" section contains basin-wide severity by management zone rather than a Defense Zone assessment |
| Defense Zone boundary layer | **Not identified.** Needs to be named and documented |

### What is needed to finish this page

1. The WUI Defense Zone boundary layer and its source.
2. An FSim run producing modeled flame length across that boundary under 90th percentile
   weather, with the fuels vintage documented.
3. A measurable definition of "well distributed," or its removal from the standard.
4. A documented rule for combining the four standard criteria into one status call.
