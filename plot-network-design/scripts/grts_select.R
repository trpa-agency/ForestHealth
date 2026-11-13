# scripts/grts_select.R
# Site selection for the forest health status plot network, as decided Oct 19 2026 (Mason and Andy).
#
# One GRTS selection, stratified by forest type, unequal probability within type:
#   seltype "proportional" on aux_var "mult" (1.5 on RRK tail cells, 0.5 on centre slope over 50 percent,
#   their product where both apply), so inclusion probability = n_base x mult / sum(mult) within type.
#   n_base is the RFP minimum per type (40). n_over makes the ranked list three times the full target:
#   SMC 40 + 170 = 210, JP 40 + 80 = 120, RF 40 + 80 = 120. The full level (SMC 70) is the base sites plus the
#   first 30 SMC over sample sites in order; spsurvey orders the over sample so any prefix used in order stays
#   spatially balanced (checked Oct 19 2026: E/W share of the first 30 over sites had a standard deviation of
#   0.04 across 30 seeds against 0.09 for simple random sampling).
#
# Balance on basin side and topographic position is NOT forced. caty_n in spsurvey sets expected counts per
# category, not fixed counts (tested Oct 19 2026: expected 4 per category, realized 0 to 9 across 30 seeds),
# so an area-proportional caty_n is the same design as equal probability. GRTS spatial balance spreads the
# sample; the notebook's section 6 reports realized against expected counts by type, side, and TPI class.
#
# Inputs (written by section 5 of notebooks/00_sample_design_template.ipynb):
#   data/processed/frame_points.gpkg       unit_id, forest_type, mult, basin_side, tpi_class, x, y
#   data/processed/selection_targets.csv   forest_type, n_base, n_over
# Outputs:
#   outputs/grts_select.gpkg               every base and over sample site with siteID, siteuse, stratum, wgt, ip, seed
#   outputs/grts_select_balance.csv        spsurvey sp_balance (Pielou evenness of Voronoi polygons) per type, base sites
#
# Run from the repo root: Rscript scripts/grts_select.R 20261016 100
#   arg1 = seed (draw.seed), arg2 = minimum distance in metres (draw.min_distance_m)

suppressPackageStartupMessages({ library(sf); library(spsurvey) })

args   <- commandArgs(trailingOnly = TRUE)
seed   <- if (length(args) >= 1) as.integer(args[1]) else 20261016L
mindis <- if (length(args) >= 2) as.numeric(args[2]) else 100

frame   <- st_read("data/processed/frame_points.gpkg", quiet = TRUE)
targets <- read.csv("data/processed/selection_targets.csv", stringsAsFactors = FALSE)
message(sprintf("spsurvey %s, seed %d, mindis %.0f m, %d frame units", packageVersion("spsurvey"), seed, mindis, nrow(frame)))

n_base <- setNames(targets$n_base, targets$forest_type)
n_over <- setNames(targets$n_over, targets$forest_type)
frame  <- frame[frame$forest_type %in% names(n_base), ]

set.seed(seed)
sel <- grts(
  sframe      = frame,
  n_base      = n_base,
  stratum_var = "forest_type",
  seltype     = "proportional",
  aux_var     = "mult",
  n_over      = n_over,
  mindis      = mindis,
  DesignID    = "TRPA-FH"
)

sites <- rbind(sel$sites_base, sel$sites_over)
sites$seed <- seed
dir.create("outputs", showWarnings = FALSE)
st_write(sites, "outputs/grts_select.gpkg", delete_dsn = TRUE, quiet = TRUE)
message("wrote ", nrow(sites), " sites: base ", nrow(sel$sites_base), ", over ", nrow(sel$sites_over))
print(table(sites$stratum, sites$siteuse))

sb <- sp_balance(sel$sites_base, frame, stratum_var = "forest_type")
write.csv(sb, "outputs/grts_select_balance.csv", row.names = FALSE)
print(sb)
