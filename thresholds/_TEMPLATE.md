# Indicator Page Copy Template

Use this file as the starting point for any new Threshold Indicator page on
`thresholds.laketahoeinfo.org`. Every `##` heading below maps to a field or panel
on the live indicator page, in the order it appears on screen. Keep the headings
exactly as written so the copy can be pasted field-by-field into the CMS.

Conventions for every file in this folder:

- Frontmatter holds the structured fields (indicator number, category, status, trend, confidence).
- Body sections hold prose that gets pasted into the matching CMS field.
- `> **TODO:**` marks content that still needs a decision, a source, or a sign-off.
  Nothing with an open TODO should be published.
- TRPA style: Oxford comma, one space between sentences, spell out one through nine,
  numerals for 10 and up, "50 percent" rather than "50%" in body prose (tables and
  standards may use the symbol), abbreviate months with specific dates (Jan. 1, 2026).
- `## Source Notes` is internal only. It does not get pasted anywhere; it exists so a
  reviewer can trace every number back to the file that produced it.

---

```yaml
---
indicator_number:
indicator_name:
url:
category:            # Evaluation Overview > <Category>
reporting_category:  # > <Reporting Category>
status:              # Considerably Better Than Target | Somewhat Better Than Target | At or Somewhat Better Than Target | Somewhat Worse Than Target | Considerably Worse Than Target | Insufficient Data
trend:               # Rapid Improvement | Moderate Improvement | Little or No Change | Moderate Decline | Rapid Decline | Insufficient Data to Determine Trend
confidence:          # High | Moderate | Low
evaluation_year:
draft_status:        # Draft | In Review | Approved
---
```

---

## Indicator Overview

Intro paragraph that sits above the STATUS panel. Three to six sentences. Say what the
indicator measures, why the Region tracks it, what the primary human and natural drivers
are, and who collects the data.

## Chart Caption

One or two sentences describing what the Summary chart shows, including the period of
record and any caveats about breaks in the record or changes in method.

## Evaluation

| Field | Value |
|---|---|
| Status | |
| Trend | |
| Confidence | |

## Applicable Standard

Standard code and the verbatim standard language.

## Key Points

- Four to six bullets. Each one stands alone and states a fact a reader can act on.

## Evaluation Map

Caption for the map panel: what is drawn, at what resolution, and from what source layer.

## About the Threshold

### Relevance

Why this matters ecologically and to the public. Two to four sentences.

### Human and Environmental Drivers

What moves the number, split between human activity and natural process.

## Delivering and Measuring Success

### EIP Action Priorities

- **Name** — one-sentence description.

### EIP Indicators

- **Name** — one-sentence description.

### Local and Regional Plans

- **Name** — one sentence on how the plan relates to this indicator.

### Example EIP Projects

- **Name** — one sentence on the project and its completion year.

### Monitoring Programs

- Name of the monitoring program that produces the data.

## Rationale Details

### Status Rationale

Lead with the status call, then the evidence: evaluation period, the values observed,
and the arithmetic that produced the call.

### Trend Rationale

Lead with the trend call, then the method (for example, Theil-Sen robust linear
regression), the period analyzed, and the rate of change.

## Confidence Details

### Confidence of Status

### Confidence of Trend

### Overall Confidence

Include the combination rule used, for example: if one rating is high and the other
is low, the overall rating is medium.

## Additional Figures and Resources

- Title, file type, and a one-sentence description for each attachment.

---

## Source Notes

*Internal only — not published to the indicator page.*

| Element | Source in this repo |
|---|---|
| | |
