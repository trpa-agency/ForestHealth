#!/usr/bin/env python3
"""Build the TRPA Forest Health Plot Survey123 XLSForm workbook."""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

SURVEY_COLS = [
    "type", "name", "label", "hint", "required", "readonly", "relevant",
    "constraint", "constraint_message", "calculation", "default", "appearance",
    "repeat_count", "bind::esri:fieldType", "bind::esri:fieldLength",
    "body::esri:style", "parameters",
]
CHOICES_COLS = ["list_name", "name", "label"]
SETTINGS_COLS = ["form_title", "form_id", "version", "instance_name",
                 "submission_url", "style"]

S = []          # survey rows (dicts)
C = []          # choices rows (tuples)


def row(**kw):
    r = {c: "" for c in SURVEY_COLS}
    r.update(kw)
    S.append(r)


def note(name, label):
    row(type="note", name=name, label=label)


def grp(name, label, appearance="field-list"):
    row(type="begin group", name=name, label=label, appearance=appearance)


def endgrp():
    row(type="end group", name="", label="")


def rep(name, label, repeat_count=""):
    row(type="begin repeat", name=name, label=label, repeat_count=repeat_count)


def endrep():
    row(type="end repeat", name="", label="")


def choices(list_name, pairs):
    for n, l in pairs:
        C.append((list_name, n, l))


# ----------------------------------------------------------------------------
# CHOICE LISTS
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
    ("primary", "Primary plot, 58.9 ft, trees 4.0 in to below breakpoint"),
    ("macroplot", "Large-tree macroplot, 56.4 m, trees at or above breakpoint"),
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

# ----------------------------------------------------------------------------
# SURVEY
# ----------------------------------------------------------------------------
note("intro", "**TRPA Forest Health Plot Protocol v1.0**  \n"
     "Primary plot 58.9 ft. Large-tree macroplot 56.4 m. Microplot 6.8 ft.  \n"
     "DBH floor 4.0 in. Breakpoint 24.0 in unless the plot record says otherwise.")

# --- A. Plot administration --------------------------------------------------
grp("plot_admin", "A. Plot administration")
row(type="text", name="plot_id", label="Plot ID", required="yes",
    appearance="", **{"bind::esri:fieldType": "esriFieldTypeString",
                      "bind::esri:fieldLength": "20"})
row(type="select_one visit_type", name="visit_type", label="Visit type",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeString",
                       "bind::esri:fieldLength": "20"})
row(type="text", name="legacy_id", label="Legacy site ID (MSIM, LTUB, LTW, CSE)",
    hint="Leave blank for a new plot",
    relevant="${visit_type}='msim_convert' or ${visit_type}='remeasure'",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "40"})
row(type="date", name="visit_date", label="Visit date", required="yes",
    default="today()", **{"bind::esri:fieldType": "esriFieldTypeDate"})
row(type="text", name="crew_lead", label="Crew lead", required="yes",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "60"})
row(type="text", name="crew_members", label="Other crew members",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "200"})
row(type="select_one plot_status", name="plot_status", label="Plot status",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeString",
                       "bind::esri:fieldLength": "20"})
row(type="select_one nonsample_reason", name="nonsample_reason",
    label="Reason not sampled", relevant="${plot_status}!='measured'",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeString",
                       "bind::esri:fieldLength": "30"})
row(type="text", name="plot_notes", label="Plot notes", appearance="multiline",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "2000"})
endgrp()

# --- B. Plot center position -------------------------------------------------
grp("position", "B. Plot center position")
note("pos_note",
     "Survey-grade GNSS on a tripod over the monument. Minimum 15 minutes "
     "static. Log raw observations and post-process. NAD83(2011) UTM 10N. "
     "Target under 1.0 m horizontal, under 0.3 m in aspen.")
row(type="geopoint", name="nav_point", label="Navigation point (device GPS)",
    hint="Rough position for navigation only, not the survey position",
    required="yes")
row(type="text", name="receiver_model", label="GNSS receiver make and model",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeString",
                       "bind::esri:fieldLength": "80"})
