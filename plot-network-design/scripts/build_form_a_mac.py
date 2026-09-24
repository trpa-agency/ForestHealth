#!/usr/bin/env python3
"""FORM A: TRPA_LiDARValidation_MAC_Survey123.xlsx

Implements Becky Estes's "Remote Sensing Field Validation & Vegetation
Monitoring" protocol (MACValidationProtocol_Draft10222024.pdf, dated October
30 2024) as faithfully as the PDF allows. CSE-based, fixed-radius circular
plots, 0.2 ac (16.0 m radius) for 30 m pixels or the 0.1 ac default
(11.37 m radius), permanently marked, centered on 30 m grid cells.

Monument and photo detail that the PDF does not specify is taken from
EXHIBIT A (North Yuba contract language) and flagged in hints. Where the PDF
is silent the hint says so rather than inventing a rule.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xlsform_common import FormBuilder, finish, STR, INT, DBL, TODAY  # noqa: E402

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/outputs/survey123"
OUT = os.path.join(OUT_DIR, "TRPA_LiDARValidation_MAC_Survey123.xlsx")

fb = FormBuilder(
    form_title="TRPA LiDAR Validation Plot (MAC protocol)",
    form_id="trpa_lidar_validation_mac",
    instance_name='concat("MAC ", ${plot_id}, " ", format-date(${visit_date}, "%Y-%m-%d"))',
    version=TODAY,
)
row, note, grp, endgrp, rep, endrep, choices = (
    fb.row, fb.note, fb.grp, fb.endgrp, fb.rep, fb.endrep, fb.choices)

# ----------------------------------------------------------------------------
# CHOICE LISTS
# ----------------------------------------------------------------------------
choices("yesno", [("yes", "Yes"), ("no", "No")])

choices("plot_size", [
    ("ac02", "0.2 acre, 16.0 m radius, 707 sq m (30 m pixel plot)"),
    ("ac01", "0.1 acre, 11.37 m radius, 405 sq m (forested default)"),
])

choices("visit_type", [
    ("install", "Installation, new plot"),
    ("remeasure", "Remeasurement, established plot"),
])

choices("utm_zone", [("10", "10N"), ("11", "11N")])

# Figure A1: one code table serves both horizontal and vertical shape
choices("plot_shape", [
    ("BR", "BR - Broken: cliffs, knobs, benches, sharp irregular breaks"),
    ("CC", "CC - Concave: gradient decreases down the slope"),
    ("CV", "CV - Convex: gradient increases down the slope"),
    ("LL", "LL - Linear or planar"),
    ("PA", "PA - Patterned: ordered hummock and swale microrelief"),
    ("UN", "UN - Undulating: low relief ridges and draws within the plot"),
    ("UA", "UA - Unable to assess"),
])

# Figure A2
choices("slope_position", [
    ("SU", "SU - Summit, ridgetop, plateau"),
    ("SH", "SH - Shoulder"),
    ("BS", "BS - Backslope"),
    ("FS", "FS - Footslope"),
    ("TS", "TS - Toeslope"),
    ("VB", "VB - Valley bottom"),
])

# Table A1, Scott and Burgan (2005) fuel models as printed in the PDF
choices("fuel_model", [
    ("NB1", "91 NB1 Urban / developed"), ("NB2", "92 NB2 Snow / ice"),
    ("NB3", "93 NB3 Agricultural"), ("NB8", "98 NB8 Open water"),
    ("NB9", "99 NB9 Bare ground"),
    ("GR1", "101 GR1 Short sparse dry climate grass"),
    ("GR2", "102 GR2 Low load dry climate grass"),
    ("GR3", "103 GR3 Low load very coarse humid climate grass"),
    ("GR4", "104 GR4 Moderate load dry climate grass"),
    ("GR5", "105 GR5 Low load humid climate grass"),
    ("GR6", "106 GR6 Moderate load humid climate grass"),
    ("GR7", "107 GR7 High load dry climate grass"),
    ("GR8", "108 GR8 High load very coarse humid climate grass"),
    ("GR9", "109 GR9 Very high load humid climate grass"),
    ("GS1", "121 GS1 Low load dry climate grass-shrub"),
    ("GS2", "122 GS2 Moderate load dry climate grass-shrub"),
    ("GS3", "123 GS3 Moderate load humid climate grass-shrub"),
    ("GS4", "124 GS4 High load humid climate grass-shrub"),
    ("SH1", "141 SH1 Low load dry climate shrub"),
    ("SH2", "142 SH2 Moderate load dry climate shrub"),
    ("SH3", "143 SH3 Moderate load humid climate shrub"),
    ("SH4", "144 SH4 Low load humid climate timber-shrub"),
    ("SH5", "145 SH5 High load dry climate shrub"),
    ("SH6", "146 SH6 Low load humid climate shrub"),
    ("SH7", "147 SH7 Very high load dry climate shrub"),
    ("SH8", "148 SH8 High load humid climate shrub"),
    ("SH9", "149 SH9 Very high load humid climate shrub"),
    ("TU1", "161 TU1 Low load dry climate timber-grass-shrub"),
    ("TU2", "162 TU2 Moderate load humid climate timber-shrub"),
    ("TU3", "163 TU3 Moderate load humid climate timber-grass-shrub"),
    ("TU4", "164 TU4 Dwarf conifer with understory"),
    ("TU5", "165 TU5 Very high load dry climate timber-shrub"),
    ("TL1", "181 TL1 Low load compact conifer litter"),
    ("TL2", "182 TL2 Low load broadleaf litter"),
    ("TL3", "183 TL3 Moderate load conifer litter"),
    ("TL4", "184 TL4 Small downed logs"),
    ("TL5", "185 TL5 High load conifer litter"),
    ("TL6", "186 TL6 Moderate load broadleaf litter"),
    ("TL7", "187 TL7 Large downed logs"),
    ("TL8", "188 TL8 Long-needle litter"),
    ("TL9", "189 TL9 Very high load broadleaf litter"),
    ("SB1", "201 SB1 Low load activity fuel"),
    ("SB2", "202 SB2 Moderate load activity fuel or low load blowdown"),
    ("SB3", "203 SB3 High load activity fuel or moderate load blowdown"),
    ("SB4", "204 SB4 High load blowdown"),
])

choices("fire_severity", [
    ("0", "0 - Not burned"),
    ("1", "1 - Light, patchy groups of surviving shrubs and saplings"),
    ("2", "2 - Lightly burned, most shrubs and saplings dead"),
    ("3", "3 - Moderately burned, understory mostly burned to ground"),
    ("4", "4 - High severity, significant overstory kill, dead needles on trees"),
    ("5", "5 - High severity, total mortality of overstory, no needles"),
])

# Table A2
choices("disturbance_code", [
    ("1", "1 - Site preparation"), ("2", "2 - Artificial regeneration"),
    ("3", "3 - Natural regeneration"), ("4", "4 - Stand improvement"),
    ("5", "5 - Tree cutting"), ("6", "6 - Fire"),
    ("7", "7 - Other silvicultural treatments"), ("8", "8 - Other human disturbance"),
    ("9", "9 - Natural disturbance"), ("10", "10 - Land clearing"),
    ("11", "11 - Insect / disease outbreak"), ("12", "12 - Animal damage"),
    ("13", "13 - Type conversion"), ("14", "14 - Mining"),
    ("15", "15 - Clear cut"), ("16", "16 - Heavy partial cut (20 percent or more removed)"),
    ("17", "17 - Light partial cut (under 20 percent removed)"),
    ("18", "18 - Firewood or local use cut"), ("19", "19 - Incidental cut"),
    ("20", "20 - Pre-commercial thin"), ("21", "21 - Improvement cut"),
    ("22", "22 - Planting throughout the stand"),
    ("23", "23 - Planting within non-stocked holes in the stand"),
    ("24", "24 - Under-planting"), ("25", "25 - Clean and release"),
    ("26", "26 - Chaining"),
])

# Life Form Cheatsheet (11 layer codes)
LIFEFORMS = [
    ("TV", "Total vegetation (all live vegetation, viewed from above)"),
    ("TOT", "Total tree (live)"),
    ("TOV", "Trees 1.8 m and taller (live overstory)"),
    ("TSA", "Trees under 1.8 m (live saplings)"),
    ("TOS", "Total shrub (live)"),
    ("ST", "Tall shrubs, 1.8 m and taller"),
    ("SM", "Medium shrubs, 0.5 to 1.7 m"),
    ("SL", "Short shrubs, under 0.5 m"),
    ("TOF", "Total forbs"),
    ("TOG", "Total graminoids (grasses, sedges, rushes)"),
    ("OTH", "Total other"),
]

choices("comp_layer", [
    ("TOV", "TOV - Tree overstory, 1.8 m and taller"),
    ("TSA", "TSA - Tree saplings, under 1.8 m"),
    ("ST", "ST - Tall shrub, 1.8 m and taller"),
    ("SM", "SM - Medium shrub, 0.5 to 1.7 m"),
    ("SL", "SL - Short shrub, under 0.5 m"),
    ("NA", "Not layered (forb, graminoid, fern, other)"),
])

choices("lifeform", [
    ("tree", "Tree"), ("shrub", "Shrub"), ("forb", "Forb"),
    ("gram", "Graminoid"), ("fern", "Fern"), ("other", "Other"),
])

choices("tally_status", [
    ("L", "Live"), ("D", "Dead"), ("M", "Marginal"),
])

choices("cwhr_size", [
    ("1", "1 - Seedling, under 1.0 in DBH"),
    ("2", "2 - Sapling, 1.0 to 5.9 in"),
    ("3", "3 - Pole, 6.0 to 10.9 in"),
    ("4", "4 - Small, 11.0 to 23.9 in"),
    ("5", "5 - Medium / large, 24.0 in and up"),
    ("6", "6 - Multi-layered (size 5 over size 4 or 3, 60 percent or more total cover)"),
    ("0", "0 - Not determined / not applicable"),
])

choices("cwhr_size_tally", [
    ("1", "1 - Seedling, under 1.0 in DBH (2.5 cm)"),
    ("2", "2 - Sapling, 1.0 to 5.9 in (2.5 to 15.0 cm)"),
    ("3", "3 - Pole, 6.0 to 10.9 in (15.2 to 27.7 cm)"),
    ("4", "4 - Small, 11.0 to 23.9 in (27.9 to 60.7 cm)"),
    ("5", "5 - Medium / large, 24.0 in and up (61.0 cm)"),
])

choices("cwhr_canopy", [
    ("S", "S - Sparse, 10.0 to 24.9 percent"),
    ("P", "P - Open, 25.0 to 39.9 percent"),
    ("M", "M - Moderate, 40.0 to 59.9 percent"),
    ("D", "D - Dense, 60 percent and up"),
    ("X", "X - Not determined / not applicable"),
])

choices("cwhr_type", [
    ("ASP", "ASP Aspen"), ("BOP", "BOP Blue oak-foothill pine"),
    ("BOW", "BOW Blue oak woodland"), ("COW", "COW Coastal oak woodland"),
    ("CPC", "CPC Closed-cone pine-cypress"), ("DFR", "DFR Douglas-fir"),
    ("DRI", "DRI Desert riparian"), ("EPN", "EPN Eastside pine"),
    ("EUC", "EUC Eucalyptus"), ("JPN", "JPN Jeffrey pine"),
    ("JST", "JST Joshua tree"), ("JUN", "JUN Juniper"),
    ("KMC", "KMC Klamath mixed conifer"), ("LPN", "LPN Lodgepole pine"),
    ("MHC", "MHC Montane hardwood-conifer"), ("MHW", "MHW Montane hardwood"),
    ("MRI", "MRI Montane riparian"), ("PJN", "PJN Pinyon-juniper"),
    ("POS", "POS Palm oasis"), ("PPN", "PPN Ponderosa pine"),
    ("RDW", "RDW Redwood"), ("RFR", "RFR Red fir"),
    ("SCN", "SCN Subalpine conifer"), ("SMC", "SMC Sierran mixed conifer"),
    ("VOW", "VOW Valley oak woodland"), ("VRI", "VRI Valley foothill riparian"),
    ("WFR", "WFR White fir"),
    ("ADS", "ADS Alpine dwarf shrub"), ("ASC", "ASC Alkali desert scrub"),
    ("BBR", "BBR Bitterbrush"), ("CRC", "CRC Chamise-redshank chaparral"),
    ("CSC", "CSC Coastal scrub"), ("DSC", "DSC Desert scrub"),
    ("DSS", "DSS Desert succulent shrub"), ("DSW", "DSW Desert wash"),
    ("LSG", "LSG Low sage"), ("MCH", "MCH Mixed chaparral"),
    ("MCP", "MCP Montane chaparral"), ("SGB", "SGB Sagebrush"),
    ("AGS", "AGS Annual grassland"), ("FEW", "FEW Fresh emergent wetland"),
    ("PAS", "PAS Pasture"), ("PGS", "PGS Perennial grassland"),
    ("SEW", "SEW Saline emergent wetland"), ("WTM", "WTM Wet meadow"),
    ("EST", "EST Estuarine"), ("LAC", "LAC Lacustrine"),
    ("MAR", "MAR Marine"), ("RIV", "RIV Riverine"),
    ("URB", "URB Urban"), ("BAR", "BAR Barren"),
])

choices("fractal", [(str(i), str(i)) for i in range(1, 9)])

choices("tree_status", [
    ("L", "L - Live"),
    ("I", "I - Infested but green crown (fresh pitch, frass, exit holes)"),
    ("M", "M - Marginal crown (partially red for pine, over 50 percent red for incense cedar)"),
    ("D1", "D1 - Dead, most red needles retained"),
    ("D2", "D2 - Dead, most needles lost"),
    ("D3", "D3 - Snag, decay class 2 to 5"),
    ("FT", "FT - Fallen tree, cannot be located standing"),
])

# Health codes from the PDF. The PDF prints A twice (blister rust and dwarf
# mistletoe) and M twice (mistletoe and mountain pine beetle); unique codes
# are used here and the letter printed in the PDF is kept in the label.
choices("health_code", [
    ("BR", "A - White pine blister rust aecia"),
    ("DT", "D - Dead top"),
    ("ST", "S - Split top"),
    ("CF", "C - Catface"),
    ("MT", "M - Mistletoe (leafy)"),
    ("DM", "A - Dwarf mistletoe (Arceuthobium)"),
    ("PT", "P - Extensive pitching on bole"),
    ("RTB", "T - Red turpentine beetle"),
    ("WPB", "W - Western pine beetle"),
    ("MPB", "M - Mountain pine beetle"),
    ("JPB", "J - Jeffrey pine beetle"),
    ("OT", "O - Other issue, describe in notes"),
])

choices("decay_class", [
    ("1", "1 - Bark intact, twigs present, texture intact, round, original color, elevated on support points"),
    ("2", "2 - Bark intact, twigs absent, intact to soft, round, original color, parts touch ground"),
    ("3", "3 - Bark trace, hard large pieces, round, original to faded, bole on ground"),
    ("4", "4 - Bark absent, soft blocky pieces, round to oval, light brown, partially below ground"),
    ("5", "5 - Bark absent, soft powdery, oval, faded yellow or gray, mostly below ground"),
])

choices("height_stratum", [
    ("dominant", "Dominant"), ("codominant", "Codominant"),
    ("intermediate", "Intermediate"), ("suppressed", "Suppressed"),
])

choices("crown_class", [
    ("OP", "OP - Open grown or isolated"), ("DO", "DO - Dominant"),
    ("CO", "CO - Codominant"), ("IN", "IN - Intermediate"),
    ("OV", "OV - Overtopped"), ("RE", "RE - Remnant"),
    ("AB", "AB - Leader above brush"), ("IB", "IB - Leader within brush"),
])

choices("shade_tolerance", [
    ("tolerant", "Shade tolerant (ABCO, ABMA, CADE27, TSME, PSME)"),
    ("intolerant", "Shade intolerant (PIJE, PIPO, PICO, PILA, POTR5, QUKE)"),
])

choices("photo_type", [
    ("tag", "Plot tag"), ("N", "North, 0 degrees"), ("E", "East, 90 degrees"),
    ("S", "South, 180 degrees"), ("W", "West, 270 degrees"),
    ("transect", "Transect looking toward plot center (Exhibit A)"),
    ("other", "Other"),
])

choices("checklist", [
    ("plot", "Plot data and photos"), ("veg_cover", "Vegetation cover form"),
    ("ground", "Ground cover form"), ("density", "Tree density tally and CWHR"),
    ("ba", "Basal area"), ("fuels", "Four fuels transects"),
    ("trees", "Individual trees, all tagged"), ("heights", "Tree heights"),
    ("regen", "Regeneration plot"), ("witness", "Two witness trees"),
    ("composition", "Species composition"), ("monument", "Monument flagged and tagged"),
])

choices("monument_status", [
    ("new", "New installation"), ("found_good", "Found, good condition"),
    ("found_damaged", "Found, damaged or displaced"),
    ("replaced", "Not found, replaced"),
])

# ----------------------------------------------------------------------------
# SURVEY
# ----------------------------------------------------------------------------
note("intro", "**Remote Sensing Field Validation and Vegetation Monitoring (MAC, CSE based)**  \n"
     "Circular plot, 0.2 ac (16.0 m radius) for 30 m pixels, or 0.1 ac (11.37 m) default. "
     "Centered in the 30 m grid cell. Permanently marked. Metric throughout; feet in hints.")

# --- 1. Plot data -------------------------------------------------------------
grp("plot", "1. Plot data")
fb.text("plot_id", "Plot number", length=20, required="yes")
fb.date("visit_date", "Date", required="yes", default="today()")
fb.calc("site_id", "concat(${plot_id}, '_', format-date(${visit_date}, '%Y%m%d'))",
        ftype=STR, **{"bind::esri:fieldLength": "40"})
note("site_id_note", "SiteID: ${site_id}")
fb.text("observers", "Observer initials", length=60, required="yes")
fb.select1("visit_type", "visit_type", "Visit type", required="yes",
           hint="GPS, slope, aspect, shape, and slope position are not re-collected on established plots")
fb.select1("plot_size", "plot_size", "Plot size", required="yes", default="ac02",
           hint="0.2 ac = 16.0 m (52.5 ft) radius. 0.1 ac = 11.37 m (37.3 ft) radius.")
fb.calc("plot_radius_m", "if(${plot_size}='ac02', 16.0, 11.37)")
fb.text("camera", "Camera the photos were taken on", length=60, required="yes")
fb.datetime("plot_start_time", "Time started", default="now()")
endgrp()

rep("photo", "Photograph", repeat_count="5")
fb.select1("photo_type", "photo_type", "Photo", required="yes",
           hint="Plot tag first, then N, E, S, W clockwise from center. Exhibit A: label with plot number and direction, same zoom level.")
fb.image("photo_file", "Photograph", required="yes")
endrep()

grp("gps", "1b. Plot location")
note("gps_note", "Sub-centimeter GPS unit per the protocol. Not needed on an already established plot; navigate to the recorded coordinates instead.")
fb.geopoint("nav_point", "Device position (navigation only)")
fb.select1("utm_zone", "utm_zone", "UTM zone", length=5, default="10",
           relevant="${visit_type}='install'", required="yes")
fb.decimal("utm_easting_m", "Easting (m)", relevant="${visit_type}='install'",
           required="yes", constraint=". > 100000 and . < 900000")
fb.decimal("utm_northing_m", "Northing (m)", relevant="${visit_type}='install'",
           required="yes", constraint=". > 4000000 and . < 5000000")
fb.text("gps_unit", "GPS unit", length=80, relevant="${visit_type}='install'")
fb.decimal("gps_horiz_acc_m", "Horizontal accuracy reported by the unit (m)",
           relevant="${visit_type}='install'",
           hint="The PDF asks for sub-centimeter accuracy and does not define a fallback. Record what the unit reports.")
endgrp()

grp("site", "1c. Site")
fb.integer("slope_pct", "Slope (percent)", constraint=". >= 0 and . <= 200",
           relevant="${visit_type}='install'", required="yes",
           hint="Clinometer from center in both directions of the aspect axis to the plot edge, averaged. Nearest 1 percent.")
fb.integer("aspect_deg", "Aspect (degrees)", constraint=". >= 0 and . <= 360",
           relevant="${visit_type}='install'", required="yes",
           hint="Hand compass, same direction as the slope, nearest 1 degree")
fb.select1("plot_shape", "shape_horizontal", "Plot horizontal shape", length=5,
           relevant="${visit_type}='install'", required="yes",
           hint="Figure A1. The PDF gives one code table for both horizontal and vertical.")
fb.select1("plot_shape", "shape_vertical", "Plot vertical shape", length=5,
           relevant="${visit_type}='install'", required="yes")
fb.select1("slope_position", "slope_position", "Slope position", length=5,
           relevant="${visit_type}='install'", required="yes", hint="Figure A2. Accuracy plus or minus 1 class.")
fb.integer("cga_pct", "Capable growing area (percent of plot able to grow trees)",
           required="yes", constraint=". >= 0 and . <= 100")
fb.select1("fuel_model", "fuel_model", "Scott and Burgan fuel model", length=5,
           required="yes", hint="Table A1. Best attempt; the GTR is on the tablet.")
fb.species("overstory_sp1", "Overstory species 1 (most dominant)")
fb.species("overstory_sp2", "Overstory species 2", required="")
fb.species("overstory_sp3", "Overstory species 3", required="")
fb.select1("fire_severity", "fire_severity", "Fire severity class", length=5,
           required="yes", hint="Pre-treatment plots should all be 0, not burned")
endgrp()

rep("plot_history", "Plot history event")
fb.select1("disturbance_code", "hist_code", "Activity or disturbance (Table A2)",
           length=5, required="yes")
fb.integer("hist_year", "Estimated year", required="yes",
           constraint=". >= 1850 and . <= 2100")
fb.text("hist_notes", "Notes", length=200)
endrep()

# --- 2. Vegetation cover form ------------------------------------------------
grp("veg_cover", "2. Vegetation cover form (whole plot)")
note("vc_note", "Percent cover of the whole plot to the nearest 5 percent, "
     "modal height in m to 0.1. Present but under 0.5 percent is recorded as 0.5. "
     "On the 0.1 ac plot about 4 sq m is 1 percent; on the 0.2 ac plot about 8 sq m. "
     "TOV plus TSA will usually exceed TOT, and ST plus SM plus SL will exceed TOS, because of crown overlap. "
     "The PDF says twelve classes; its Life Form Cheatsheet lists eleven, which are the eleven here.")
for code, lab in LIFEFORMS:
    fb.decimal(f"cov_{code.lower()}_pct", f"{code} cover (percent): {lab}",
               required="yes", constraint=". >= 0 and . <= 100",
               constraint_message="0 to 100. Use 0.5 for present but under 0.5 percent.")
    fb.decimal(f"ht_{code.lower()}_m", f"{code} modal height (m)",
               relevant=f"${{cov_{code.lower()}_pct}} > 0", required="yes",
               constraint=". >= 0 and . <= 100")
endgrp()

rep("tree_sp_cover", "Cover by tree species (live)")
fb.species("tsc_species", "Tree species")
fb.unk_species("tsc_species", "tsc_species_unk")
fb.decimal("tsc_cover_pct", "Cover (percent)", required="yes",
           constraint=". > 0 and . <= 100")
fb.decimal("tsc_height_m", "Modal height (m)", constraint=". >= 0 and . <= 100")
endrep()

# --- 3. Ground cover form ----------------------------------------------------
grp("ground_cover", "3. Ground cover form (whole plot)")
note("gc_note", "Ground surface cover without vegetation. Nearest 5 percent. Must sum to 100.")
fb.integer("gc_basal_veg_pct", "Live basal vegetation (percent)", required="yes",
           constraint=". >= 0 and . <= 100")
fb.integer("gc_rock_pct", "Rock (percent)", required="yes", constraint=". >= 0 and . <= 100")
fb.integer("gc_cwd_pct", "Coarse woody debris (percent)", required="yes",
           constraint=". >= 0 and . <= 100")
fb.integer("gc_litter_pct", "Litter (percent)", required="yes", constraint=". >= 0 and . <= 100")
fb.integer("gc_cryptogam_pct", "Cryptogams (percent)", required="yes",
           constraint=". >= 0 and . <= 100")
fb.integer("gc_bare_pct", "Bare ground (percent)", required="yes",
           constraint="(${gc_basal_veg_pct} + ${gc_rock_pct} + ${gc_cwd_pct} + ${gc_litter_pct} + ${gc_cryptogam_pct} + .) = 100",
           constraint_message="Ground cover categories must sum to exactly 100 percent")
fb.calc("gc_sum_pct", "${gc_basal_veg_pct} + ${gc_rock_pct} + ${gc_cwd_pct} + ${gc_litter_pct} + ${gc_cryptogam_pct} + ${gc_bare_pct}", ftype=INT)
endgrp()

# --- 4. Tree density tally ---------------------------------------------------
note("density_note", "**4. Tree density tally (whole plot).** Count trees by species, "
     "status, and CWHR size class. One row per species by status by size class.")
rep("density", "Tally row")
fb.species("den_species", "Species")
fb.unk_species("den_species", "den_species_unk")
fb.select1("tally_status", "den_status", "Status", length=5, required="yes")
fb.select1("cwhr_size_tally", "den_size", "CWHR size class", length=5, required="yes")
fb.integer("den_count", "Count", required="yes", constraint=". > 0")
endrep()

grp("structure", "4b. Structure and CWHR")
fb.select1("fractal", "fractal_index", "Fractal dimension index (Figure 1)", length=5,
           required="yes", appearance="likert",
           hint="1 is uniform, 8 is the most complex clump and gap pattern")
fb.select1("cwhr_type", "cwhr_type", "CWHR vegetation type", length=5, required="yes",
           hint="Appendix C flow chart from the vegetation cover data")
fb.select1("cwhr_size", "cwhr_size", "CWHR size class", length=5, required="yes")
fb.select1("cwhr_canopy", "cwhr_canopy", "CWHR canopy closure class", length=5,
           required="yes")
endgrp()

# --- 5. Stand basal area ------------------------------------------------------
grp("basal_area", "5. Stand basal area (variable radius, gauge or prism)")
fb.text("ba_instrument", "Basal area gauge or prism used", length=60, required="yes",
        hint="Gauge: hold at arm's length over plot center and walk around it. Prism: stand at center and swing the prism.")
fb.decimal("baf", "Basal area factor (sq ft per acre per tree)", required="yes",
           constraint=". > 0 and . <= 80",
           hint="The PDF does not name a factor; record the one on the instrument")
endgrp()

rep("ba_tally", "Basal area count by species")
fb.species("ba_species", "Species")
fb.unk_species("ba_species", "ba_species_unk")
fb.integer("ba_live_count", "Live trees in", required="yes", constraint=". >= 0")
fb.integer("ba_dead_count", "Dead trees in", required="yes", constraint=". >= 0")
fb.calc("ba_live_sqft_ac", "${ba_live_count} * ${baf}")
fb.calc("ba_dead_sqft_ac", "${ba_dead_count} * ${baf}")
endrep()

# --- 6. Woody fuels -----------------------------------------------------------
note("fuel_note", "**6. Woody fuels, four Brown's transects.** Cardinal directions from "
     "plot center to plot edge. Transects are READ FROM THE EDGE toward center; "
     "0 m is at the plot edge. Go/no-go gauge for fine fuels. Fuel particles must be "
     "severed from the source; no needles, grass, bark, cones, or rooted stumps; "
     "intersection must lie above the litter and duff.")
rep("transect", "Fuels transect", repeat_count="4")
fb.calc("tr_index", "position(..)", ftype=INT)
fb.calc("tr_default_az", "(${tr_index} - 1) * 90", ftype=INT)
fb.integer("tr_azimuth_deg", "Transect azimuth (degrees)", required="yes",
           calculation="${tr_default_az}", constraint=". >= 0 and . <= 360",
           hint="Defaults to N, E, S, W. Overwrite only if the transect had to diverge from the cardinal direction.")
note("tr_len_note", "Transect length is the plot radius: ${plot_radius_m} m. Distances below are from the transect start at the plot edge.")
fb.integer("fwd_1hr_count", "1-hr fuels count, under 0.64 cm, 3.0 to 5.0 m", required="yes",
           constraint=". >= 0", hint="Under 0.25 in")
fb.integer("fwd_10hr_count", "10-hr fuels count, 0.64 to 2.54 cm, 3.0 to 5.0 m",
           required="yes", constraint=". >= 0", hint="0.25 to 1.0 in")
fb.integer("fwd_100hr_count", "100-hr fuels count, 2.54 to 7.62 cm, 3.0 to 6.0 m",
           required="yes", constraint=". >= 0", hint="1.0 to 3.0 in")
note("depth_note", "Litter, duff, and fuel depth at 3.8 m and 7.6 m from the transect start. "
     "The PDF does not state the depth unit; cm is used here to match Exhibit A. "
     "The PDF's alternative note (11.3, 7.5, 3.7 when 0 m is at center) is ambiguous and is not implemented.")
for d in ("38", "76"):
    lbl = "3.8 m" if d == "38" else "7.6 m"
    fb.decimal(f"litter_{d}_cm", f"Litter depth at {lbl} (cm)", required="yes",
               constraint=". >= 0 and . <= 200")
    fb.decimal(f"duff_{d}_cm", f"Duff depth at {lbl} (cm)", required="yes",
               constraint=". >= 0 and . <= 200")
    fb.decimal(f"fuel_depth_{d}_cm", f"Fuel bed depth at {lbl} (cm)", required="yes",
               constraint=". >= 0 and . <= 500")

rep("cwd", "CWD piece on this transect")
note("cwd_note", "Tally when the central axis crosses the transect, diameter at the "
     "intersection is over 7.6 cm (3 in), and the piece is at least 1 m (3.3 ft) long. "
     "Count both intersections of a curved piece.")
fb.decimal("cwd_dist_m", "Distance along transect from start (m)",
           constraint=". >= 0 and . <= ${plot_radius_m}",
           hint="Optional; the PDF does not ask for it")
fb.species("cwd_species", "Species", required="")
fb.decimal("cwd_dia_intersect_cm", "Diameter at transect intersection (cm)",
           required="yes", constraint=". > 7.6",
           constraint_message="CWD must be over 7.6 cm (3 in) at the intersection")
fb.decimal("cwd_dia_large_cm", "Diameter at large end (cm)", required="yes",
           constraint=". >= ${cwd_dia_intersect_cm}")
fb.decimal("cwd_dia_small_cm", "Diameter at small end (cm)", required="yes",
           constraint=". > 0 and . <= ${cwd_dia_large_cm}")
fb.decimal("cwd_length_m", "Length (m)", required="yes", constraint=". >= 1.0",
           constraint_message="Minimum piece length is 1 m (3.3 ft)")
fb.select1("decay_class", "cwd_decay", "Decay class", length=5, required="yes",
           appearance="likert")
endrep()
endrep()

# --- 7. Trees ------------------------------------------------------------------
note("tree_note", "**7. Trees (whole plot).** All live and dead trees at or above 7.6 cm "
     "(3.0 in) DBH and 1.37 m (4.5 ft) tall are measured individually. All live trees "
     "are tagged; add a tag to any untagged live tree and note it. The PDF does not "
     "record azimuth or distance per tree, so the in-or-out call is made in the field "
     "against the ${plot_radius_m} m radius.")
rep("tree", "Tree")
fb.integer("tree_tag", "Tag number", required="yes")
fb.select1("tree_status", "tree_status", "Status", length=5, required="yes",
           hint="The PDF header lists L, D, S, X, Y but defines L, I, M, D1, D2, D3, FT. The defined codes are used.")
fb.yesno("ft_tag_visible", "Fallen tree: is the tag visible", required="yes",
         relevant="${tree_status}='FT'")
fb.species("species", "Species")
fb.unk_species("species", "species_unk")
fb.yesno("dead_prior_fire", "Dead prior to the fire",
         relevant="${tree_status}='D1' or ${tree_status}='D2' or ${tree_status}='D3'")
fb.decimal("dbh_cm", "DBH (cm, d-tape)", required="yes",
           relevant="${tree_status}!='FT'",
           constraint=". >= 7.6 and . <= 300",
           constraint_message="Tree tally floor is 7.6 cm (3.0 in). Smaller stems go in the regeneration plot.",
           hint="7.6 cm = 3.0 in. Measured at 1.37 m (4.5 ft).")
fb.selectm("health_code", "health_codes", "Health codes",
           relevant="${tree_status}!='FT'",
           hint="Ignore bole pitching unless extensive. Describe O in notes.")
fb.integer("live_crown_ratio_pct", "Live crown ratio (percent of total height with live foliage)",
           relevant="${tree_status}='L' or ${tree_status}='I' or ${tree_status}='M'",
           required="yes", constraint=". >= 0 and . <= 100")
fb.decimal("htlcb_m", "Height to live crown base (m, to 0.1)",
           relevant="${tree_status}='L' or ${tree_status}='I' or ${tree_status}='M'",
           required="yes", constraint=". >= 0 and . <= 100",
           hint="Lowest live, vertically continuous crown: a wedge of at least 30 degrees and less than 2 m below continuous crown. Measure where the branch meets the bole.")
fb.select1("decay_class", "decay_class", "Decay class (dead trees)", length=5,
           relevant="${tree_status}='D1' or ${tree_status}='D2' or ${tree_status}='D3'",
           required="yes", appearance="likert")
fb.yesno("witness_tree", "Witness tree", default="no")
fb.text("tree_notes", "Notes", length=500, appearance="multiline",
        hint="Dead top: record height to the top of the live crown here. New tag numbers here.")
endrep()

# --- 8. Tree heights -----------------------------------------------------------
note("height_note", "**8. Tree heights.** The tallest tree in each of the four strata "
     "present on the plot. On a remeasurement, measure the same trees as last time.")
rep("height_tree", "Height tree", repeat_count="4")
fb.select1("height_stratum", "ht_stratum", "Stratum", required="yes",
           hint="The PDF names dominant, codominant, intermediate, suppressed here; the crown class cheatsheet uses a longer list.")
fb.integer("ht_tag", "Tag number", required="yes")
fb.decimal("height_m", "Total height (m, to 0.1)", required="yes",
           constraint=". > 1.37 and . <= 100",
           hint="Leaning tree: measure from the ground directly beneath the top. Include a dead top. 1 m = 3.28 ft.")
fb.integer("lean_deg", "Lean angle if leaning (degrees)",
           constraint=". >= 0 and . <= 90", hint="The PDF asks for this in notes; recorded as a field here")
fb.decimal("crown_width_1_m", "Crown width, first axis (m)", required="yes",
           constraint=". >= 0 and . <= 50")
fb.decimal("crown_width_2_m", "Crown width, perpendicular axis (m)", required="yes",
           constraint=". >= 0 and . <= 50",
           hint="Enter the same value twice if the crown is circular")
fb.calc("crown_width_avg_m", "round((${crown_width_1_m} + ${crown_width_2_m}) div 2, 1)")
endrep()

# --- 9. Regeneration ------------------------------------------------------------
note("regen_note", "**9. Regeneration plot, 4.37 m radius (60 sq m).** Flag four points on "
     "the perimeter. Seedlings are under 1.37 m (4.5 ft) tall. Saplings are over 1.37 m "
     "tall and under 7.6 cm (3 in) DBH. Age is bud scar count minus the current year.")
rep("seedling", "Seedlings by species")
fb.species("seed_species", "Species")
fb.unk_species("seed_species", "seed_species_unk")
fb.integer("seed_count_age0", "Count, age class 0 (current year)", required="yes",
           constraint=". >= 0")
fb.integer("seed_count_age1plus", "Count, age class 1 and older", required="yes",
           constraint=". >= 0")
fb.decimal("seed_tallest_ht_m", "Tallest seedling height (m)",
           constraint=". >= 0 and . < 1.37")
fb.integer("seed_tallest_age_yr", "Tallest seedling age (years)", constraint=". >= 0")
fb.decimal("seed_tallest_growth_cm", "Tallest seedling last year's growth (cm)",
           constraint=". >= 0")
endrep()

rep("sapling", "Sapling (individual)")
fb.species("sap_species", "Species")
fb.unk_species("sap_species", "sap_species_unk")
fb.decimal("sap_dbh_cm", "DBH (cm)", required="yes",
           constraint=". > 0 and . < 7.6",
           constraint_message="Saplings are under 7.6 cm (3 in). Larger stems go in the tree repeat.")
endrep()

rep("resprout", "Resprout (individual or clump, hardwoods)")
fb.species("rs_species", "Species")
fb.unk_species("rs_species", "rs_species_unk")
fb.decimal("rs_height_m", "Height of tallest resprout (m)", required="yes",
           constraint=". > 0")
fb.decimal("rs_dbh_cm", "DBH of tallest resprout if over 1.37 m tall (cm)",
           relevant="${rs_height_m} > 1.37", constraint=". > 0")
fb.integer("rs_age_yr", "Age (years, bud scars)", constraint=". >= 0")
fb.integer("rs_sprout_count", "Number of sprouts in the clump", required="yes",
           constraint=". >= 1", hint="Clumps more than 1 m apart are separate resprouts")
endrep()

rep("seed_source", "Nearest regenerated tree and seed source by species")
fb.species("ss_species", "Species")
fb.select1("shade_tolerance", "ss_tolerance", "Shade tolerance group", required="yes")
fb.decimal("ss_dist_regen_m", "Distance to nearest regenerated tree (m)", required="yes",
           constraint=". >= 0")
fb.decimal("ss_dist_seed_source_m", "Distance to nearest seed source (m)", required="yes",
           constraint=". >= 0")
endrep()

# --- 10. Witness trees and monument -----------------------------------------------
note("witness_note", "**10. Witness trees.** Two previously tagged trees at roughly 90 "
     "degrees to each other through plot center, with an unobstructed pull to the base "
     "of the stake. Exhibit A: use two of the largest trees, tag nailed facing center.")
rep("witness", "Witness tree", repeat_count="2")
fb.integer("wt_tag", "Tag number", required="yes")
fb.species("wt_species", "Species", required="")
fb.decimal("wt_distance_m", "Distance to plot center (m, to 0.1)", required="yes",
           constraint=". > 0 and . <= 20",
           hint="The PDF does not say slope or horizontal distance. Record horizontal and note if slope.")
fb.decimal("wt_azimuth_deg", "Azimuth from tree to plot center (degrees)", required="yes",
           constraint=". >= 0 and . <= 360")
endrep()

grp("monument", "10b. Monument (PDF plus Exhibit A)")
fb.select1("monument_status", "monument_status", "Monument status", required="yes")
fb.yesno("rebar_set", "Rebar at plot center with cap and metal tag labeled with the plot number",
         required="yes",
         hint="The PDF says flag the rebar and wire the plot tag to it. Exhibit A adds the cap, the tag, and at least 1 ft (30 cm) above ground.")
fb.decimal("rebar_above_ground_cm", "Rebar height above ground (cm)",
           constraint=". >= 0 and . <= 150")
fb.text("plot_tag_number", "Plot tag number on the rebar", length=20, required="yes")
fb.yesno("center_flagged", "Rebar and a few nearby trees flagged", required="yes")
fb.yesno("approach_flags", "Two white attention flags hung at eye level from the direction of access (Exhibit A)",
         required="yes")
fb.text("monument_notes", "Monument and access notes", length=1000, appearance="multiline")
endgrp()

# --- 11. Species composition ------------------------------------------------------
note("comp_note", "**11. Species composition (whole plot).** Trees first, then shrubs, "
     "then the rest where full floristics are in scope. Cover to the nearest 1 percent. "
     "A species can appear once per layer.")
fb.yesno("full_floristics", "Full floristics collected (forbs and graminoids), not trees and shrubs only",
         required="yes", default="no")
rep("composition", "Species by layer")
fb.select1("lifeform", "comp_lifeform", "Lifeform", length=10, required="yes")
fb.species("comp_species", "Species", woody_only=False)
fb.unk_species("comp_species", "comp_species_unk")
fb.text("comp_new_species", "New species not in the list (scientific name)", length=80,
        relevant="${comp_species}='XXXX'")
fb.select1("comp_layer", "comp_layer", "Layer code", length=5, required="yes",
           hint="Trees: TOV or TSA. Shrubs: ST, SM, or SL. Others: not layered.")
fb.integer("comp_cover_pct", "Cover (percent)", required="yes",
           constraint=". >= 1 and . <= 100")
fb.text("comp_notes", "Notes", length=200)
endrep()

# --- 12. Checklist and closeout ---------------------------------------------------
grp("closeout", "12. Plot checklist and closeout")
fb.selectm("checklist", "checklist", "Plot checklist, confirm each section is complete",
           required="yes")
fb.datetime("plot_end_time", "Time finished")
fb.text("plot_notes", "Plot notes", length=2000, appearance="multiline")
endgrp()

if __name__ == "__main__":
    finish(fb, OUT)
