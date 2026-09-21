# scripts/grts_draw.R
# Frozen GRTS draw with spsurvey, for parity with the TEON backbone (Shale Hunter used spsurvey).
#
# Inputs (written by notebooks/03_allocate_draw.ipynb):
#   data/processed/frame_points.gpkg     candidate pixel centers with cell_id, inclusion_weight, x, y
#   data/processed/allocation_full.csv   cell_id, n_B  (use the level you are freezing)
#   data/processed/legacy_sites.gpkg     existing plots with cell_id (optional)
# Output:
#   outputs/grts_draw_spsurvey.gpkg      sites with siteID, stratum, wgt, ip, siteuse (Base/Over), caty
#
# Run: Rscript scripts/grts_draw.R 20261016 2.5
#   arg1 = seed, arg2 = oversample factor

suppressPackageStartupMessages({ library(sf); library(spsurvey) })

args <- commandArgs(trailingOnly = TRUE)
seed <- if (length(args) >= 1) as.integer(args[1]) else 20261016L
over <- if (length(args) >= 2) as.numeric(args[2]) else 2.5
set.seed(seed)

frame <- st_read("data/processed/frame_points.gpkg", quiet = TRUE)
alloc <- read.csv("data/processed/allocation_full.csv", stringsAsFactors = FALSE)
n_base <- setNames(alloc$n_B, alloc$cell_id)
n_over <- setNames(ceiling(alloc$n_B * (over - 1)), alloc$cell_id)

legacy <- NULL
if (file.exists("data/processed/legacy_sites.gpkg")) {
  legacy <- st_read("data/processed/legacy_sites.gpkg", quiet = TRUE)
  legacy <- legacy[legacy$cell_id %in% names(n_base), ]
  message("Legacy sites in frame: ", nrow(legacy))
}

# Unequal inclusion probability via the "proportional" option on inclusion_weight.
# Stratified by cell_id; legacy sites are honoured and the draw balances around them.
draw <- grts(
  sframe     = frame,
  n_base     = n_base,
  stratum_var = "cell_id",
  seltype    = "proportional",
  aux_var    = "inclusion_weight",
  n_over     = n_over,
  legacy_sites = legacy,
  legacy_stratum_var = if (!is.null(legacy)) "cell_id" else NULL,
  DesignID   = "TRPA-FH"
)

sites <- rbind(
  cbind(draw$sites_legacy, siteuse2 = "legacy"),
  cbind(draw$sites_base,   siteuse2 = "primary"),
  cbind(draw$sites_over,   siteuse2 = "backup")
)
sites$seed <- seed
dir.create("outputs", showWarnings = FALSE)
st_write(sites, "outputs/grts_draw_spsurvey.gpkg", delete_dsn = TRUE, quiet = TRUE)
message("Wrote ", nrow(sites), " sites to outputs/grts_draw_spsurvey.gpkg (seed ", seed, ")")

# Spatial balance check against simple random sampling
sb <- sp_balance(draw$sites_base, frame, stratum_var = "cell_id")
print(sb)