row(type="decimal", name="antenna_height_m", label="Antenna height (m)",
    required="yes", constraint=". > 0 and . < 3",
    constraint_message="Antenna height must be between 0 and 3 m",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="dateTime", name="occ_start", label="Occupation start", required="yes",
    **{"bind::esri:fieldType": "esriFieldTypeDate"})
row(type="dateTime", name="occ_end", label="Occupation end", required="yes",
    **{"bind::esri:fieldType": "esriFieldTypeDate"})
row(type="integer", name="occ_minutes", label="Occupation length (minutes)",
    required="yes", constraint=". >= 15",
    constraint_message="Minimum occupation is 15 minutes. Reoccupy.",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
row(type="integer", name="epochs", label="Number of epochs logged",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
row(type="decimal", name="pdop", label="PDOP at occupation",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="select_one solution_type", name="solution_type",
    label="Best solution achieved in the field", required="yes",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "20"})
row(type="select_one yesno", name="raw_logged",
    label="Raw observations logged for post-processing", required="yes",
    constraint=".='yes'",
    constraint_message="Raw logging is mandatory. Restart the occupation.",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "5"})
row(type="text", name="raw_file", label="Raw observation file name",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeString",
                       "bind::esri:fieldLength": "120"})
row(type="select_one yesno", name="offset_used", label="Offset used",
    required="yes", default="no",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "5"})
row(type="decimal", name="offset_azimuth",
    label="Offset azimuth to monument (degrees)",
    relevant="${offset_used}='yes'", required="yes",
    constraint=". >= 0 and . <= 360",
    constraint_message="Azimuth must be 0 to 360",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="decimal", name="offset_distance_ft",
    label="Offset horizontal distance to monument (ft)",
    relevant="${offset_used}='yes'", required="yes",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="text", name="offset_reason", label="Reason for offset",
    relevant="${offset_used}='yes'", required="yes",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "200"})
note("pp_note", "Fields below are completed in the office after post-processing.")
row(type="text", name="pp_software", label="Post-processing software",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "80"})
row(type="text", name="pp_base", label="Base station or network used",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "80"})
row(type="decimal", name="horiz_acc_m", label="Final horizontal accuracy (m)",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="decimal", name="vert_acc_m", label="Final vertical accuracy (m)",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="decimal", name="final_easting", label="Final easting (UTM 10N, m)",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="decimal", name="final_northing", label="Final northing (UTM 10N, m)",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
endgrp()

# --- C. Site and condition ---------------------------------------------------
grp("site", "C. Site and condition")
row(type="select_one condition", name="condition", label="Condition class",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeString",
                       "bind::esri:fieldLength": "20"})
row(type="select_one forest_type", name="forest_type",
    label="Forest type (CWHR crosswalk)", required="yes",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "10"})
row(type="select_one yesno", name="aspen_flag",
    label="Aspen present as a stand component", required="yes", default="no",
    hint="Aspen plots require sub-meter positioning without exception",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "5"})
row(type="decimal", name="breakpoint_dia_in",
    label="Macroplot breakpoint diameter (in)", required="yes", default="24.0",
    hint="Recorded per plot, not assumed. Do not change without direction.",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="decimal", name="elevation_ft", label="Elevation (ft)",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="integer", name="slope_pct", label="Slope (percent)", required="yes",
    constraint=". >= 0 and . <= 200",
    constraint_message="Slope must be 0 to 200 percent",
    hint="Used for the fuels slope correction",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
row(type="integer", name="aspect_deg", label="Aspect (degrees)",
    constraint=". >= 0 and . <= 360",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
row(type="select_multiple disturbance", name="disturbance",
    label="Disturbance and treatment evidence", required="yes",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "200"})
row(type="integer", name="disturbance_year",
    label="Estimated year of most recent disturbance",
    relevant="not(selected(${disturbance},'none'))",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
row(type="select_one ownership", name="ownership", label="Ownership",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeString",
                       "bind::esri:fieldLength": "20"})
endgrp()

# --- D. Trees ----------------------------------------------------------------
note("tree_note",
     "**D. Trees.** Primary plot 58.9 ft: all live trees and snags 4.0 in DBH "
     "and larger, below the breakpoint. Macroplot 56.4 m: all trees at or "
     "above the breakpoint, including those inside the primary plot. "
     "Do not tally a breakpoint tree twice.")
rep("tree", "Tree")
row(type="integer", name="tree_tag", label="Tag number", required="yes",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
row(type="select_one tally_unit", name="tally_unit", label="Tally unit",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeString",
                       "bind::esri:fieldLength": "20"})
row(type="text", name="species", label="Species (PLANTS symbol)", required="yes",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "10"})
row(type="select_one tree_status", name="tree_status", label="Status",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeString",
                       "bind::esri:fieldLength": "20"})
