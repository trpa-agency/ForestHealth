# scripts/grts_split_draw.R
# Split-sample site selection adopted September 19, 2026 (Pat Manley meeting).
#
# Half A: spatially balanced, NOT pre-stratified on structure.
#         Stratified by forest_type only (the reporting domain) so that domain
#         sample sizes are fixed rather than random. Within each stratum the
#         expected count per balance category (basin side x topographic
#         position, from src/covariates.py) is set with caty_n, so east/west
#         and landform coverage is guaranteed without becoming strata. Those
#         attributes do not change between cycles, so balancing on them does
#         not lock the design to a current-condition snapshot.
# Half B: unequal inclusion probability, weighted by inclusion_weight (tail boost,
#         aspen, riparian, co-registration targets), stratified by cell_id as
#         in scripts/grts_draw.R.
#
# Both halves keep design weights, so they pool in spsurvey estimators. Legacy
# sites (LTW, burn plots, MSIM/LTUB conversions) enter Half A as legacy_sites so
# the equal-probability selection balances around them.
#
# Inputs (written by notebooks/03_allocate_draw.ipynb):
#   data/processed/frame_points.gpkg     candidate points: x, y, cell_id, forest_type,
#                                        inclusion_weight, balance_caty (side_topo)
#   data/processed/allocation_full.csv   cell_id, forest_type, n_B  (Half B allocation)
#   data/processed/allocation_typeA.csv  forest_type, n_A         (Half A allocation by type)
#   data/processed/caty_n_typeA.csv      forest_type, balance_caty, n  (expected per category,
#                                        from covariates.caty_n_by_stratum)
#   data/processed/legacy_sites.gpkg     existing plots with forest_type and cell_id (optional)
# Output:
#   outputs/grts_split_draw.gpkg         siteID, half, stratum, wgt, ip, siteuse, seed
#   outputs/grts_split_balance.csv       sp_balance for each half
#
# Sampling units are 3x3 LiDAR pixel blocks (plot on the centre pixel). No two sites,
# legacy included, may be closer than mindis (two macroplot radii), so plot footprints
# never overlap. Half B is drawn from the units left after Half A's sites and their
# mindis buffers are removed.
#
# Run: Rscript scripts/grts_split_draw.R 20261016 2.5 120
#   arg1 = seed, arg2 = oversample factor (backups per primary), arg3 = min distance in metres

suppressPackageStartupMessages({ library(sf); library(spsurvey) })

args <- commandArgs(trailingOnly = TRUE)
seed   <- if (length(args) >= 1) as.integer(args[1]) else 20261016L
over   <- if (length(args) >= 2) as.numeric(args[2]) else 2.5
mindis <- if (length(args) >= 3) as.numeric(args[3]) else 120

frame  <- st_read("data/processed/frame_points.gpkg", quiet = TRUE)
allocB <- read.csv("data/processed/allocation_full.csv", stringsAsFactors = FALSE)
allocA <- read.csv("data/processed/allocation_typeA.csv", stringsAsFactors = FALSE)
catyA  <- read.csv("data/processed/caty_n_typeA.csv", stringsAsFactors = FALSE)
# caty_n must be a list of named vectors, one per stratum, when stratum_var is set
caty_n_list <- lapply(split(catyA, catyA$forest_type),
                      function(d) setNames(d$n, d$balance_caty))

legacy <- NULL
if (file.exists("data/processed/legacy_sites.gpkg")) {
  legacy <- st_read("data/processed/legacy_sites.gpkg", quiet = TRUE)
  legacy <- legacy[legacy$forest_type %in% allocA$forest_type, ]
  message("Legacy sites in frame: ", nrow(legacy))
}

# ---- Half A: stratified by forest type, balanced on side x landform -----------
set.seed(seed)
nA_base <- setNames(allocA$n_A, allocA$forest_type)
nA_over <- setNames(ceiling(allocA$n_A * (over - 1)), allocA$forest_type)

