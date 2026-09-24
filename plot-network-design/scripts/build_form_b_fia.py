#!/usr/bin/env python3
"""FORM B: TRPA_FIA_Phase2_Survey123.xlsx

FIA Phase 2 plot with the macroplot switched on, in metric field names with
feet noted in hints. Four 24.0 ft (7.32 m) subplots in the standard cluster,
6.8 ft (2.07 m) microplot offset 12 ft (3.66 m) at 90 degrees from each
subplot center, 58.9 ft (17.95 m) macroplot on every subplot. Tally: 5.0 in
(12.7 cm) DBH and up on the subplot, 1.0 to 4.9 in (2.5 to 12.6 cm) on the
microplot, breakpoint and up on the macroplot (24 in California, 21 in
Interior West, which covers Nevada). Total height measured on every tally
tree. Condition-level ocular canopy cover. P2 vegetation profile and DWM on
three 24 ft transects per subplot at 30, 150, and 270 degrees.

Monument and photo detail follows EXHIBIT A (rebar, cap, tag, two witness
trees, four cardinal photos) since FIA core uses pins, not permanent rebar.
GNSS block follows the FIA High Performance GNSS standard and the R5 LiDAR
booklet (offset azimuth and distance from the monument to the receiver).
Codes are FIA National Core Field Guide v9.x values where the guide has
them; verify against the PNW 2026 v9.5 manual before publishing.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xlsform_common import FormBuilder, finish, STR, INT, DBL, TODAY  # noqa: E402

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/outputs/survey123"
OUT = os.path.join(OUT_DIR, "TRPA_FIA_Phase2_Survey123.xlsx")

fb = FormBuilder(
    form_title="TRPA FIA Phase 2 Plot with Macroplot",
    form_id="trpa_fia_phase2_macro",
    instance_name='concat("FIA ", ${plot_id}, " ", format-date(${visit_date}, "%Y-%m-%d"))',
    version=TODAY,
)
row, note, grp, endgrp, rep, endrep, choices = (
    fb.row, fb.note, fb.grp, fb.endgrp, fb.rep, fb.endrep, fb.choices)

# ----------------------------------------------------------------------------
# CHOICE LISTS
# ----------------------------------------------------------------------------
choices("yesno", [("yes", "Yes"), ("no", "No")])
choices("state", [("CA", "California (PNW FIA, breakpoint 24 in)"),
                  ("NV", "Nevada (Interior West FIA, breakpoint 21 in)")])
choices("sample_kind", [("1", "1 - Initial plot establishment"),
                        ("2", "2 - Remeasurement"),
                        ("3", "3 - Replacement plot")])
choices("plot_status", [("1", "1 - Sampled, at least one accessible forest condition"),
                        ("2", "2 - Sampled, no accessible forest condition"),
                        ("3", "3 - Nonsampled")])
choices("nonsample_reason", [
    ("01", "01 - Outside US boundary"), ("02", "02 - Denied access"),
    ("03", "03 - Hazardous"), ("05", "05 - Lost data"), ("06", "06 - Lost plot"),
    ("07", "07 - Wrong location"), ("08", "08 - Skipped visit"),
    ("09", "09 - Dropped plot"), ("10", "10 - Other"),
    ("11", "11 - Ocean"),
])
choices("cond_status", [
    ("1", "1 - Accessible forest land"),
    ("2", "2 - Nonforest land"),
    ("3", "3 - Noncensus water"),
    ("4", "4 - Census water"),
    ("5", "5 - Nonsampled, possible forest land"),
])
choices("forest_type", [
    ("201", "201 Douglas-fir"), ("221", "221 Ponderosa pine"),
    ("222", "222 Incense cedar"), ("224", "224 Sugar pine"),
    ("225", "225 Jeffrey pine"), ("261", "261 White fir"),
    ("262", "262 Red fir"), ("270", "270 Mountain hemlock"),
    ("281", "281 Lodgepole pine"), ("366", "366 Limber pine"),
    ("367", "367 Whitebark pine"), ("368", "368 Miscellaneous western softwoods"),
    ("369", "369 Western juniper"), ("371", "371 California mixed conifer"),
    ("901", "901 Aspen"), ("922", "922 Cottonwood"),
    ("962", "962 Other hardwoods"), ("999", "999 Nonstocked"),
])
choices("stand_size", [
    ("1", "1 - Large diameter (softwoods 11.0 in and up, hardwoods 9.0 in and up)"),
    ("2", "2 - Medium diameter (5.0 to 10.9 in softwoods, 5.0 to 8.9 in hardwoods)"),
    ("3", "3 - Small diameter (under 5.0 in)"),
    ("5", "5 - Nonstocked"),
])
choices("stand_origin", [("0", "0 - Natural stand"), ("1", "1 - Clear evidence of planting")])
choices("owner_group", [
    ("10", "10 - Forest Service"), ("20", "20 - Other federal"),
    ("30", "30 - State and local government"), ("40", "40 - Private"),
])
choices("physclass", [
    ("11", "11 - Dry tops"), ("12", "12 - Dry slopes"), ("13", "13 - Deep sands"),
    ("19", "19 - Other xeric"), ("21", "21 - Flatwoods"), ("22", "22 - Rolling uplands"),
    ("23", "23 - Moist slopes and coves"), ("24", "24 - Narrow floodplains and bottomlands"),
    ("25", "25 - Broad floodplains and bottomlands"), ("29", "29 - Other mesic"),
    ("31", "31 - Swamps and bogs"), ("32", "32 - Small drains"),
    ("34", "34 - Beaver ponds"), ("39", "39 - Other hydric"),
])
choices("disturbance", [
    ("00", "00 - None"), ("10", "10 - Insect damage"), ("12", "12 - Insect, defoliators"),
    ("20", "20 - Disease damage"), ("30", "30 - Fire, crown and ground"),
    ("31", "31 - Ground fire"), ("32", "32 - Crown fire"),
    ("40", "40 - Animal damage"), ("41", "41 - Beaver"), ("42", "42 - Porcupine"),
    ("43", "43 - Deer or ungulate"), ("44", "44 - Bear"), ("46", "46 - Domestic animal"),
    ("50", "50 - Weather damage"), ("51", "51 - Ice"), ("52", "52 - Wind"),
    ("53", "53 - Flooding"), ("54", "54 - Drought"),
    ("60", "60 - Vegetation, suppression or competition"), ("70", "70 - Unknown"),
    ("80", "80 - Human caused"), ("90", "90 - Geologic"), ("91", "91 - Landslide"),
    ("92", "92 - Avalanche"), ("95", "95 - Other geologic"),
])
choices("treatment", [
    ("00", "00 - None"), ("10", "10 - Cutting"), ("20", "20 - Site preparation"),
    ("30", "30 - Artificial regeneration"), ("40", "40 - Natural regeneration"),
    ("50", "50 - Other silvicultural treatment"),
])
choices("subplot_status", [
    ("1", "1 - Sampled, at least one accessible forest condition"),
    ("2", "2 - Sampled, no accessible forest condition"),
    ("3", "3 - Nonsampled"),
])
choices("tally_unit", [
    ("micro", "Microplot 6.8 ft (2.07 m): 1.0 to 4.9 in DBH"),
    ("sub", "Subplot 24.0 ft (7.32 m): 5.0 in to below breakpoint"),
    ("macro", "Macroplot 58.9 ft (17.95 m): breakpoint and up"),
])
choices("tree_status", [
    ("1", "1 - Live"), ("2", "2 - Dead (standing, 1.37 m unbroken bole, lean under 45 degrees)"),
    ("3", "3 - Removed (cut and removed, remeasurement only)"),
])
choices("reconcile", [
    ("1", "1 - Ingrowth"), ("2", "2 - Through growth"), ("3", "3 - Missed live"),
    ("4", "4 - Missed dead"), ("5", "5 - Shrank"), ("6", "6 - Physical movement"),
    ("7", "7 - Cruiser error"), ("8", "8 - Procedural change"),
])
choices("height_method", [
    ("1", "1 - Total and actual length measured"),
    ("2", "2 - Total length estimated, actual length measured"),
    ("3", "3 - Total and actual length estimated"),
    ("4", "4 - Total length estimated for a broken top, actual measured"),
])
choices("crown_class", [
    ("1", "1 - Open grown"), ("2", "2 - Dominant"), ("3", "3 - Codominant"),
    ("4", "4 - Intermediate"), ("5", "5 - Overtopped"),
])
choices("damage_agent", [
    ("00", "00 - No damage"), ("10", "10 - General insects"),
    ("11", "11 - Bark beetles"), ("12", "12 - Defoliators"),
    ("13", "13 - Chewing insects"), ("14", "14 - Sucking insects"),
    ("15", "15 - Boring insects"), ("19", "19 - Seed, cone, flower insects"),
    ("20", "20 - General diseases"), ("21", "21 - Root and butt diseases"),
    ("22", "22 - Stem decays and cankers"), ("23", "23 - Parasitic and epiphytic plants"),
    ("24", "24 - Decline complexes"), ("25", "25 - Dwarf mistletoe"),
    ("26", "26 - Foliage diseases"), ("27", "27 - Stem rusts"),
    ("30", "30 - Fire"), ("40", "40 - Animals"), ("50", "50 - Abiotic damage, weather"),
    ("60", "60 - Competition and suppression"), ("70", "70 - Human activities"),
    ("90", "90 - Unknown"),
])
choices("severity", [
    ("1", "1 - Bole"), ("2", "2 - Roots and stump"), ("3", "3 - Crown, branch or foliage"),
])
choices("decay_class", [
    ("1", "1 - All limbs and branches present, top intact, bark intact"),
    ("2", "2 - Few limbs, no fine branches, top may be broken"),
    ("3", "3 - Limb stubs only, top broken, some bark loss"),
    ("4", "4 - Few or no limb stubs, top broken, sapwood sloughing"),
    ("5", "5 - No evidence of branches, stump or shell, heartwood only"),
])
choices("cause_of_death", [
    ("10", "10 - Insect"), ("20", "20 - Disease"), ("30", "30 - Fire"),
    ("40", "40 - Animal"), ("50", "50 - Weather"),
    ("60", "60 - Vegetation, suppression, competition"), ("70", "70 - Unknown"),
    ("80", "80 - Silvicultural or land clearing"), ("90", "90 - Physical"),
])
choices("solution_type", [
    ("pp_fixed", "Post-processed fixed"), ("pp_float", "Post-processed float"),
    ("rtk_fixed", "RTK fixed"), ("rtk_float", "RTK float"),
    ("dgps", "Code differential (DGPS)"), ("autonomous", "Autonomous"),
])
choices("growth_habit", [
    ("TT", "Tally tree species"), ("NT", "Non-tally tree species"),
    ("SH", "Shrub, subshrub, or woody vine"), ("FB", "Forb"), ("GR", "Graminoid"),
])
choices("veg_layer", [
    ("L1", "Layer 1, 0 to 2.0 ft (0 to 0.6 m)"),
    ("L2", "Layer 2, 2.1 to 6.0 ft (0.6 to 1.8 m)"),
    ("L3", "Layer 3, 6.1 to 16.0 ft (1.8 to 4.9 m)"),
    ("L4", "Layer 4, above 16 ft (4.9 m)"),
    ("AER", "Aerial total, all layers"),
])
choices("monument_status", [
    ("new", "New installation"), ("found_good", "Found, good condition"),
    ("found_damaged", "Found, damaged or displaced"), ("replaced", "Not found, replaced"),
])
choices("photo_dir", [
    ("N", "North, 0 degrees"), ("E", "East, 90 degrees"), ("S", "South, 180 degrees"),
    ("W", "West, 270 degrees"), ("monument", "Monument"), ("approach", "Approach"),
    ("other", "Other"),
])

# ----------------------------------------------------------------------------
# SURVEY
# ----------------------------------------------------------------------------
note("intro", "**FIA Phase 2 plot with macroplot, metric.**  \n"
     "Four subplots 7.32 m (24.0 ft). Subplots 2, 3, 4 at 0, 120, 240 degrees, "
     "36.58 m (120 ft) from subplot 1. Microplot 2.07 m (6.8 ft), centered 3.66 m (12 ft) "
     "at 90 degrees from each subplot center. Macroplot 17.95 m (58.9 ft) on every subplot.  \n"
     "Tally: 12.7 cm (5.0 in) and up on the subplot; 2.5 to 12.6 cm (1.0 to 4.9 in) on the "
     "microplot; breakpoint and up on the macroplot only.")

# --- A. Plot ---------------------------------------------------------------------
grp("plot_admin", "A. Plot")
fb.text("plot_id", "Plot ID", length=20, required="yes")
fb.date("visit_date", "Visit date", required="yes", default="today()")
fb.calc("site_id", "concat(${plot_id}, '_', format-date(${visit_date}, '%Y%m%d'))",
        ftype=STR, **{"bind::esri:fieldLength": "40"})
note("site_id_note", "SiteID: ${site_id}")
fb.select1("state", "state", "State", required="yes")
fb.calc("breakpoint_dia_in", "if(${state}='NV', 21.0, 24.0)")
fb.calc("breakpoint_dia_cm", "round(${breakpoint_dia_in} * 2.54, 1)")
note("bp_note", "Macroplot breakpoint for this plot: ${breakpoint_dia_in} in (${breakpoint_dia_cm} cm)")
fb.select1("sample_kind", "sample_kind", "Sample kind", length=5, required="yes")
fb.text("crew_lead", "Crew lead", length=60, required="yes")
fb.text("crew_members", "Other crew members", length=200)
fb.datetime("plot_start_time", "Time started at subplot 1", default="now()")
fb.select1("plot_status", "plot_status", "Plot status", length=5, required="yes")
fb.select1("nonsample_reason", "nonsample_reason", "Nonsampled reason", length=5,
           relevant="${plot_status}='3'", required="yes")
fb.integer("declination_deg", "Magnetic declination set on compass (degrees east)",
           required="yes", constraint=". >= 0 and . <= 30",
           hint="All azimuths are true north. Tahoe is roughly 13 degrees east; verify daily against a known bearing.")
fb.geopoint("nav_point", "Navigation point at subplot 1 (device GPS)", required="yes")
fb.text("plot_notes", "Plot notes", length=2000, appearance="multiline")
endgrp()

# --- B. Conditions --------------------------------------------------------------
note("cond_note", "**B. Condition classes.** Condition 1 is the condition at subplot 1 "
     "center. Add a condition only where a boundary in condition status, forest type, "
     "stand size, owner group, regeneration status, or reserved status crosses a subplot "
     "or macroplot. Boundary mapping (contrasting condition azimuths) is not carried in "
     "this form; record it in notes.")
rep("condition", "Condition class")
fb.calc("cond_id", "position(..)", ftype=INT)
note("cond_label", "Condition ${cond_id}")
fb.select1("cond_status", "cond_status", "Condition status", length=5, required="yes")
fb.select1("forest_type", "forest_type", "Forest type (FIA code)", length=5,
           relevant="${cond_status}='1'", required="yes")
fb.select1("stand_size", "stand_size", "Stand size class", length=5,
           relevant="${cond_status}='1'", required="yes")
fb.select1("stand_origin", "stand_origin", "Stand origin", length=5,
           relevant="${cond_status}='1'", required="yes")
fb.select1("owner_group", "owner_group", "Owner group", length=5, required="yes")
fb.select1("physclass", "physclass", "Physiographic class", length=5,
           relevant="${cond_status}='1'", required="yes")
fb.integer("cond_slope_pct", "Condition slope (percent)", required="yes",
           relevant="${cond_status}='1'", constraint=". >= 0 and . <= 155")
fb.integer("cond_aspect_deg", "Condition aspect (degrees, 0 when slope under 5 percent)",
           relevant="${cond_status}='1'", required="yes", constraint=". >= 0 and . <= 360")
fb.integer("canopy_cover_live_pct", "Live canopy cover (percent, ocular)",
           relevant="${cond_status}='1'", required="yes", constraint=". >= 0 and . <= 100",
           hint="Condition-level ocular estimate: vertical projection of live tally trees, saplings, and seedlings; within-crown gaps count as cover")
fb.integer("canopy_cover_live_missing_pct", "Live plus missing canopy cover (percent)",
           relevant="${cond_status}='1'", required="yes",
           constraint=". >= ${canopy_cover_live_pct} and . <= 100",
           hint="Add cover lost to mortality or removal within the last 10 years")
for i in (1, 2, 3):
    fb.select1("disturbance", f"disturbance{i}", f"Disturbance {i}", length=5,
               relevant="${cond_status}='1'", default="00" if i == 1 else "",
               hint="Since the last measurement, or 5 years for a new plot, affecting at least 1 acre" if i == 1 else "")
    fb.integer(f"disturbance{i}_year", f"Disturbance {i} year",
               relevant=f"${{disturbance{i}}}!='' and ${{disturbance{i}}}!='00'",
               required="yes", constraint=". >= 1900 and . <= 2100")
for i in (1, 2, 3):
    fb.select1("treatment", f"treatment{i}", f"Treatment {i}", length=5,
               relevant="${cond_status}='1'", default="00" if i == 1 else "")
    fb.integer(f"treatment{i}_year", f"Treatment {i} year",
               relevant=f"${{treatment{i}}}!='' and ${{treatment{i}}}!='00'",
               required="yes", constraint=". >= 1900 and . <= 2100")
fb.text("cond_notes", "Condition notes", length=500, appearance="multiline")
endrep()

# --- C. Subplots ----------------------------------------------------------------
note("subplot_note", "**C. Subplots.** Four subplots, entered in order 1 to 4. "
     "Subplot 2 at 0 degrees, 3 at 120 degrees, 4 at 240 degrees, each 36.58 m (120 ft) "
     "horizontal from subplot 1. Microplot center 3.66 m (12 ft) at 90 degrees from each subplot center.")
rep("subplot", "Subplot", repeat_count="4")
fb.calc("subplot_num", "position(..)", ftype=INT)
fb.calc("subplot_az", "if(${subplot_num}=1, 0, (${subplot_num} - 2) * 120)", ftype=INT)
note("subplot_label", "Subplot ${subplot_num}. Center azimuth from subplot 1: ${subplot_az} degrees, 36.58 m (120 ft).")
fb.select1("subplot_status", "subplot_status", "Subplot status", length=5, required="yes")
fb.integer("subp_center_cond", "Condition at subplot center", required="yes",
           constraint=". >= 1 and . <= 9")
fb.integer("micro_center_cond", "Condition at microplot center", required="yes",
           constraint=". >= 1 and . <= 9")
fb.integer("macro_center_cond", "Condition at macroplot center", required="yes",
           constraint=". >= 1 and . <= 9", hint="Same point as subplot center")
fb.integer("subp_slope_pct", "Subplot slope (percent)", constraint=". >= 0 and . <= 155")
fb.integer("subp_aspect_deg", "Subplot aspect (degrees)", constraint=". >= 0 and . <= 360")

grp("subp_gnss", "Subplot center position (High Performance GNSS)")
note("gnss_note", "Survey-grade receiver on a tripod over the subplot center, 15 minutes minimum, raw observations logged and post-processed. Establish azimuths before the receiver is set up; it disturbs the compass.")
fb.geopoint("subp_point", "Device position at subplot center", required="yes")
fb.text("receiver_model", "GNSS receiver make and model", length=80, required="yes")
fb.integer("occ_minutes", "Occupation length (minutes)", required="yes",
           constraint=". >= 15", constraint_message="Minimum 15 minute occupation")
fb.integer("epochs", "Epochs logged")
fb.decimal("pdop", "PDOP")
fb.select1("solution_type", "solution_type", "Solution type achieved in the field",
           required="yes")
fb.decimal("rcvr_horiz_acc_m", "Horizontal accuracy reported by the receiver (m)",
           required="yes", constraint=". >= 0")
fb.text("raw_file", "Raw observation file name", length=120, required="yes")
fb.yesno("offset_used", "Receiver offset from the subplot center", required="yes", default="no")
fb.decimal("offset_azimuth_deg", "Azimuth from subplot center to receiver (degrees)",
           relevant="${offset_used}='yes'", required="yes", constraint=". >= 0 and . <= 360")
fb.decimal("offset_distance_m", "Horizontal distance from subplot center to receiver (m)",
           relevant="${offset_used}='yes'", required="yes", constraint=". > 0 and . <= 100",
           hint="Laser rangefinder, nearest 0.1 m (0.3 ft)")
endgrp()

# --- C1. Trees on this subplot ---------------------------------------------------
note("tree_note", "**Trees.** Number trees clockwise from north within each tally unit. "
     "Every tally tree gets total height. Breakpoint trees are macroplot trees wherever "
     "they stand inside 17.95 m, never subplot trees.")
rep("tree", "Tree")
fb.integer("tree_num", "Tree number", required="yes", constraint=". > 0 and . < 1000")
fb.integer("tree_cond", "Condition class of the tree", required="yes", default="1",
           constraint=". >= 1 and . <= 9")
fb.select1("tally_unit", "tally_unit", "Tally unit", required="yes")
fb.decimal("azimuth_deg", "Azimuth from subplot center (degrees)", required="yes",
           constraint=". >= 1 and . <= 360",
           hint="Microplot trees: azimuth and distance from the MICROPLOT center. 360 for due north, never 0.")
fb.decimal("dist_m", "Horizontal distance from center (m)", required="yes",
           constraint="if(${tally_unit}='micro', . > 0 and . <= 2.07, "
                      "if(${tally_unit}='sub', . > 0 and . <= 7.32, . > 0 and . <= 17.95))",
           constraint_message="Microplot 2.07 m (6.8 ft), subplot 7.32 m (24.0 ft), macroplot 17.95 m (58.9 ft). In or out is decided by horizontal distance to the pith at ground level.",
           hint="Nearest 0.01 m. 7.32 m = 24.0 ft. 17.95 m = 58.9 ft.")
fb.species("species", "Species (PLANTS symbol)")
fb.unk_species("species", "species_unk")
fb.select1("tree_status", "tree_status", "Tree status", length=5, required="yes")
fb.select1("reconcile", "reconcile", "Reconcile code (remeasurement only)", length=5,
           relevant="${sample_kind}='2'")
fb.decimal("dbh_cm", "DBH (cm, to 0.1)", required="yes",
           relevant="${tree_status}!='3'",
           constraint="if(${tally_unit}='micro', . >= 2.5 and . < 12.7, "
                      "if(${tally_unit}='sub', . >= 12.7 and . < ${breakpoint_dia_cm}, "
                      ". >= ${breakpoint_dia_cm} and . <= 400))",
           constraint_message="Microplot 2.5 to 12.6 cm (1.0 to 4.9 in). Subplot 12.7 cm (5.0 in) to below the breakpoint. Macroplot at or above the breakpoint.",
           hint="At 1.37 m (4.5 ft) on the uphill side. 12.7 cm = 5.0 in. Breakpoint ${breakpoint_dia_cm} cm = ${breakpoint_dia_in} in.")
fb.calc("dbh_in", "round(${dbh_cm} div 2.54, 1)")
fb.decimal("dbh_height_m", "Height of diameter measurement (m)", default="1.37",
           constraint=". > 0 and . <= 10", hint="1.37 m = 4.5 ft. Record where DBH is taken off breast height.")
fb.decimal("total_height_m", "Total height (m, to 0.1)", required="yes",
           relevant="${tree_status}!='3'", constraint=". > 0 and . <= 120",
           hint="Measured on every tally tree. Include an estimate of the missing portion of a broken top. 1 m = 3.28 ft.")
fb.calc("total_height_ft", "round(${total_height_m} * 3.2808, 1)")
fb.yesno("broken_top", "Broken or missing top", default="no",
         relevant="${tree_status}!='3'")
fb.decimal("actual_length_m", "Actual length to the break (m)",
           relevant="${broken_top}='yes'", required="yes",
           constraint=". > 0 and . < ${total_height_m}",
           constraint_message="Actual length must be less than total height")
fb.select1("height_method", "height_method", "Height method", length=5, required="yes",
           relevant="${tree_status}!='3'", default="1")
fb.select1("crown_class", "crown_class", "Crown class", length=5,
           relevant="${tree_status}='1'", required="yes")
fb.integer("uncomp_crown_ratio_pct", "Uncompacted live crown ratio (percent)",
           relevant="${tree_status}='1'", required="yes", constraint=". >= 0 and . <= 99",
           hint="Lowest live branch to the top, gaps included, nearest 5 percent unless 1 percent is meaningful")
fb.integer("comp_crown_ratio_pct", "Compacted live crown ratio (percent)",
           relevant="${tree_status}='1'", required="yes",
           constraint=". >= 0 and . <= ${uncomp_crown_ratio_pct}",
           constraint_message="Compacted ratio cannot exceed the uncompacted ratio")
for i in (1, 2, 3):
    fb.select1("damage_agent", f"damage{i}", f"Damage agent {i}", length=5,
               relevant="${tree_status}='1'",
               default="00" if i == 1 else "")
    fb.select1("severity", f"damage{i}_location", f"Damage {i} location", length=5,
               relevant=f"${{damage{i}}}!='' and ${{damage{i}}}!='00'")
fb.select1("decay_class", "decay_class", "Decay class", length=5,
           relevant="${tree_status}='2'", required="yes", appearance="likert")
fb.integer("mortality_year", "Estimated year of death",
           relevant="${tree_status}='2'", constraint=". >= 1900 and . <= 2100")
fb.select1("cause_of_death", "cause_of_death", "Cause of death", length=5,
           relevant="${tree_status}='2'")
fb.integer("lean_deg", "Lean from vertical (degrees)", constraint=". >= 0 and . <= 90",
           hint="Not FIA core. Standing dead must lean under 45 degrees to be tallied.")
fb.text("tree_notes", "Tree notes", length=500, appearance="multiline")
endrep()

rep("seedling", "Seedling count by species (microplot)")
fb.species("seed_species", "Species (PLANTS symbol)")
fb.unk_species("seed_species", "seed_species_unk")
fb.integer("seed_cond", "Condition class", required="yes", default="1",
           constraint=". >= 1 and . <= 9")
fb.integer("seed_count", "Count", required="yes", constraint=". > 0",
           hint="Under 2.5 cm (1.0 in) DBH. Conifers at least 15 cm (6 in) tall, hardwoods at least 30 cm (12 in).")
endrep()

# --- C2. DWM transects on this subplot --------------------------------------------
note("dwm_note", "**Down woody material.** Three transects from subplot center at 30, 150, "
     "and 270 degrees, each 7.32 m (24.0 ft) horizontal. Fine woody on the 4.27 to 6.10 m "
     "(14 to 20 ft) segment for small and medium, 4.27 to 7.32 m (14 to 24 ft) for large. "
     "Coarse woody on the full 7.32 m. Duff, litter, and fuelbed depth at 4.27 m (14 ft) and 7.32 m (24 ft).")
rep("transect", "DWM transect", repeat_count="3")
fb.calc("tr_index", "position(..)", ftype=INT)
fb.calc("tr_azimuth", "30 + (${tr_index} - 1) * 120", ftype=INT)
note("tr_label", "Transect at ${tr_azimuth} degrees from subplot ${subplot_num} center")
fb.integer("fwd_small_count", "Small FWD count, 0 to 0.6 cm (0 to 0.24 in), 4.27 to 6.10 m",
           required="yes", constraint=". >= 0 and . <= 999")
fb.integer("fwd_medium_count", "Medium FWD count, 0.6 to 2.5 cm (0.25 to 0.9 in), 4.27 to 6.10 m",
           required="yes", constraint=". >= 0 and . <= 999")
fb.integer("fwd_large_count", "Large FWD count, 2.5 to 7.6 cm (1.0 to 2.9 in), 4.27 to 7.32 m",
           required="yes", constraint=". >= 0 and . <= 999")
for pt, ft in (("427", "14 ft"), ("732", "24 ft")):
    m = "4.27 m" if pt == "427" else "7.32 m"
    fb.decimal(f"duff_{pt}_cm", f"Duff depth at {m} ({ft}) (cm)", required="yes",
               constraint=". >= 0 and . <= 60", hint="Nearest 0.1 in is 0.25 cm")
    fb.decimal(f"litter_{pt}_cm", f"Litter depth at {m} ({ft}) (cm)", required="yes",
               constraint=". >= 0 and . <= 250")
    fb.decimal(f"fuelbed_{pt}_cm", f"Fuelbed depth at {m} ({ft}) (cm)", required="yes",
               constraint=". >= 0 and . <= 500")

rep("cwd", "CWD piece on this transect")
fb.decimal("cwd_slope_dist_m", "Slope distance along transect (m)", required="yes",
           constraint=". > 0 and . <= 7.5", hint="7.32 m = 24 ft")
fb.integer("cwd_cond", "Condition class", default="1", constraint=". >= 1 and . <= 9")
fb.species("cwd_species", "Species", required="")
fb.decimal("cwd_dia_cm", "Diameter at transect intersection (cm)", required="yes",
           constraint=". >= 7.6",
           constraint_message="CWD is 7.6 cm (3.0 in) or larger at the intersection")
fb.decimal("cwd_dia_large_cm", "Large end diameter (cm)", required="yes",
           constraint=". >= ${cwd_dia_cm}")
fb.decimal("cwd_dia_small_cm", "Small end diameter (cm)", required="yes",
           constraint=". > 0 and . <= ${cwd_dia_large_cm}")
fb.decimal("cwd_length_m", "Piece length (m)", required="yes", constraint=". >= 0.15",
           hint="Pieces 0.15 m (0.5 ft) and longer")
fb.select1("decay_class", "cwd_decay", "Decay class", length=5, required="yes",
           appearance="likert")
fb.yesno("cwd_hollow", "Hollow at the intersection", default="no")
fb.decimal("cwd_hollow_dia_cm", "Hollow diameter (cm)", relevant="${cwd_hollow}='yes'",
           required="yes", constraint=". > 0 and . < ${cwd_dia_cm}")
fb.integer("cwd_charred_pct", "Percent charred (Core Optional)",
           constraint=". >= 0 and . <= 100")
endrep()
endrep()

# --- C3. P2 vegetation profile on this subplot ------------------------------------
note("veg_note", "**P2 vegetation profile, 7.32 m (24.0 ft) subplot.** Ocular cover to the "
     "nearest 1 percent for five growth habits in four layers plus the aerial total. "
     "Species at 3 percent or more listed individually. One condition per subplot assumed.")
rep("veg_cover", "Cover by growth habit and layer")
fb.select1("growth_habit", "gh", "Growth habit", length=5, required="yes")
fb.select1("veg_layer", "layer", "Height layer", length=5, required="yes")
fb.integer("cover_pct", "Cover (percent)", required="yes", constraint=". >= 0 and . <= 100")
endrep()

rep("veg_species", "Species with 3 percent cover or more")
fb.species("vs_species", "Species (PLANTS symbol)", woody_only=False)
fb.unk_species("vs_species", "vs_species_unk")
fb.integer("vs_cover_pct", "Total aerial cover (percent)", required="yes",
           constraint=". >= 3 and . <= 100")
endrep()

fb.text("subplot_notes", "Subplot notes", length=1000, appearance="multiline")
endrep()   # subplot

# --- D. Monument and photos (Exhibit A) --------------------------------------------
grp("monument", "D. Monument at subplot 1 (Exhibit A)")
fb.select1("monument_status", "monument_status", "Monument status", required="yes")
fb.yesno("rebar_set", "Rebar with cap and metal tag labeled with the plot number, at least 30 cm (1 ft) above ground",
         required="yes")
fb.text("plot_tag_number", "Tag number", length=20)
fb.yesno("subplot_pins", "Pins set at subplots 2, 3, and 4", required="yes")
fb.yesno("approach_flags", "Two white flags hung at eye level from the direction of access",
         required="yes")
fb.text("access_narrative", "Access route narrative", length=2000, appearance="multiline",
        required="yes")
fb.geopoint("park_point", "Parking or approach point")
endgrp()

rep("witness", "Witness tree (two of the largest trees, tag facing plot center)", repeat_count="2")
fb.integer("wt_tag", "Tag number", required="yes")
fb.species("wt_species", "Species")
fb.decimal("wt_dbh_cm", "DBH (cm)", required="yes", constraint=". > 0")
fb.decimal("wt_azimuth_deg", "Azimuth from tree to subplot 1 center (degrees)", required="yes",
           constraint=". >= 0 and . <= 360")
fb.decimal("wt_distance_m", "Horizontal distance (m)", required="yes",
           constraint=". > 0 and . <= 60")
endrep()

rep("photo", "Photograph", repeat_count="6")
fb.select1("photo_dir", "photo_direction", "Photo type", required="yes",
           hint="Four cardinal directions from subplot 1 center, same zoom, plus monument and approach")
fb.image("photo_file", "Photograph", required="yes", appearance="annotate")
endrep()

# --- E. Closeout ------------------------------------------------------------------
grp("closeout", "E. Closeout")
fb.datetime("plot_end_time", "Time finished", required="yes")
fb.integer("crew_minutes_on_plot", "Crew minutes on plot", required="yes",
           constraint=". > 0 and . <= 1440")
fb.yesno("qa_flag", "Flag this plot for review", default="no")
fb.text("qa_reason", "Reason for review flag", length=1000, relevant="${qa_flag}='yes'",
        required="yes", appearance="multiline")
endgrp()

if __name__ == "__main__":
    finish(fb, OUT)