row(type="decimal", name="dbh_in", label="DBH (in, to 0.1, round down)",
    required="yes", constraint=". >= 4.0 and . <= 120",
    constraint_message="DBH floor is 4.0 in on the tree repeat. Saplings go in the microplot repeat.",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="decimal", name="dbh_height_ft",
    label="Height of diameter measurement (ft)", default="4.5",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="decimal", name="total_height_ft", label="Total height (ft)",
    required="yes", constraint=". > 0 and . < 400",
    hint="Laser hypsometer. Tolerance 5 percent under 60 ft, 10 percent above.",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="decimal", name="crown_base_ht_ft", label="Height to live crown base (ft)",
    relevant="${tree_status}='live'",
    constraint=". >= 0 and . < ${total_height_ft}",
    constraint_message="Crown base must be below total height",
    hint="Added variable. Lowest live branch whorl, not compacted.",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="integer", name="crown_ratio_pct", label="Compacted crown ratio (percent)",
    relevant="${tree_status}='live'", constraint=". >= 0 and . <= 99",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
row(type="select_one crown_class", name="crown_class", label="Crown class",
    relevant="${tree_status}='live'",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "5"})
row(type="decimal", name="crown_width_long_ft",
    label="Crown width, long axis (ft)", relevant="${tree_status}='live'",
    hint="Added variable. Needed for the crown cover reconciliation.",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="decimal", name="crown_width_perp_ft",
    label="Crown width, axis at 90 degrees (ft)",
    relevant="${tree_status}='live'",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="select_one damage_agent", name="damage1", label="Damage agent 1",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "5"})
row(type="select_one damage_agent", name="damage2", label="Damage agent 2",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "5"})
row(type="select_one damage_agent", name="damage3", label="Damage agent 3",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "5"})
row(type="select_one mistletoe", name="mistletoe",
    label="Dwarf mistletoe rating (Hawksworth)",
    relevant="${tree_status}='live'",
    hint="Required on live conifers except juniper and incense cedar",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "5"})
row(type="select_one decay_class", name="decay_class", label="Decay class",
    relevant="${tree_status}='dead_standing'", required="yes",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "5"})
note("pos_tree_note",
     "Stem position. Azimuth tolerance is 2 degrees, not the FIA 10 degrees. "
     "Use a declination-corrected compass and a laser rangefinder.")
row(type="select_one position_ref", name="position_ref",
    label="Position measured from", default="center",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "20"})
row(type="decimal", name="azimuth_deg", label="Azimuth from plot center (degrees)",
    required="yes", constraint=". >= 0 and . <= 360",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="decimal", name="distance_ft",
    label="Horizontal distance from plot center (ft)", required="yes",
    constraint=". > 0 and . <= 185.1",
    constraint_message="Distance cannot exceed the 185.0 ft macroplot radius",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="text", name="tree_notes", label="Tree notes", appearance="multiline",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "500"})
endrep()

# --- E. Saplings and seedlings ----------------------------------------------
note("micro_note", "**E. Microplot, 6.8 ft radius.** Saplings 1.0 to 3.9 in DBH "
     "measured individually. Seedlings under 1.0 in counted by species.")