drawA <- grts(
  sframe             = frame,
  n_base             = nA_base,
  stratum_var        = "forest_type",
  seltype            = "unequal",
  caty_var           = "balance_caty",
  caty_n             = caty_n_list,
  n_over             = nA_over,
  legacy_sites       = legacy,
  legacy_stratum_var = if (!is.null(legacy)) "forest_type" else NULL,
  mindis             = mindis,
  DesignID           = "TRPA-FH-A"
)

# ---- Half B: unequal probability within structural cell ---------------------
# Remove every unit within mindis of a Half A site (legacy, primary, or backup) so no
# Half B site can sit on or overlap a Half A plot.
sitesA <- rbind(
  if (!is.null(drawA$sites_legacy) && nrow(drawA$sites_legacy)) drawA$sites_legacy[, "siteID"] else NULL,
  drawA$sites_base[, "siteID"], drawA$sites_over[, "siteID"]
)
tooClose <- lengths(st_is_within_distance(frame, sitesA, dist = mindis)) > 0
frameB <- frame[!tooClose, ]
message("Half B frame: ", nrow(frameB), " of ", nrow(frame), " units after removing Half A sites and their ", mindis, " m buffers")

set.seed(seed + 1L)
nB_base <- setNames(allocB$n_B, allocB$cell_id)
nB_over <- setNames(ceiling(allocB$n_B * (over - 1)), allocB$cell_id)

drawB <- grts(
  sframe      = frameB,
  n_base      = nB_base,
  stratum_var = "cell_id",
  seltype     = "proportional",
  aux_var     = "inclusion_weight",
  n_over      = nB_over,
  mindis      = mindis,
  DesignID    = "TRPA-FH-B"
)

# ---- Assemble ----------------------------------------------------------------
tag <- function(s, half, use) { s$half <- half; s$siteuse2 <- use; s }
sites <- rbind(
  if (!is.null(drawA$sites_legacy) && nrow(drawA$sites_legacy)) tag(drawA$sites_legacy, "A", "legacy") else NULL,
  tag(drawA$sites_base, "A", "primary"),
  tag(drawA$sites_over, "A", "backup"),
  tag(drawB$sites_base, "B", "primary"),
  tag(drawB$sites_over, "B", "backup")
)
sites$seed <- seed
dir.create("outputs", showWarnings = FALSE)
st_write(sites, "outputs/grts_split_draw.gpkg", delete_dsn = TRUE, quiet = TRUE)
message("Wrote ", nrow(sites), " sites (A primary ", nrow(drawA$sites_base),
        ", B primary ", nrow(drawB$sites_base), ") to outputs/grts_split_draw.gpkg")

# ---- Spatial balance and design effect ----------------------------------------
sbA <- sp_balance(drawA$sites_base, frame, stratum_var = "forest_type")
# realized vs expected count per balance category, Half A
catA_real <- as.data.frame(table(drawA$sites_base$forest_type, drawA$sites_base$balance_caty))
names(catA_real) <- c("forest_type", "balance_caty", "n_realized")
catA_chk <- merge(catyA, catA_real, all = TRUE)
catA_chk$n_realized[is.na(catA_chk$n_realized)] <- 0L
write.csv(catA_chk, "outputs/grts_split_catyA_check.csv", row.names = FALSE)
print(catA_chk)
sbB <- sp_balance(drawB$sites_base, frameB, stratum_var = "cell_id")
bal <- rbind(cbind(half = "A", sbA), cbind(half = "B", sbB))
write.csv(bal, "outputs/grts_split_balance.csv", row.names = FALSE)
print(bal)

# Kish design effect of the pooled primary sample from the achieved weights.
w <- c(drawA$sites_base$wgt, drawB$sites_base$wgt)
deff <- length(w) * sum(w^2) / sum(w)^2
message(sprintf("Pooled primary n = %d, Kish deff = %.3f, effective n = %.0f",
                length(w), deff, length(w) / deff))
