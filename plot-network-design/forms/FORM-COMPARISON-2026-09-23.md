# Survey123 Form Comparison

Built September 23, 2026. Form A is the MAC validation protocol (Estes, October 2024). Form B is FIA Phase 2 with the macroplot on. Form C is the hybrid, v1.1 of the TRPA form, implementing Protocol v1.0 DRAFT and the Plot Data Schema. TEON 2025 is Pat Manley's suite, included for the code lists the hybrid shares with it and because Beth's biodiversity work will read both. Units are as stored; feet appear in hints.

## Variable by variable

| Variable | MAC (A) | FIA P2 (B) | Hybrid v1.1 (C) | TEON 2025 |
|---|---|---|---|---|
| Geometry | One circle, 16.0 m or 11.37 m, on 30 m pixel | Four 7.32 m subplots, 2.07 m micro, 17.95 m macro | Concentric: 2.07 m micro, 7.32 m veg and fuels, 17.95 m primary, 56.4 m large-tree | Concentric 7.3, 17.6, 56.5 m |
| Tree floor | 7.6 cm, whole plot | 12.7 cm subplot, 2.5 cm micro, breakpoint macro | 4.0 in (10.2 cm) primary, breakpoint on 56.4 m, 1.0 in micro | 12.5 cm at 7.3 m, 28 cm trees at 17.6 m, 60 cm at 56.5 m |
| Breakpoint | None | 24 in CA, 21 in NV from state | 24.0 in per plot, 21.0 allowed | 60 cm |
| Species | PLANTS from CSV | Same, FIA code column | Same, TEON UNK codes | PLANTS from CSV, UNK |
| DBH | cm | cm, in calculated | in to 0.1, cm calculated | cm |
| Status | L, I, M, D1, D2, D3, FT | 1 live, 2 dead, 3 removed | live, standing dead, down, stump, missing | tree, snag |
| Azimuth, distance | Not recorded | Every tree, m | Every tree, ft, 2 degree tolerance | Not recorded |
| Total height | Tallest per stratum, m | Every tally tree, m | Every tally tree, ft | m, not on 56 m |
| Crown base height | Live trees, m | Omitted, not core | Live trees, ft | m, not on 56 m |
| Crown class | 8 codes, height trees only | FIA 1 to 5 | D, C, I, O, OG | None |
| Crown width | Height trees, averaged, m | Omitted | Every live tree, two axes, ft | None |
| Damage | Health codes | Three agents, location | Three agents, mistletoe, decadence optional | Decadence 0 to 13 |
| Snag decay | 1 to 5 | 1 to 5, year, cause | 1 to 5 | 1 to 5 |
| Saplings | Individual, under 7.6 cm, 4.37 m plot | Micro tree records | Micro, 1.0 to 3.9 in, height | Live and dead counts, 7.3 m |
| Canopy cover | Ocular, 11 lifeform layers, CWHR class | Condition ocular, live and live plus missing | 100 point intercept, crown and effective, stratum | Moosehorn (2024), densiometer at 4 points |
| Fuels transects | Four cardinal, plot radius, from edge | Three per subplot, 7.32 m | Four cardinal, 17.95 m | Three at 0, 120, 240 |
| Fine woody | 1, 10, 100 hr at 3 to 6 m from edge | 4.27 to 6.10 and 4.27 to 7.32 m | 14 to 20 ft and 14 to 24 ft | Counts per transect |
| Coarse woody | Over 7.6 cm, 1 m long, ends, length, decay | 7.6 cm, 0.15 m, ends, hollow, charred optional | 3.0 in, 0.5 ft, hollow, inclination, charred required | 7.5 cm, 0.5 m, ends, decay |
| Duff, litter | Litter, duff, fuel depth at 3.8 and 7.6 m, cm | At 4.27 and 7.32 m, cm | At 20 and 50 ft, in | Litter mm |
| Understory | Lifeform cover and modal height, species by layer | P2 profile, 5 habits by 4 layers, species 3 percent | Same as FIA, Tier 3 only | Species cover by subplot, ground cover |
| Basal area | Gauge or prism by species | None | Prism factor and count, QA only | Prism factor and count (2026) |
| Site descriptors | Shape, slope position, CGA, fuel model, fire severity, history | Forest type, stand size, origin, physiographic, disturbance, treatment | Condition, CWHR crosswalk, disturbance, ownership | Stumps, trash |
| Plot center GNSS | UTM coordinates, accuracy | Per subplot, 15 min, offset | Monument type, method, receiver accuracy, datum, raw file, open-sky offset | Device geopoint |
| Legacy link | None | None | Network, ID, rebar found, offset to design | Site table |
| Monument, witness | Rebar, wired tag; two witness trees | Rebar per Exhibit A; two witness trees | Rebar with stamped cap; three witness trees | Existing rebar |
| Photos | Tag plus N, E, S, W | N, E, S, W, monument, approach | N, E, S, W, canopy, monument, approach | Center 0, 120, 240, transect ends |