rep("sapling", "Sapling (1.0 to 3.9 in DBH)")
row(type="text", name="sap_species", label="Species (PLANTS symbol)",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeString",
                       "bind::esri:fieldLength": "10"})
row(type="select_one tree_status", name="sap_status", label="Status",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeString",
                       "bind::esri:fieldLength": "20"})
row(type="decimal", name="sap_dbh_in", label="DBH (in)", required="yes",
    constraint=". >= 1.0 and . < 4.0",
    constraint_message="Saplings are 1.0 to 3.9 in. Trees 4.0 in and larger go in the tree repeat.",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="decimal", name="sap_height_ft", label="Total height (ft)",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
endrep()

rep("seedling", "Seedling count by species (under 1.0 in DBH)")
row(type="text", name="seed_species", label="Species (PLANTS symbol)",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeString",
                       "bind::esri:fieldLength": "10"})
row(type="integer", name="seed_count", label="Count", required="yes",
    constraint=". > 0",
    hint="Conifers 0.5 ft length or more, hardwoods 1.0 ft or more",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
endrep()

# --- F. Canopy cover point intercept ----------------------------------------
note("cover_note",
     "**F. Canopy cover, 100 vertical point intercepts.** 25 points on each of "
     "four transects, every 2 ft from 3.0 to 51.0 ft. Moosehorn or vertical "
     "densitometer. Record BOTH determinations at every point: crown cover "
     "counts within-crown gaps as cover, effective cover does not. The "
     "difference between them is a deliverable.")
rep("cover_pt", "Canopy point", repeat_count="100")
row(type="calculate", name="pt_index", calculation="position(..)",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
row(type="calculate", name="pt_transect",
    calculation="int((${pt_index} - 1) div 25) + 1",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
row(type="calculate", name="pt_azimuth",
    calculation="(${pt_transect} - 1) * 90",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
row(type="calculate", name="pt_distance_ft",
    calculation="3.0 + (((${pt_index} - 1) mod 25) * 2.0)",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
note("pt_label", "Transect ${pt_azimuth} degrees, ${pt_distance_ft} ft from center")
row(type="select_one cover_hit", name="crown_cover_hit",
    label="Crown cover (within-crown gaps count as cover)", required="yes",
    appearance="horizontal-compact",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "5"})
row(type="select_one cover_hit", name="effective_cover_hit",
    label="Effective cover (foliage or wood actually intercepted)",
    required="yes", appearance="horizontal-compact",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "5"})
row(type="select_one cover_stratum", name="cover_stratum",
    label="Height stratum of the intercepting material",
    relevant="${crown_cover_hit}='hit' or ${effective_cover_hit}='hit'",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeString",
                       "bind::esri:fieldLength": "20"})
endrep()

# --- G. Fuels transects ------------------------------------------------------
note("fuel_note",
     "**G. Fuels.** Four transects from plot center at 0, 90, 180, 270 degrees, "
     "each 58.9 ft horizontal. Azimuth tolerance 2 degrees. Slope correction "
     "uses c = 1 + (percent slope / 100) squared.")
rep("transect", "Fuels transect", repeat_count="4")
row(type="calculate", name="tr_index", calculation="position(..)",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
row(type="calculate", name="tr_azimuth", calculation="(${tr_index} - 1) * 90",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
note("tr_label", "Transect at ${tr_azimuth} degrees")
row(type="integer", name="fwd_small_count",
    label="Small FWD count, 0 to 0.24 in (1 hr), 14 to 20 ft",
    required="yes", constraint=". >= 0",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
row(type="integer", name="fwd_medium_count",
    label="Medium FWD count, 0.25 to 0.9 in (10 hr), 14 to 20 ft",
    required="yes", constraint=". >= 0",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
row(type="integer", name="fwd_large_count",
    label="Large FWD count, 1.0 to 2.9 in (100 hr), 14 to 24 ft",
    required="yes", constraint=". >= 0",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
row(type="decimal", name="duff_20ft", label="Duff depth at 20 ft (in)",
    required="yes", constraint=". >= 0 and . <= 24",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="decimal", name="litter_20ft", label="Litter depth at 20 ft (in)",
    required="yes", constraint=". >= 0 and . <= 99.9",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="decimal", name="duff_50ft", label="Duff depth at 50 ft (in)",
    required="yes", constraint=". >= 0 and . <= 24",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="decimal", name="litter_50ft", label="Litter depth at 50 ft (in)",
    required="yes", constraint=". >= 0 and . <= 99.9",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})

rep("cwd", "CWD piece on this transect")
row(type="decimal", name="cwd_slope_dist_ft",
    label="Slope distance along transect (ft)", required="yes",
    constraint=". > 0 and . <= 58.9",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="text", name="cwd_species", label="Species (PLANTS symbol or UNKN)",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "10"})
row(type="decimal", name="cwd_dia_in",
    label="Diameter at point of intersection (in)", required="yes",
    constraint=". >= 3.0",
    constraint_message="CWD is 3.0 in or larger at the intersection",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="decimal", name="cwd_hollow_dia_in",
    label="Diameter of hollow at intersection (in)", default="0",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="select_one decay_class", name="cwd_decay", label="Decay class",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeString",
                       "bind::esri:fieldLength": "5"})
row(type="decimal", name="cwd_length_ft", label="Total piece length (ft)",
    required="yes", constraint=". >= 0.5",
    hint="Recorded on every piece so either the 0.5 ft or 3 ft rule can be applied later",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="integer", name="cwd_inclination_deg", label="Inclination (degrees)",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
row(type="integer", name="cwd_charred_pct",
    label="Percent of piece charred by fire", required="yes",
    constraint=". >= 0 and . <= 100",
    hint="Required under this protocol. Core Optional in FIA.",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
endrep()
endrep()

# --- H. Understory, Tier 3 ---------------------------------------------------
note("veg_note",
     "**H. Understory composition, Tier 3.** Collected on scoped plots only. "
     "24.0 ft subplot footprint. Daubenmire cover convention, nearest 1 percent.")
row(type="select_one yesno", name="tier3_collected",
    label="Tier 3 understory collected on this plot", required="yes",
    default="no", **{"bind::esri:fieldType": "esriFieldTypeString",
                     "bind::esri:fieldLength": "5"})
grp("veg", "H. Understory composition")
row(type="select_one veg_qual", name="veg_qualification",
    label="Crew qualification for this tier", required="yes",
    relevant="${tier3_collected}='yes'",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "20"})
row(type="select_one yesno", name="fully_leafed",
    label="Species fully leafed out", required="yes",
    relevant="${tier3_collected}='yes'",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "5"})
endgrp()

rep("veg_cover", "Cover by growth habit and layer")
row(type="select_one growth_habit", name="gh", label="Growth habit",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeString",
                       "bind::esri:fieldLength": "5"})
row(type="select_one veg_layer", name="layer", label="Height layer",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeString",
                       "bind::esri:fieldLength": "5"})
row(type="integer", name="cover_pct", label="Aerial canopy cover (percent)",
    required="yes", constraint=". >= 0 and . <= 100",
    hint="Nearest 1 percent. Cover above 0 and at or below 1 is recorded as 1.",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
endrep()

rep("veg_species", "Species with 3 percent cover or more")
row(type="text", name="vs_species", label="Species (PLANTS symbol)",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeString",
                       "bind::esri:fieldLength": "10"})
row(type="integer", name="vs_cover_pct", label="Total aerial cover (percent)",
    required="yes", constraint=". >= 3 and . <= 100",
    constraint_message="Only species at 3 percent or more are recorded. Do not round up to reach 3.",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
endrep()

# --- I. Monumentation and relocation ----------------------------------------
grp("monument", "I. Monumentation")
row(type="select_one monument_status", name="monument_status",
    label="Monument status", required="yes",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "20"})
row(type="text", name="monument_stamp", label="Cap stamping",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "40"})
row(type="text", name="access_narrative", label="Access route narrative",
    appearance="multiline", required="yes",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "2000"})
