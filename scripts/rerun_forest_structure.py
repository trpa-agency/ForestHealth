"""Rerun the two forest structure standards against the F: geodatabase.

Reproduces analysis notebook cells 10, 11, 14, and 15 (stand density assessment and
summary; seral stage and canopy cover classification) with the corrected canopy class
codes and the Lodgepole Pine crosswalk, without changing the method. Writes the summary
tables to output/ and a diff against the tables that were there before.

Run from the repo root in the arcgispro-py3 environment:

    python scripts/rerun_forest_structure.py --check          verify inputs, write nothing
    python scripts/rerun_forest_structure.py                  full rerun
    python scripts/rerun_forest_structure.py --skip-density   seral only
    python scripts/rerun_forest_structure.py --skip-seral     density only

Outputs (repo):
    output/stand_density_forest_type_attainment_new.csv   cell 11 schema
    output/stand_density_status.csv                       attribute table of the assessment raster
    output/seral_stage_with_classification.csv            cell 14 schema
    output/seral_stage_basinwide.csv                      five class shares and candidate attainment figures
    output/rerun_diff_<date>.md                           old versus new, side by side
    logs/rerun_forest_structure_<date>.log

Outputs (geodatabase, overwritten, same names the notebook uses):
    stand_density_threshold_assessment, seral_canopy_veg_classification, seral_tabulation

Then run scripts/build_forest_structure_charts.py to regenerate the HTML.
"""

import argparse
import datetime as dt
import logging
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
M2_TO_ACRES = 1 / 4046.8564224

log = logging.getLogger("rerun")


# ----------------------------------------------------------------------------- setup
def load_config() -> dict:
    with open(ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_logging(log_dir: Path, stamp: str) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"rerun_forest_structure_{stamp}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(path, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
    )
    return path


def import_arcpy(gdb: str):
    """arcpy takes over a minute to import here; do it once and report the time."""
    t0 = dt.datetime.now()
    log.info("importing arcpy")
    import arcpy  # noqa: WPS433

    arcpy.CheckOutExtension("Spatial")
    arcpy.env.workspace = gdb
    arcpy.env.overwriteOutput = True
    log.info("arcpy %s ready in %.0f s, workspace %s", arcpy.GetInstallInfo()["Version"], (dt.datetime.now() - t0).total_seconds(), gdb)
    return arcpy


# ----------------------------------------------------------------------------- helpers
def rat_to_df(arcpy, raster: str) -> pd.DataFrame:
    fields = [f.name for f in arcpy.ListFields(raster)]
    with arcpy.da.SearchCursor(raster, fields) as cur:
        return pd.DataFrame([list(r) for r in cur], columns=fields)


def cell_acres(arcpy, raster: str) -> float:
    size = float(arcpy.GetRasterProperties_management(raster, "CELLSIZEX").getOutput(0))
    return size * size * M2_TO_ACRES


def build_forest_type_raster(arcpy, veg_raster: str, veg_map: dict):
    from arcpy.sa import Raster, Reclassify, RemapValue

    remap = RemapValue([[k, v] for k, v in veg_map.items()])
    return Reclassify(Raster(veg_raster), "WHRTYPE", remap, "NODATA")


def add_acres(arcpy, raster) -> None:
    """Mirror utils.add_acres: Count times acres per 30 m cell."""
    arcpy.management.AddField(raster, "Acres", "DOUBLE", 18, 11)
    arcpy.management.CalculateField(raster, "Acres", "!Count! * 0.222395", "PYTHON3")


# ----------------------------------------------------------------------------- check
def check_inputs(arcpy, cfg: dict) -> bool:
    ok = True
    for key, name in cfg["rasters"].items():
        exists = arcpy.Exists(name)
        log.info("%-22s %-45s %s", key, name, "ok" if exists else "MISSING")
        if key in ("veg_type", "seral_stage", "canopy_cover", "stand_density", "basal_area") and not exists:
            ok = False
    if not ok:
        return False

    veg = rat_to_df(arcpy, cfg["rasters"]["veg_type"])
    acres_per_cell = cell_acres(arcpy, cfg["rasters"]["veg_type"])
    veg["acres"] = veg["Count"] * acres_per_cell
    veg["code"] = veg["WHRTYPE"].map(cfg["forest_types"]["veg_map"])
    frame = veg.dropna(subset=["code"]).groupby("code")["acres"].sum()
    log.info("frame acres from the veg type raster attribute table versus report Table 1:")
    for code, name in cfg["forest_types"]["names"].items():
        log.info("  %-24s %9.0f  report %7d", name, frame.get(code, 0), cfg["forest_types"]["report_acres"][code])
    log.info("  %-24s %9.0f  report %7d", "total", frame.sum(), sum(cfg["forest_types"]["report_acres"].values()))
    for key in ("seral_stage", "canopy_cover", "stand_density", "basal_area"):
        name = cfg["rasters"][key]
        d = arcpy.Describe(name)
        log.info("%-14s %s  cell %.0f m  %s", key, d.spatialReference.name, d.meanCellWidth, d.extent)
    return True