Field counts: A 162 fields, 15 repeats. B 140, 10 repeats. C 149, 10 repeats. All three convert under pyxform 4.5 and ODK Validate with no errors or warnings.

## What the hybrid takes from each and why

From FIA Phase 2 it takes the skeleton: the 6.8 ft microplot, the 24.0 ft footprint for vegetation and fuels, the 58.9 ft macroplot radius as the primary plot, condition and disturbance coding, decay class, damage agents, the P2 vegetation profile, and the Brown's transect segments. An FIA crew can read it, and the metrics stay comparable to the FIA-based threshold baseline.

From the MAC protocol it takes what matters for remote sensing: one concentric plot on a grid cell, crown base height and crown width on every live tree, four cardinal fuels transects from one center, and the whole-plot tally. It rejects the MAC ocular cover form because ocular cover cannot be compared to a LiDAR cover fraction at the 40 to 50 percent break that decides VP9.

From the R5 LiDAR booklet and Exhibit A it takes position and monument discipline: static occupation with epochs and PDOP, an explicit offset record, rebar with cap and tag, witness trees with azimuth back to center, and an ordered photo set.

From TEON it takes conventions crews already know: SiteID as site plus date, species from a CSV filtered on a woody column, UNK codes, snag decay 1 to 5 as likert, the 0 to 13 decadence list as an optional multi-select on live trees, and the prism factor and trees-in pair from the 2026 form. A converted site produces a record both networks can read.

The three review additions (position block, legacy-site block, prism check) are in Form C only.

## Where the MAC PDF and Protocol v1.0 disagree

1. Plot size: MAC 16.0 m or 11.37 m; protocol 17.95 m with a 56.4 m large-tree annulus.
2. Tree floor: MAC 7.6 cm; protocol 4.0 in with DBH to 0.1 in so any floor can be recomputed.
3. Heights: MAC measures the tallest tree per stratum; protocol measures every tally tree.
4. Position: MAC records no azimuth or distance per tree; protocol requires both at 2 degrees and 0.1 ft.
5. Canopy cover: MAC ocular by lifeform; protocol 100 point intercept with two determinations.
6. Fuels: MAC reads from the plot edge with fine fuels at 3 to 6 m and CWD at 1 m minimum; protocol reads from center on the FIA segments and admits 0.5 ft.
7. Basal area: MAC has a variable-radius section; protocol forbids variable radius, so the hybrid carries the prism as QA only.
8. Breakpoint: the brief says 21 in for Nevada; protocol selects 24.0 in for both states pending confirmation. Form C defaults to 24.0 and accepts 21.0; Form B computes it from state.

## Unresolved in the MAC PDF

- "Twelve classes" of vegetation cover are cited; the Life Form Cheatsheet lists eleven, which are implemented.
- Tree status header lists L, D, S, X, Y; the definitions give L, I, M, D1, D2, D3, FT. The defined codes are used.
- Health codes reuse A and M for two agents each. Unique codes carry the printed letter in the label.
- Depth measurements have no unit; cm is used to match Exhibit A. The note "11.3, 7.5, and 3.7 if m0 is at center" is ambiguous and not implemented.
- Witness tree distance is not stated as slope or horizontal; horizontal is asked for.
- GPS is "sub-centimeter" with no fallback or metadata; the form records what the unit reports.
- Crown class cheatsheet has eight codes but the height section names four strata; the four strata are used.
- Tables A2, C2 to C4, and the cheatsheets are page images; check transcribed codes against the source.
- No per-tree position, no monument spec beyond flagging and a wired tag, and no photo labeling rule; Exhibit A fills these.