row(type="geopoint", name="park_point", label="Parking or approach point")
row(type="text", name="gate_road_status", label="Gate and road status",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "500"})
row(type="text", name="permission_ref", label="Landowner permission reference",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "200"})
row(type="text", name="hazards", label="Hazards", appearance="multiline",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "500"})
row(type="integer", name="travel_minutes",
    label="Travel time from maintained road (minutes)",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
endgrp()

rep("witness", "Witness tree", repeat_count="3")
row(type="text", name="wt_species", label="Species (PLANTS symbol)",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeString",
                       "bind::esri:fieldLength": "10"})
row(type="decimal", name="wt_dbh_in", label="DBH (in)", required="yes",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="decimal", name="wt_azimuth", label="Azimuth to plot center (degrees)",
    required="yes", constraint=". >= 0 and . <= 360",
    **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="decimal", name="wt_distance_ft", label="Horizontal distance (ft)",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeDouble"})
row(type="integer", name="wt_tag", label="Tag number",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
endrep()

rep("photo", "Photograph", repeat_count="7")
row(type="select_one photo_dir", name="photo_direction", label="Photo type",
    required="yes", **{"bind::esri:fieldType": "esriFieldTypeString",
                       "bind::esri:fieldLength": "20"})
row(type="image", name="photo_file", label="Photograph", required="yes",
    appearance="annotate", **{"parameters": "max-pixels=2048"})
endrep()

# --- J. Closeout -------------------------------------------------------------
grp("closeout", "J. Closeout")
row(type="integer", name="crew_minutes_on_plot",
    label="Crew minutes on plot", required="yes",
    hint="Used to calibrate future cost estimates. Do not skip.",
    **{"bind::esri:fieldType": "esriFieldTypeInteger"})
row(type="select_one yesno", name="qa_flag",
    label="Flag this plot for TRPA review", default="no",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "5"})
row(type="text", name="qa_reason", label="Reason for review flag",
    relevant="${qa_flag}='yes'", required="yes", appearance="multiline",
    **{"bind::esri:fieldType": "esriFieldTypeString",
       "bind::esri:fieldLength": "1000"})
endgrp()

# ----------------------------------------------------------------------------
# WRITE WORKBOOK
# ----------------------------------------------------------------------------
wb = Workbook()
hdr_font = Font(bold=True, color="FFFFFF")
hdr_fill = PatternFill("solid", fgColor="1F4E79")

ws = wb.active
ws.title = "survey"
ws.append(SURVEY_COLS)
for r in S:
    ws.append([r[c] for c in SURVEY_COLS])

ws2 = wb.create_sheet("choices")
ws2.append(CHOICES_COLS)
for t in C:
    ws2.append(list(t))

ws3 = wb.create_sheet("settings")
ws3.append(SETTINGS_COLS)
ws3.append([
    "TRPA Forest Health Plot",
    "trpa_forest_health_plot",
    "1.0.0",
    'concat("Plot ", ${plot_id}, " ", format-date(${visit_date}, "%Y-%m-%d"))',
    "",
    "pages",
])

for sheet in (ws, ws2, ws3):
    for cell in sheet[1]:
        cell.font = hdr_font
        cell.fill = hdr_fill
        cell.alignment = Alignment(vertical="center")
    sheet.freeze_panes = "A2"

widths = {"survey": [22, 24, 62, 52, 9, 9, 40, 40, 46, 40, 16, 22, 14, 26, 14, 16, 20],
          "choices": [20, 18, 62],
          "settings": [28, 28, 10, 62, 16, 10]}
for name, ws_w in widths.items():
    sh = wb[name]
    for i, w in enumerate(ws_w, start=1):
        sh.column_dimensions[get_column_letter(i)].width = w

out = "/mnt/user-data/outputs/ForestHealth-Package/TRPA_ForestHealth_Plot_Survey123_v1.0.xlsx"
wb.save(out)
print("survey rows:", len(S))
print("choice rows:", len(C))
print("saved:", out)