# ----------------------------------------------------------------------------- density
def assess_density(arcpy, cfg: dict, forest_type_r):
    """Cell 10. Output raster: 1 exceeds a target (out of attainment), 0 at or below both (in)."""
    from arcpy.sa import Con, Int, Raster, SetNull

    r = cfg["rasters"]
    seral_r = Raster(r["seral_stage"])
    tpa_r = Raster(r["stand_density"])
    ba_r = Raster(r["basal_area"])

    out = Int(-1)
    for ftype, stages in cfg["stand_density"]["targets"].items():
        for stage, (max_tpa, max_ba) in stages.items():
            over = (forest_type_r == ftype) & (seral_r == stage) & (tpa_r >= max_tpa) & (ba_r >= max_ba)
            under = (forest_type_r == ftype) & (seral_r == stage) & ~over
            out = Con(over, 1, out)
            out = Con(under, 0, out)
            log.info("density type %s stage %s max TPA %s max BA %s", ftype, stage, max_tpa, max_ba)
    out = SetNull(out == -1, out)

    name = r["density_assessment"]
    if arcpy.Exists(name):
        arcpy.management.Delete(name)
    out.save(name)
    arcpy.BuildRasterAttributeTable_management(out, "Overwrite")
    add_acres(arcpy, out)
    arcpy.AddField_management(out, "Attainment", "SHORT")
    arcpy.CalculateField_management(out, "Attainment", "!VALUE!", "PYTHON3")
    out.save(name)
    log.info("saved %s", name)
    return Raster(name)


def summarize_density(arcpy, cfg: dict, forest_type_r, assessment_r) -> pd.DataFrame:
    """Cell 11. Acres meeting the target per forest type and seral stage."""
    from arcpy.sa import Con, Raster, ZonalStatistics

    seral_r = Raster(cfg["rasters"]["seral_stage"])
    acres_per_cell = cell_acres(arcpy, cfg["rasters"]["veg_type"])
    names = cfg["forest_types"]["names"]
    stages = {1: "Early", 2: "Mid", 3: "Late"}
    rows = []
    for ftype in names:
        for stage in stages:
            combo = (forest_type_r == ftype) & (seral_r == stage)
            total_r = Con(combo, 1)
            total = ZonalStatistics(total_r, "Value", total_r, "SUM", "DATA").maximum or 0
            att_r = Con(combo & (assessment_r == 0), 1)
            att = ZonalStatistics(att_r, "Value", att_r, "SUM", "DATA").maximum or 0
            total_ac, att_ac = total * acres_per_cell, att * acres_per_cell
            rows.append(
                {
                    "Forest Type": names[ftype],
                    "Seral Stage": stages[stage],
                    "Total Acres": round(total_ac, 2),
                    "Acres Meeting Threshold": round(att_ac, 2),
                    "Percent Meeting Threshold": round(att_ac / total_ac * 100, 2) if total_ac else 0,
                }
            )
            log.info("density %-24s %-5s total %9.0f meeting %9.0f", names[ftype], stages[stage], total_ac, att_ac)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- seral
