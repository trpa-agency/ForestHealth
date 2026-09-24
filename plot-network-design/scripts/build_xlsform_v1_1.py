#!/usr/bin/env python3
"""Build TRPA_ForestHealth_Plot_Survey123_v1.1.xlsx.

Extends build_xlsform.py (v1.0). Implements Forest-Health-Plot-Protocol-v1.0-DRAFT
and Plot-Data-Schema-and-Calculations.md. Every v1.0 field name is kept where the
schema defines it. Additions in v1.1:

  - SiteID calculate (TEON convention, plot_id + '_' + visit date)
  - species from species_list.csv (media folder) with the TEON UNK pattern
  - plot-center position block: monument type, position method, receiver
    accuracy, datum and epoch, open-sky offset point
  - legacy-site block: network, legacy ID, rebar found, offset to design point
  - prism basal-area check at center (QA only, matches TEON 2026)
  - state and per-plot breakpoint kept together
  - tree: height method, top condition, TEON decadence codes (optional, live)
  - tally rule enforced by unit, DBH, and distance, TEON style nested if()
  - metric twins of the key measurements as calculates for TEON comparison
  - plot start and end time
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xlsform_common import FormBuilder, finish, STR, INT, DBL, TODAY  # noqa: E402

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/outputs/survey123"
OUT = os.path.join(OUT_DIR, "TRPA_ForestHealth_Plot_Survey123_v1.1.xlsx")

fb = FormBuilder(
    form_title="TRPA Forest Health Plot v1.1",
    form_id="trpa_forest_health_plot",
    instance_name='concat("Plot ", ${plot_id}, " ", format-date(${visit_date}, "%Y-%m-%d"))',
    version=TODAY,
)
row, note, grp, endgrp, rep, endrep, choices = (
    fb.row, fb.note, fb.grp, fb.endgrp, fb.rep, fb.endrep, fb.choices)

# ----------------------------------------------------------------------------
# CHOICE LISTS (v1.0 lists kept verbatim, new lists added below)
# ----------------------------------------------------------------------------
choices("yesno", [("yes", "Yes"), ("no", "No")])

choices("visit_type", [
    ("install", "Installation (first measurement)"),
    ("remeasure", "Remeasurement"),
    ("qa_blind", "QA blind remeasurement"),
    ("msim_convert", "MSIM / LTUB conversion visit"),
])

choices("plot_status", [
    ("measured", "Measured"),
    ("partial", "Partially measured"),
    ("not_sampled", "Not sampled"),
])

choices("nonsample_reason", [
    ("access_denied", "Access denied by landowner"),
    ("hazard", "Hazardous conditions"),
    ("snow", "Snow covered"),
    ("nonforest", "Nonforest condition"),
    ("cannot_locate", "Could not locate monument"),
    ("time", "Insufficient time"),
    ("other", "Other, see notes"),
])

choices("solution_type", [
    ("pp_fixed", "Post-processed fixed"),
    ("pp_float", "Post-processed float"),
    ("rtk_fixed", "RTK fixed"),
    ("rtk_float", "RTK float"),
    ("dgps", "Code differential (DGPS)"),
    ("autonomous", "Autonomous"),
])

choices("position_ref", [
    ("center", "From plot center"),
    ("offset_station", "From an offset station inside the plot"),
])

choices("forest_type", [
    ("JP", "Jeffrey Pine"),
    ("SMC", "Sierran Mixed Conifer / White Fir"),
    ("RF", "Red Fir"),
    ("LP", "Lodgepole Pine"),
    ("SA", "Subalpine Conifer"),
    ("ASP", "Aspen"),
    ("MRI", "Montane Riparian"),
    ("NONF", "Nonforest"),
])

choices("tally_unit", [
    ("primary", "Primary plot, 58.9 ft (17.95 m), trees 4.0 in to below breakpoint"),
    ("macroplot", "Large-tree macroplot, 56.4 m (185.0 ft), trees at or above breakpoint"),
])

choices("tree_status", [
    ("live", "Live"),
    ("dead_standing", "Standing dead"),
    ("dead_down", "Down dead, not tallied as CWD"),
    ("stump", "Cut stump"),
    ("missing", "Previously recorded, now missing"),
])

choices("crown_class", [
    ("D", "Dominant"),
    ("C", "Codominant"),
    ("I", "Intermediate"),
    ("O", "Overtopped"),
    ("OG", "Open grown"),
])

choices("decay_class", [
    ("1", "1 - All limbs and branches present, top intact, bark intact"),
    ("2", "2 - Few limbs, no fine branches, top may be broken"),
    ("3", "3 - Limb stubs only, top broken, some bark loss"),
    ("4", "4 - Few or no limb stubs, top broken, sapwood sloughing"),
    ("5", "5 - No evidence of branches, stump or shell, heartwood only"),
])

choices("mistletoe", [
    ("0", "0 - No infection"), ("1", "1"), ("2", "2"), ("3", "3"),
    ("4", "4"), ("5", "5"), ("6", "6 - Severe, entire crown"),
])

choices("damage_agent", [
    ("00", "00 - No damage"),
    ("10", "10 - Insect"),
    ("11", "11 - Bark beetle"),
    ("12", "12 - Defoliator"),
    ("20", "20 - Disease"),
    ("22", "22 - Root disease"),
    ("24", "24 - Stem decay / canker"),
    ("25", "25 - Dwarf mistletoe"),
    ("30", "30 - Fire"),
    ("40", "40 - Animal"),
    ("50", "50 - Weather"),
    ("60", "60 - Vegetation / suppression"),
    ("70", "70 - Unknown"),
    ("80", "80 - Human / mechanical"),
    ("90", "90 - Physical / abiotic"),
])

choices("condition", [
    ("forest", "Accessible forest land"),
    ("nonforest_meas", "Measurable nonforest"),
    ("nonforest", "Nonforest"),
    ("water", "Water"),
])

choices("disturbance", [
    ("none", "None evident"),
    ("fire_low", "Fire, low severity"),
    ("fire_mod", "Fire, moderate severity"),
    ("fire_high", "Fire, high severity"),
    ("beetle", "Bark beetle mortality"),
    ("disease", "Disease"),
    ("mech_thin", "Mechanical thinning"),
    ("mastication", "Mastication"),
    ("pile_burn", "Pile burning"),
    ("rx_fire", "Prescribed broadcast burn"),
    ("blowdown", "Windthrow"),
    ("avalanche", "Avalanche"),
])

choices("ownership", [
    ("usfs", "USDA Forest Service, LTBMU"),
    ("ca_parks", "California State Parks"),
    ("nv_parks", "Nevada State Parks"),
    ("ndf", "Nevada Division of Forestry"),
    ("ctc", "California Tahoe Conservancy"),
    ("local", "Local government"),
    ("private", "Private"),
    ("other", "Other"),
])

choices("cover_hit", [
    ("hit", "Hit"),
    ("miss", "Miss"),
])

choices("cover_stratum", [
    ("below2m", "Below 2.0 m"),
    ("2to6m", "2.0 to 6.0 m"),
    ("6to16m", "6.0 to 16.0 m"),
    ("above16m", "Above 16.0 m"),
])

choices("growth_habit", [
    ("TT", "Tally tree species"),
    ("NT", "Non-tally tree species"),
    ("SH", "Shrub, subshrub, or woody vine"),
    ("FB", "Forb"),
    ("GR", "Graminoid"),
])

choices("veg_layer", [
    ("L1", "Layer 1, 0 to 2.0 ft"),
    ("L2", "Layer 2, 2.1 to 6.0 ft"),
    ("L3", "Layer 3, 6.1 to 16.0 ft"),
    ("L4", "Layer 4, above 16 ft"),
    ("AER", "Aerial total, all layers"),
])

choices("veg_qual", [
    ("botanist", "Certified botanist on crew"),
    ("tech_woody", "Trained technician, woody species only"),
])

choices("monument_status", [
    ("found_good", "Found, in good condition"),
    ("found_damaged", "Found, damaged or displaced"),
    ("replaced", "Not found, new monument set"),
    ("new", "New installation"),
])

choices("photo_dir", [
    ("az000", "0 degrees"), ("az090", "90 degrees"),
    ("az180", "180 degrees"), ("az270", "270 degrees"),
    ("canopy", "Vertical canopy"), ("monument", "Monument"),
    ("approach", "Approach"),
])

# --- new in v1.1 --------------------------------------------------------------
choices("state", [("CA", "California"), ("NV", "Nevada")])

choices("monument_type", [
    ("rebar_cap", "Rebar with stamped aluminum cap (protocol standard)"),
    ("rebar_tag", "Rebar with wired tag, no cap"),
    ("rebar_only", "Rebar, no cap or tag"),
    ("stake_round", "Wood stake with aluminum round (TNF style)"),
    ("pin", "Pin or nail"),
    ("none", "No monument"),
])

choices("position_method", [
    ("rtk_fixed", "RTK fixed"),
    ("rtk_float", "RTK float"),
    ("ppk", "PPK (post-processed kinematic)"),
    ("static", "Static, post-processed"),
    ("dgps", "DGPS (code differential)"),
    ("autonomous", "Autonomous"),
])

choices("datum", [
    ("nad83_2011", "NAD83(2011) epoch 2010.00, UTM 10N (protocol standard)"),
    ("wgs84_g2139", "WGS84 (G2139), current epoch"),
    ("itrf2014", "ITRF2014, current epoch"),
    ("nad83_orig", "NAD83 original or unspecified realization"),
    ("other", "Other, record in datum epoch field"),
])

choices("legacy_network", [
    ("none", "None, new plot"),
    ("teon_msim", "TEON MSIM"),
    ("teon_ltub", "TEON LTUB"),
    ("ltw", "LTW"),
    ("other", "Other, see legacy ID"),
])

choices("height_method", [
    ("laser", "Laser hypsometer, measured"),
    ("clinometer", "Clinometer and tape, measured"),
    ("estimated", "Ocular estimate"),
])

choices("top_condition", [
    ("intact", "Intact live top"),
    ("dead_top", "Dead top, bole intact"),
    ("broken", "Broken or missing top"),
])

choices("decadence", [
    ("0", "0 - none"),
    ("1", "1 - conks, bracket fungi"),
    ("2", "2 - cavities > 6in (15cm) diameter"),
    ("3", "3 - broken top"),
    ("4", "4 - broken limb >12in (30cm) diameter"),
    ("5", "5 - loose bark / sloughing"),
    ("6", "6 - mistletoe"),
    ("7", "7 - dead top"),
    ("8", "8 - split top"),
    ("9", "9 - thin canopy (relative to nearby trees)"),
    ("10", "10 - light foliar color"),
    ("11", "11 - leaf necroses"),
    ("12", "12 - frass (insect debris)"),
    ("13", "13 - sap exudation"),
])

choices("prism_factor", [
    ("10", "BAF 10"), ("20", "BAF 20"), ("40", "BAF 40"),
])

# ----------------------------------------------------------------------------
# SURVEY
# ----------------------------------------------------------------------------
note("intro", "**TRPA Forest Health Plot Protocol v1.0, form v1.1**  \n"
     "Primary plot 58.9 ft (17.95 m). Large-tree macroplot 56.4 m (185.0 ft). "
     "Microplot 6.8 ft (2.07 m). Fuels and understory footprint 24.0 ft (7.32 m).  \n"
     "DBH floor 4.0 in. Breakpoint 24.0 in unless the plot record says otherwise.")

# --- A. Plot administration --------------------------------------------------
grp("plot_admin", "A. Plot administration")
fb.text("plot_id", "Plot ID", length=20, required="yes")
fb.select1("visit_type", "visit_type", "Visit type", required="yes")
fb.date("visit_date", "Visit date", required="yes", default="today()")
fb.calc("site_id", "concat(${plot_id}, '_', format-date(${visit_date}, '%Y%m%d'))",
        ftype=STR, **{"bind::esri:fieldLength": "40"})
note("site_id_note", "SiteID: ${site_id}")
fb.select1("state", "state", "State", required="yes",
           hint="Sets which FIA breakpoint convention applies. The breakpoint itself is recorded in section C.")
fb.text("crew_lead", "Crew lead", length=60, required="yes")
fb.text("crew_members", "Other crew members", length=200)
fb.datetime("plot_start_time", "Time crew arrived at plot center", required="yes",
            default="now()")
fb.select1("plot_status", "plot_status", "Plot status", required="yes")
fb.select1("nonsample_reason", "nonsample_reason", "Reason not sampled",
           length=30, relevant="${plot_status}!='measured'", required="yes")
fb.text("plot_notes", "Plot notes", length=2000, appearance="multiline")
endgrp()

# --- A2. Legacy site (new in v1.1) -------------------------------------------
grp("legacy", "A2. Legacy site")
fb.select1("legacy_network", "legacy_network", "Legacy network", required="yes",
           default="none",
           hint="MSIM and LTUB sites use 7.3 m, 17 m, and 56.4 m tiers and nest inside this design")
fb.text("legacy_id", "Legacy site ID (MSIM, LTUB, LTW, CSE)", length=40,
        hint="Leave blank for a new plot",
        relevant="${legacy_network}!='none'", required="yes")
fb.yesno("legacy_rebar_found", "Legacy rebar or monument found", required="yes",
         relevant="${legacy_network}!='none'")
fb.decimal("legacy_dist_to_design_ft",
           "Horizontal distance from found monument to design coordinate (ft)",
           relevant="${legacy_network}!='none' and ${legacy_rebar_found}='yes'",
           required="yes", constraint=". >= 0 and . <= 500",
           hint="Laser rangefinder from the found monument to the navigation point for the design coordinate. 0 if they coincide. (1 m = 3.28 ft)")
fb.decimal("legacy_az_to_design_deg",
           "Azimuth from found monument to design coordinate (degrees)",
           relevant="${legacy_network}!='none' and ${legacy_rebar_found}='yes' and ${legacy_dist_to_design_ft} > 0",
           required="yes", constraint=". >= 0 and . <= 360")
fb.text("legacy_notes", "Legacy site notes", length=500, appearance="multiline",
        relevant="${legacy_network}!='none'",
        hint="Tag numbering scheme found, condition of subplot pins, anything a TEON crew would want to know")
endgrp()

# --- B. Plot center position -------------------------------------------------
grp("position", "B. Plot center position")
note("pos_note",
     "Survey-grade GNSS on a tripod over the monument. Minimum 15 minutes "
     "static. Log raw observations and post-process. NAD83(2011) UTM 10N. "
     "Target under 1.0 m horizontal, under 0.3 m in aspen.")
fb.geopoint("nav_point", "Navigation point (device GPS)",
            hint="Rough position for navigation only, not the survey position",
            required="yes")
fb.select1("monument_type", "monument_type", "Monument type occupied", required="yes",
           hint="What the antenna is centered over. Protocol standard is rebar with a stamped aluminum cap.")
fb.text("receiver_model", "GNSS receiver make and model", length=80, required="yes")
fb.select1("position_method", "position_method", "Positioning method used in the field",
           required="yes",
           hint="Static post-processed is the protocol standard. RTK and PPK are recorded but a static file is still required.")
fb.decimal("antenna_height_m", "Antenna height (m)", required="yes",
           constraint=". > 0 and . < 3",
           constraint_message="Antenna height must be between 0 and 3 m")
fb.datetime("occ_start", "Occupation start", required="yes")
fb.datetime("occ_end", "Occupation end", required="yes")
fb.integer("occ_minutes", "Occupation length (minutes)", required="yes",
           constraint=". >= 15",
           constraint_message="Minimum occupation is 15 minutes. Reoccupy.")
fb.integer("epochs", "Number of epochs logged")
fb.decimal("pdop", "PDOP at occupation")
fb.select1("solution_type", "solution_type", "Best solution achieved in the field",
           required="yes")
fb.decimal("rcvr_horiz_acc_m", "Horizontal accuracy reported by the receiver (m)",
           required="yes", constraint=". >= 0 and . < 100",
           hint="The field estimate from the receiver screen, not the post-processed value. 1.0 m = 3.3 ft.")
fb.decimal("rcvr_vert_acc_m", "Vertical accuracy reported by the receiver (m)")
fb.select1("datum", "datum", "Datum and realization", required="yes",
           default="nad83_2011", length=20)
fb.text("datum_epoch", "Datum epoch or notes", length=40,
        hint="For example 2010.00 for NAD83(2011). Required if datum is Other.",
        relevant="${datum}='other'", required="yes")
fb.yesno("raw_logged", "Raw observations logged for post-processing", required="yes",
         constraint=".='yes'",
         constraint_message="Raw logging is mandatory. Restart the occupation.")
fb.text("raw_file", "Raw observation file name", length=120, required="yes")
fb.yesno("offset_used", "Offset used", required="yes", default="no",
         hint="Only where canopy defeats reception entirely or a hazard prevents tripod setup")
fb.geopoint("offset_point", "Open-sky point occupied (device GPS)",
            relevant="${offset_used}='yes'",
            hint="The GNSS antenna sat here, not on the monument")
fb.decimal("offset_azimuth", "Offset azimuth from open-sky point to monument (degrees)",
           relevant="${offset_used}='yes'", required="yes",
           constraint=". >= 0 and . <= 360",
           constraint_message="Azimuth must be 0 to 360")
fb.decimal("offset_distance_ft", "Offset horizontal distance from open-sky point to monument (ft)",
           relevant="${offset_used}='yes'", required="yes",
           constraint=". > 0 and . <= 300",
           hint="Laser rangefinder, nearest 0.1 ft. One leg only; a traverse of more than two legs is not acceptable.")
fb.text("offset_reason", "Reason for offset", length=200,
        relevant="${offset_used}='yes'", required="yes")
note("pp_note", "Fields below are completed in the office after post-processing.")
fb.text("pp_software", "Post-processing software", length=80)
fb.text("pp_base", "Base station or network used", length=80)
fb.decimal("horiz_acc_m", "Final horizontal accuracy (m)")
fb.decimal("vert_acc_m", "Final vertical accuracy (m)")
fb.decimal("final_easting", "Final easting (UTM 10N, m)")
fb.decimal("final_northing", "Final northing (UTM 10N, m)")
endgrp()

# --- C. Site and condition ---------------------------------------------------
grp("site", "C. Site and condition")
fb.select1("condition", "condition", "Condition class", required="yes")
fb.select1("forest_type", "forest_type", "Forest type (CWHR crosswalk)",
           required="yes", length=10)
fb.yesno("aspen_flag", "Aspen present as a stand component", required="yes",
         default="no", hint="Aspen plots require sub-meter positioning without exception")
fb.decimal("breakpoint_dia_in", "Macroplot breakpoint diameter (in)", required="yes",
           default="24.0", constraint=". = 24.0 or . = 21.0",
           constraint_message="Breakpoint is 24.0 (California FIA) or 21.0 (Interior West FIA). Do not enter any other value.",
           hint="Recorded per plot, not assumed. Protocol v1.0 selects 24.0 in for both states pending confirmation for Nevada (21.0 in Interior West). Do not change without direction.")
fb.calc("breakpoint_dia_cm", "round(${breakpoint_dia_in} * 2.54, 1)")
fb.decimal("elevation_ft", "Elevation (ft)")
fb.integer("slope_pct", "Slope (percent)", required="yes",
           constraint=". >= 0 and . <= 200",
           constraint_message="Slope must be 0 to 200 percent",
           hint="Used for the fuels slope correction, c = 1 + (slope/100) squared")
fb.integer("aspect_deg", "Aspect (degrees)", constraint=". >= 0 and . <= 360")
fb.selectm("disturbance", "disturbance", "Disturbance and treatment evidence",
           required="yes")
fb.integer("disturbance_year", "Estimated year of most recent disturbance",
           relevant="not(selected(${disturbance},'none'))")
fb.select1("ownership", "ownership", "Ownership", required="yes")
note("prism_note", "**Prism basal-area check at plot center (QA only).** "
     "Same two fields as the TEON 2026 tree form so the two networks can be "
     "compared. Not a tally unit under this protocol; the fixed-radius tally "
     "is the measurement.")
fb.select1("prism_factor", "prism_factor", "Prism factor (BAF, sq ft per acre)",
           length=5, hint="TEON uses an integer BAF. Sweep from plot center.")
fb.integer("prism_trees_in", "Trees 'in' prism (live and dead)",
           relevant="${prism_factor}!=''", required="yes", constraint=". >= 0 and . <= 60")
fb.calc("prism_ba_sqft_ac", "if(${prism_factor}!='', number(${prism_factor}) * ${prism_trees_in}, '')")
endgrp()

# --- D. Trees ----------------------------------------------------------------
note("tree_note",
     "**D. Trees.** Primary plot 58.9 ft (17.95 m): all live trees and snags 4.0 in DBH "
     "and larger, below the breakpoint. Macroplot 56.4 m (185.0 ft): all trees at or "
     "above the breakpoint, including those inside the primary plot. "
     "Do not tally a breakpoint tree twice.")
rep("tree", "Tree")
fb.integer("tree_tag", "Tag number", required="yes")
fb.select1("tally_unit", "tally_unit", "Tally unit", required="yes")
fb.species("species", "Species (PLANTS symbol)")
fb.unk_species("species", "species_unk")
fb.select1("tree_status", "tree_status", "Status", required="yes")
fb.decimal("dbh_in", "DBH (in, to 0.1, round down)", required="yes",
           constraint="if(${tally_unit}='primary', . >= 4.0 and . < ${breakpoint_dia_in}, "
                      "if(${tally_unit}='macroplot', . >= ${breakpoint_dia_in} and . <= 120, false()))",
           constraint_message="Primary plot takes 4.0 in up to but not including the breakpoint. Macroplot takes the breakpoint and larger. Saplings go in the microplot repeat.",
           hint="4.0 in = 10.2 cm. Measured at 4.5 ft on the uphill side.")
fb.calc("dbh_cm", "round(${dbh_in} * 2.54, 1)")
fb.decimal("dbh_height_ft", "Height of diameter measurement (ft)", default="4.5",
           constraint=". > 0 and . < 30")
fb.decimal("total_height_ft", "Total height (ft)", required="yes",
           constraint=". > 0 and . < 400",
           hint="Laser hypsometer. Tolerance 5 percent under 60 ft, 10 percent above. Include a dead top.")
fb.calc("total_height_m", "round(${total_height_ft} * 0.3048, 1)")
fb.select1("height_method", "height_method", "Height method", required="yes",
           default="laser",
           hint="Protocol requires a laser hypsometer. Record an estimate only where sighting was impossible and say why in notes.")
fb.select1("top_condition", "top_condition", "Top condition", required="yes",
           default="intact", relevant="${tree_status}='live'",
           hint="Dead or broken top: total height still includes the dead top; note height to the live top in tree notes.")
fb.decimal("crown_base_ht_ft", "Height to live crown base (ft)",
           relevant="${tree_status}='live'",
           constraint=". >= 0 and . < ${total_height_ft}",
           constraint_message="Crown base must be below total height",
           hint="Added variable. Lowest live branch whorl, not compacted.")
fb.calc("crown_base_ht_m", "round(${crown_base_ht_ft} * 0.3048, 1)")
fb.integer("crown_ratio_pct", "Compacted crown ratio (percent)",
           relevant="${tree_status}='live'", constraint=". >= 0 and . <= 99")
fb.select1("crown_class", "crown_class", "Crown class", length=5,
           relevant="${tree_status}='live'", required="yes")
fb.decimal("crown_width_long_ft", "Crown width, long axis (ft)",
           relevant="${tree_status}='live'", required="yes",
           constraint=". >= 0 and . <= 150",
           hint="Added variable. Widest point of the natural spread, not compacted. Needed for the crown cover reconciliation.")
fb.decimal("crown_width_perp_ft", "Crown width, axis at 90 degrees (ft)",
           relevant="${tree_status}='live'", required="yes",
           constraint=". >= 0 and . <= 150")
fb.select1("damage_agent", "damage1", "Damage agent 1", length=5)
fb.select1("damage_agent", "damage2", "Damage agent 2", length=5)
fb.select1("damage_agent", "damage3", "Damage agent 3", length=5)
fb.select1("mistletoe", "mistletoe", "Dwarf mistletoe rating (Hawksworth)", length=5,
           relevant="${tree_status}='live'",
           hint="Required on live conifers except juniper and incense cedar")
fb.selectm("decadence", "decadence", "Decadence features (TEON codes, optional)",
           relevant="${tree_status}='live'",
           hint="Same 0 to 13 list as the TEON tree form. Fill on converted TEON sites so the two records read the same.")
fb.select1("decay_class", "decay_class", "Decay class", length=5,
           relevant="${tree_status}='dead_standing'", required="yes",
           appearance="likert")
note("pos_tree_note",
     "Stem position. Azimuth tolerance is 2 degrees, not the FIA 10 degrees. "
     "Use a declination-corrected compass and a laser rangefinder.")
fb.select1("position_ref", "position_ref", "Position measured from", default="center")
fb.decimal("azimuth_deg", "Azimuth from plot center (degrees)", required="yes",
           constraint=". >= 0 and . <= 360")
fb.decimal("distance_ft", "Horizontal distance from plot center (ft)", required="yes",
           constraint="if(${tally_unit}='primary', . > 0 and . <= 58.9, . > 0 and . <= 185.1)",
           constraint_message="Primary plot trees must be within 58.9 ft. Distance cannot exceed the 185.0 ft macroplot radius. A breakpoint tree inside 58.9 ft is still a macroplot tree.",
           hint="To bole center at ground level, nearest 0.1 ft. 58.9 ft = 17.95 m, 185.0 ft = 56.4 m.")
fb.calc("distance_m", "round(${distance_ft} * 0.3048, 2)")
fb.text("tree_notes", "Tree notes", length=500, appearance="multiline")
endrep()

# --- E. Saplings and seedlings ----------------------------------------------
note("micro_note", "**E. Microplot, 6.8 ft (2.07 m) radius.** Saplings 1.0 to 3.9 in DBH "
     "measured individually. Seedlings under 1.0 in counted by species.")
rep("sapling", "Sapling (1.0 to 3.9 in DBH)")
fb.species("sap_species", "Species (PLANTS symbol)")
fb.unk_species("sap_species", "sap_species_unk")
fb.select1("tree_status", "sap_status", "Status", required="yes")
fb.decimal("sap_dbh_in", "DBH (in)", required="yes",
           constraint=". >= 1.0 and . < 4.0",
           constraint_message="Saplings are 1.0 to 3.9 in. Trees 4.0 in and larger go in the tree repeat.",
           hint="1.0 in = 2.5 cm, 4.0 in = 10.2 cm")
fb.decimal("sap_height_ft", "Total height (ft)", constraint=". > 0 and . < 100")
endrep()

rep("seedling", "Seedling count by species (under 1.0 in DBH)")
fb.species("seed_species", "Species (PLANTS symbol)")
fb.unk_species("seed_species", "seed_species_unk")
fb.integer("seed_count", "Count", required="yes", constraint=". > 0",
           hint="Conifers 0.5 ft length or more, hardwoods 1.0 ft or more")
endrep()

# --- F. Canopy cover point intercept ----------------------------------------
note("cover_note",
     "**F. Canopy cover, 100 vertical point intercepts.** 25 points on each of "
     "four transects, every 2 ft from 3.0 to 51.0 ft. Moosehorn or vertical "
     "densitometer. Record BOTH determinations at every point: crown cover "
     "counts within-crown gaps as cover, effective cover does not. The "
     "difference between them is a deliverable.")
rep("cover_pt", "Canopy point", repeat_count="100")
fb.calc("pt_index", "position(..)", ftype=INT)
fb.calc("pt_transect", "int((${pt_index} - 1) div 25) + 1", ftype=INT)
fb.calc("pt_azimuth", "(${pt_transect} - 1) * 90", ftype=INT)
fb.calc("pt_distance_ft", "3.0 + (((${pt_index} - 1) mod 25) * 2.0)")
note("pt_label", "Transect ${pt_azimuth} degrees, ${pt_distance_ft} ft from center")
fb.select1("cover_hit", "crown_cover_hit", "Crown cover (within-crown gaps count as cover)",
           length=5, required="yes", appearance="horizontal-compact")
fb.select1("cover_hit", "effective_cover_hit", "Effective cover (foliage or wood actually intercepted)",
           length=5, required="yes", appearance="horizontal-compact")
fb.select1("cover_stratum", "cover_stratum", "Height stratum of the intercepting material",
           relevant="${crown_cover_hit}='hit' or ${effective_cover_hit}='hit'",
           required="yes")
endrep()

# --- G. Fuels transects ------------------------------------------------------
note("fuel_note",
     "**G. Fuels.** Four transects from plot center at 0, 90, 180, 270 degrees, "
     "each 58.9 ft (17.95 m) horizontal. Azimuth tolerance 2 degrees. Slope correction "
     "uses c = 1 + (percent slope / 100) squared.")
rep("transect", "Fuels transect", repeat_count="4")
fb.calc("tr_index", "position(..)", ftype=INT)
fb.calc("tr_azimuth", "(${tr_index} - 1) * 90", ftype=INT)
note("tr_label", "Transect at ${tr_azimuth} degrees")
fb.integer("fwd_small_count", "Small FWD count, 0 to 0.24 in (1 hr), 14 to 20 ft",
           required="yes", constraint=". >= 0",
           hint="0 to 0.6 cm. Segment 4.3 to 6.1 m. Not counted above 6 ft off the ground.")
fb.integer("fwd_medium_count", "Medium FWD count, 0.25 to 0.9 in (10 hr), 14 to 20 ft",
           required="yes", constraint=". >= 0", hint="0.6 to 2.5 cm")
fb.integer("fwd_large_count", "Large FWD count, 1.0 to 2.9 in (100 hr), 14 to 24 ft",
           required="yes", constraint=". >= 0", hint="2.5 to 7.6 cm. Segment 4.3 to 7.3 m.")
fb.decimal("duff_20ft", "Duff depth at 20 ft (in)", required="yes",
           constraint=". >= 0 and . <= 24", hint="Nearest 0.1 in")
fb.decimal("litter_20ft", "Litter depth at 20 ft (in)", required="yes",
           constraint=". >= 0 and . <= 99.9")
fb.decimal("duff_50ft", "Duff depth at 50 ft (in)", required="yes",
           constraint=". >= 0 and . <= 24")
fb.decimal("litter_50ft", "Litter depth at 50 ft (in)", required="yes",
           constraint=". >= 0 and . <= 99.9",
           hint="Where a log, rock, or pile occupies the point, record litter above and below it and estimate duff from the surroundings")

rep("cwd", "CWD piece on this transect")
fb.decimal("cwd_slope_dist_ft", "Slope distance along transect (ft)", required="yes",
           constraint=". > 0 and . <= 58.9")
fb.species("cwd_species", "Species (PLANTS symbol or UNK code)", required="")
fb.unk_species("cwd_species", "cwd_species_unk")
fb.decimal("cwd_dia_in", "Diameter at point of intersection (in)", required="yes",
           constraint=". >= 3.0",
           constraint_message="CWD is 3.0 in or larger at the intersection",
           hint="3.0 in = 7.6 cm")
fb.decimal("cwd_hollow_dia_in", "Diameter of hollow at intersection (in)", default="0",
           constraint=". >= 0 and . < ${cwd_dia_in}")
fb.select1("decay_class", "cwd_decay", "Decay class", length=5, required="yes",
           appearance="likert")
fb.decimal("cwd_length_ft", "Total piece length (ft)", required="yes",
           constraint=". >= 0.5",
           hint="Recorded on every piece so either the 0.5 ft or 3 ft rule can be applied later")
fb.integer("cwd_inclination_deg", "Inclination (degrees)",
           constraint=". >= 0 and . <= 90")
fb.integer("cwd_charred_pct", "Percent of piece charred by fire", required="yes",
           constraint=". >= 0 and . <= 100",
           hint="Required under this protocol. Core Optional in FIA.")
endrep()
endrep()

# --- H. Understory, Tier 3 ---------------------------------------------------
note("veg_note",
     "**H. Understory composition, Tier 3.** Collected on scoped plots only. "
     "24.0 ft (7.32 m) subplot footprint. Daubenmire cover convention, nearest 1 percent.")
fb.yesno("tier3_collected", "Tier 3 understory collected on this plot", required="yes",
         default="no")
grp("veg", "H. Understory composition")
fb.select1("veg_qual", "veg_qualification", "Crew qualification for this tier",
           required="yes", relevant="${tier3_collected}='yes'")
fb.yesno("fully_leafed", "Species fully leafed out", required="yes",
         relevant="${tier3_collected}='yes'")
endgrp()

rep("veg_cover", "Cover by growth habit and layer")
fb.select1("growth_habit", "gh", "Growth habit", length=5, required="yes")
fb.select1("veg_layer", "layer", "Height layer", length=5, required="yes")
fb.integer("cover_pct", "Aerial canopy cover (percent)", required="yes",
           constraint=". >= 0 and . <= 100",
           hint="Nearest 1 percent. Cover above 0 and at or below 1 is recorded as 1.")
endrep()

rep("veg_species", "Species with 3 percent cover or more")
fb.species("vs_species", "Species (PLANTS symbol)", woody_only=False)
fb.unk_species("vs_species", "vs_species_unk")
fb.integer("vs_cover_pct", "Total aerial cover (percent)", required="yes",
           constraint=". >= 3 and . <= 100",
           constraint_message="Only species at 3 percent or more are recorded. Do not round up to reach 3.")
endrep()

# --- I. Monumentation and relocation ----------------------------------------
grp("monument", "I. Monumentation")
fb.select1("monument_status", "monument_status", "Monument status", required="yes")
fb.text("monument_stamp", "Cap stamping", length=40,
        hint="Rebar with aluminum cap stamped with the plot ID, flush or slightly proud, ferrous element for a metal locator")
fb.text("access_narrative", "Access route narrative", length=2000,
        appearance="multiline", required="yes")
fb.geopoint("park_point", "Parking or approach point")
fb.text("gate_road_status", "Gate and road status", length=500)
fb.text("permission_ref", "Landowner permission reference", length=200)
fb.text("hazards", "Hazards", length=500, appearance="multiline")
fb.integer("travel_minutes", "Travel time from maintained road (minutes)")
endgrp()

rep("witness", "Witness tree", repeat_count="3")
fb.species("wt_species", "Species (PLANTS symbol)")
fb.decimal("wt_dbh_in", "DBH (in)", required="yes", constraint=". > 0 and . <= 120")
fb.decimal("wt_azimuth", "Azimuth to plot center (degrees)", required="yes",
           constraint=". >= 0 and . <= 360",
           hint="From the tag nail back to the monument, as on the TEON and TNF forms")
fb.decimal("wt_distance_ft", "Horizontal distance (ft)", required="yes",
           constraint=". > 0 and . <= 200")
fb.integer("wt_tag", "Tag number",
           hint="Tag nailed facing plot center. Choose for durability, not proximity.")
endrep()

rep("photo", "Photograph", repeat_count="7")
fb.select1("photo_dir", "photo_direction", "Photo type", required="yes",
           hint="Four cardinal from center, one vertical canopy, one monument, one approach with a landmark. All geotagged.")
fb.image("photo_file", "Photograph", required="yes", appearance="annotate")
endrep()

# --- J. Closeout -------------------------------------------------------------
grp("closeout", "J. Closeout")
fb.datetime("plot_end_time", "Time crew left plot center", required="yes")
fb.integer("crew_minutes_on_plot", "Crew minutes on plot", required="yes",
           constraint=". > 0 and . <= 1440",
           hint="Arrival to departure at plot center, travel excluded. Used to calibrate future cost estimates. Do not skip.")
fb.yesno("qa_flag", "Flag this plot for TRPA review", default="no")
fb.text("qa_reason", "Reason for review flag", length=1000,
        relevant="${qa_flag}='yes'", required="yes", appearance="multiline")
endgrp()

if __name__ == "__main__":
    finish(fb, OUT)