def classify_seral(arcpy, cfg: dict, forest_type_r) -> pd.DataFrame:
    """Cell 15 with the cell 14 output schema.

    canopy class: 1 closed (cover at or above the cutoff for the type), 0 open.
    combined class codes: 1 early, 2 mid closed, 3 mid open, 4 late open, 5 late closed.
    These match seral_canopy.class_names and the keys of seral_canopy.desired_pct.
    """
    from arcpy.sa import Con, IsNull, Raster, TabulateArea

    r, sc = cfg["rasters"], cfg["seral_canopy"]
    cut = sc["closed_cutoff_pct"]
    seral_r = Raster(r["seral_stage"])
    cover_r = Con(IsNull(Raster(r["canopy_cover"])), 0, Raster(r["canopy_cover"]))

    closed_r = Con(forest_type_r == 1, Con(cover_r >= cut[1], 1, 0),
               Con(forest_type_r == 2, Con(cover_r >= cut[2], 1, 0),
                                       Con(cover_r >= cut[3], 1, 0)))
    closed_r = Con(IsNull(closed_r), 0, closed_r)

    combined_r = Con(seral_r == 1, 1,
                 Con((seral_r == 2) & (closed_r == 1), 2,
                 Con((seral_r == 2) & (closed_r == 0), 3,
                 Con((seral_r == 3) & (closed_r == 0), 4,
                 Con((seral_r == 3) & (closed_r == 1), 5, None)))))

    # One integer raster: type * 100 + class * 10 + canopy, with a labeled attribute table.
    coded_r = (forest_type_r * 100) + (combined_r * 10) + closed_r
    out = r["seral_classification"]
    coded_r.save(out)
    arcpy.BuildRasterAttributeTable_management(out, "Overwrite")
    existing = {f.name for f in arcpy.ListFields(out)}
    for field in ("VEG_TYPE", "SERAL_STAGE", "CANOPY_CLASS"):
        if field not in existing:
            arcpy.AddField_management(out, field, "TEXT", field_length=50)
    names, class_names = cfg["forest_types"]["names"], sc["class_names"]
    with arcpy.da.UpdateCursor(out, ["Value", "VEG_TYPE", "SERAL_STAGE", "CANOPY_CLASS"]) as cur:
        for row in cur:
            code = row[0]
            row[1] = names.get(code // 100, "Unknown")
            row[2] = class_names.get((code % 100) // 10, "Unknown")
            row[3] = {0: "Open Canopy", 1: "Closed Canopy"}.get(code % 10, "Unknown")
            cur.updateRow(row)
    log.info("saved %s", out)

    tab = r["seral_tabulation"]
    TabulateArea(forest_type_r, "Value", combined_r, "Value", tab, forest_type_r.meanCellWidth)
    fields = [f.name for f in arcpy.ListFields(tab) if f.name.startswith("VALUE_")]
    counts = {}
    with arcpy.da.SearchCursor(tab, ["Value"] + fields) as cur:
        for row in cur:
            counts[row[0]] = list(row[1:])

    rows = []
    for ftype, targets in sc["desired_pct"].items():
        areas = counts.get(ftype, [0] * len(fields))  # TabulateArea returns area in m2
        total_m2 = sum(areas)
        total_ac = total_m2 * M2_TO_ACRES
        for i, field in enumerate(fields):
            code = int(field.replace("VALUE_", ""))
            area_m2 = areas[i]
            area_ac = area_m2 * M2_TO_ACRES
            pct = round(area_m2 / total_m2 * 100, 2) if total_m2 else 0
            lo, hi = targets.get(code, (0, 0))
            lo_ac, hi_ac = total_ac * lo / 100, total_ac * hi / 100
            if area_ac < lo_ac:
                status, gap = "Underrepresented", round(lo_ac - area_ac, 2)
            elif area_ac > hi_ac:
                status, gap = "Overrepresented", round(hi_ac - area_ac, 2)
            else:
                status, gap = "Within", 0
            rows.append(
                {
                    "Forest Type": names[ftype],
                    "Seral Stage": class_names[code],
                    "Desired % Range": f"{lo}–{hi}%",
                    "Classification": status,
                    "Current Area %": pct,
                    "Area (m²)": round(area_m2, 0),
                    "Area (acres)": round(area_ac, 2),
                    "Total Area of Type (acres)": round(total_ac, 2),
                    "Acres from Target": gap,
                    "_code": code,
                    "_lo": lo,
                    "_hi": hi,
                }
            )
            log.info("seral %-24s %-20s %6.2f%%  %s", names[ftype], class_names[code], pct, status)
    return pd.DataFrame(rows)


def basinwide_seral(cfg: dict, df: pd.DataFrame) -> pd.DataFrame:
    """Five class shares of the assessed frame plus two candidate attainment figures.

    The report publishes 70,836 acres within desired ranges (61 percent of 115,396). The
    repo has never documented how that figure was computed, so two candidates are written:
      within_class_acres   acres in classes whose share is inside the range (the CSV's Within rows)
      not_in_excess_acres  per class, min(area, upper bound); everything not above the range
    Whichever lands near 70,836 is the report's definition.
    """
    total = df["Area (acres)"].sum()
    shares = df.groupby("Seral Stage")["Area (acres)"].sum().reindex(cfg["seral_canopy"]["class_names"].values())
    out = pd.DataFrame({"metric": [f"share_{k}" for k in shares.index], "acres": shares.values})
    out["percent_of_frame"] = out["acres"] / total * 100
    within = df.loc[df["Classification"] == "Within", "Area (acres)"].sum()
    not_excess = (df["Area (acres)"].clip(upper=df["Total Area of Type (acres)"] * df["_hi"] / 100)).sum()
    extra = pd.DataFrame(
        {
            "metric": ["assessed_acres", "within_class_acres", "not_in_excess_acres", "report_within_acres"],
            "acres": [total, within, not_excess, cfg["seral_canopy"]["report_within_acres"]],
        }
    )
    extra["percent_of_frame"] = extra["acres"] / total * 100
    return pd.concat([out, extra], ignore_index=True).round(2)


# ----------------------------------------------------------------------------- diff
def read_old(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.exists() else None


def md(df: pd.DataFrame) -> str:
    """Markdown table; falls back to a fenced text table when tabulate is not installed."""
    try:
        return df.to_markdown(index=False)
    except ImportError:
        return "```\n" + df.to_string(index=False) + "\n```"


def write_diff(path: Path, density_old, density_new, seral_old, seral_new, basin) -> None:
    lines = [f"# Rerun diff, {dt.date.today().isoformat()}", ""]
    lines += ["Type 2 was labeled White Fir before this run and Sierran Mixed Conifer after; rows are matched on that.", ""]
    rename = {"White Fir": "Sierran Mixed Conifer"}
    if density_new is not None:
        lines += ["## Stand density", ""]
        if density_old is not None:
            o = density_old.replace({"Forest Type": rename})
            m = o.merge(density_new, on=["Forest Type", "Seral Stage"], suffixes=(" old", " new"), how="outer")
            cols = ["Forest Type", "Seral Stage", "Total Acres old", "Total Acres new",
                    "Acres Meeting Threshold old", "Acres Meeting Threshold new",
                    "Percent Meeting Threshold old", "Percent Meeting Threshold new"]
            lines += [md(m[cols]), ""]
            for label, d in (("old", o), ("new", density_new)):
                t, a = d["Total Acres"].sum(), d["Acres Meeting Threshold"].sum()
                lines.append(f"- basin {label}: {a:,.0f} of {t:,.0f} acres meeting, {a / t * 100:.1f} percent")
        else:
            lines += [md(density_new)]
        lines.append("")
    if seral_new is not None:
        lines += ["## Seral stage and canopy cover", "",
                  "Old mid and late labels were transposed (an old 'closed' row holds open pixels), so a label-matched row is not the same population. Compare the class shares, not the rows.", ""]
        keep = ["Forest Type", "Seral Stage", "Desired % Range", "Classification", "Current Area %", "Area (acres)", "Acres from Target"]
        if seral_old is not None:
            o = seral_old.replace({"Forest Type": rename})[keep]
            m = o.merge(seral_new[keep], on=["Forest Type", "Seral Stage", "Desired % Range"], suffixes=(" old", " new"), how="outer")
            lines += [md(m), ""]
        else:
            lines += [md(seral_new[keep]), ""]
        lines += ["### Basin-wide", "", md(basin), ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    log.info("diff written to %s", path)


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="verify inputs and write nothing")
    ap.add_argument("--skip-density", action="store_true")
    ap.add_argument("--skip-seral", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    setup_logging(ROOT / cfg["paths"]["logs"], stamp)
    out_dir = ROOT / cfg["paths"]["output"]
    out_dir.mkdir(exist_ok=True)

    arcpy = import_arcpy(cfg["paths"]["gdb"])
    if not check_inputs(arcpy, cfg):
        log.error("inputs missing, stopping")
        return 2
    if args.check:
        log.info("check only, nothing written")
        return 0

    forest_type_r = build_forest_type_raster(arcpy, cfg["rasters"]["veg_type"], cfg["forest_types"]["veg_map"])

    density_path = out_dir / "stand_density_forest_type_attainment_new.csv"
    seral_path = out_dir / "seral_stage_with_classification.csv"
    density_old, seral_old = read_old(density_path), read_old(seral_path)
    density_new = seral_new = basin = None

    if not args.skip_density:
        assessment_r = assess_density(arcpy, cfg, forest_type_r)
        density_new = summarize_density(arcpy, cfg, forest_type_r, assessment_r)
        density_new.to_csv(density_path, index=False)
        status = rat_to_df(arcpy, cfg["rasters"]["density_assessment"])
        status.to_csv(out_dir / "stand_density_status.csv", index=False)
        log.info("wrote %s and stand_density_status.csv", density_path.name)

    if not args.skip_seral:
        df = classify_seral(arcpy, cfg, forest_type_r)
        basin = basinwide_seral(cfg, df)
        seral_new = df.drop(columns=["_code", "_lo", "_hi"])
        seral_new.to_csv(seral_path, index=False)
        basin.to_csv(out_dir / "seral_stage_basinwide.csv", index=False)
        log.info("wrote %s and seral_stage_basinwide.csv", seral_path.name)
        log.info("basin-wide:\n%s", basin.to_string(index=False))

    write_diff(out_dir / f"rerun_diff_{stamp[:8]}.md", density_old, density_new, seral_old, seral_new, basin)
    log.info("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
