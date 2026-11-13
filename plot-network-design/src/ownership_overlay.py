"""Ownership shares per hexagon cell by Identity overlay.

Used by notebooks/06_tessellation.ipynb section 6b and by scripts/rerun_ownership.py. arcpy is imported
inside the function so the module can be imported without it.

Method: dissolve the parcel layer by ownership class, Identity the grid with it, then with the land
polygon, then with the TRPA boundary. Every resulting piece carries cell_key, the ownership class (blank
where no parcel), whether it is land, and whether it is inside the TRPA boundary. Sum piece areas per cell
and join the shares back to the grid. Land pieces with no parcel are "other" inside the TRPA boundary
(roads and other unparceled land) and "nodata" outside it, where the parcel layer has no coverage (the
strip inside LTBMU only). Stacked parcels can make the classes sum past 100 percent of land; those
cells are rescaled and counted.
"""
from __future__ import annotations

import pandas as pd

OWN_OTHER, OWN_NODATA, OWN_DOM = "own_other_pct", "own_nodata_pct", "own_dom"


def ownership_fields(own_map: dict) -> list:
    return [(f, "DOUBLE") for f in own_map.values()] + [(OWN_OTHER, "DOUBLE"), (OWN_NODATA, "DOUBLE"), (OWN_DOM, "TEXT", 8)]


def prepare_ownership(own_fc: str, own_field: str, work: str) -> str:
    """Dissolve the parcel layer by class. Returns the dissolved feature class path."""
    import arcpy
    out = f"{work}/ownership_dissolved"
    arcpy.management.Dissolve(own_fc, out, own_field)
    return out


def overlay_cells(grid_fc: str, own_dis: str, own_field: str, land_fc: str, trpa_fc: str, work: str, name: str) -> pd.DataFrame:
    """Identity chain: grid x ownership x land x TRPA boundary. Returns one row per piece with its area in ha."""
    import arcpy
    a = f"{work}/{name}_id_own"
    b = f"{work}/{name}_id_land"
    c = f"{work}/{name}_id_trpa"
    arcpy.analysis.Identity(grid_fc, own_dis, a, "ALL")
    arcpy.analysis.Identity(a, land_fc, b, "ONLY_FID")
    arcpy.analysis.Identity(b, trpa_fc, c, "ONLY_FID")
    # Identity names the join field FID_<identity feature class basename>. Match it exactly: the chained
    # outputs also carry FID_<intermediate class> fields, which are never -1.
    names = {f.name.upper(): f.name for f in arcpy.ListFields(c)}
    fid_land = names[f"FID_{land_fc.rsplit('/', 1)[-1]}".upper()]
    fid_trpa = names[f"FID_{trpa_fc.rsplit('/', 1)[-1]}".upper()]
    rows = []
    with arcpy.da.SearchCursor(c, ["cell_key", own_field, fid_land, fid_trpa, "SHAPE@AREA"]) as cur:
        for key, cls, fl, ft, area in cur:
            rows.append({"cell_key": key, "cls": (cls or "").strip(), "land": fl != -1, "trpa": ft != -1, "ha": area / 10_000.0})
    return pd.DataFrame(rows)


def summarize(pieces: pd.DataFrame, own_map: dict, land_ha: pd.Series | None = None) -> tuple[pd.DataFrame, int]:
    """Per cell shares of land by class. Returns (table indexed by cell_key, cells rescaled for overlap).

    land_ha is the grid's own land area per cell (geometric, from the land polygon). Without it the piece
    sum is used, which double counts land under stacked parcels and hides the overlap."""
    land = pieces[pieces.land]
    piece_land = land.groupby("cell_key")["ha"].sum()
    land_ha = piece_land if land_ha is None else land_ha.reindex(piece_land.index).fillna(piece_land)
    land_ha = land_ha[land_ha > 0]
    by_cls = land.pivot_table(index="cell_key", columns="cls", values="ha", aggfunc="sum", fill_value=0.0)
    out = pd.DataFrame(index=land_ha.index)
    known = pd.Series(0.0, index=out.index)
    for cls, field in own_map.items():
        out[field] = 100 * by_cls[cls].reindex(out.index, fill_value=0.0) / land_ha if cls in by_cls.columns else 0.0
        known += out[field]
    over = known > 100.5
    for field in own_map.values():           # stacked parcels: scale the classes to 100 and keep the ratios
        out.loc[over, field] = out.loc[over, field] * 100 / known[over]
    known = known.clip(upper=100.0)
    noparcel = land[land.cls == ""]
    nodata = 100 * noparcel[~noparcel.trpa].groupby("cell_key")["ha"].sum().reindex(out.index, fill_value=0.0) / land_ha
    out[OWN_NODATA] = nodata.clip(0, 100)
    out[OWN_OTHER] = (100 - known - out[OWN_NODATA]).clip(lower=0.0)
    cls_cols = list(own_map.values())
    out[OWN_DOM] = out[cls_cols].idxmax(axis=1).where(known > 0)
    inv = {v: k for k, v in own_map.items()}
    out[OWN_DOM] = out[OWN_DOM].map(inv)
    return out, int(over.sum())


def write_back(grid_fc: str, shares: pd.DataFrame, own_map: dict) -> None:
    """Join the shares to the grid by cell_key. Cells with no land are null."""
    import arcpy
    names = [n for n, *_ in ownership_fields(own_map)]
    with arcpy.da.UpdateCursor(grid_fc, ["cell_key", "land_ha"] + names) as cur:
        for r in cur:
            k, lh = r[0], r[1]
            if not lh or lh <= 0 or k not in shares.index:
                r[2:] = [None] * len(names)
            else:
                s = shares.loc[k]
                r[2:] = [None if pd.isna(s[n]) else (float(s[n]) if n != OWN_DOM else str(s[n])) for n in names]
            cur.updateRow(r)


def stats(grid_fc: str, own_map: dict, min_land_frac: float, over: int) -> dict:
    """Land weighted Basin shares and dominant class counts over cells with land."""
    import arcpy
    names = [n for n, *_ in ownership_fields(own_map)]
    with arcpy.da.SearchCursor(grid_fc, ["cell_key", "land_frac", "land_ha"] + names) as cur:
        o = pd.DataFrame([list(r) for r in cur], columns=["cell_key", "land_frac", "land_ha"] + names)
    o = o[o.land_frac > min_land_frac]
    w = o.land_ha / o.land_ha.sum()
    return {**{c: round(float((o[f] * w).sum()), 1) for c, f in own_map.items()},
            "other": round(float((o[OWN_OTHER] * w).sum()), 1), "nodata": round(float((o[OWN_NODATA] * w).sum()), 1),
            "cells_by_dominant": o[OWN_DOM].value_counts().to_dict(), "cells_rescaled_for_overlap": int(over),
            "cells_with_land": int(len(o))}


def run(grid_fcs: list, own_fc: str, own_field: str, own_map: dict, land_fc: str, trpa_fc: str, work: str,
        min_land_frac: float, add_fields, log=None) -> dict:
    """Whole section for a list of grids. add_fields(fc, spec) is the notebook helper."""
    own_dis = prepare_ownership(own_fc, own_field, work)
    result = {}
    for fc in grid_fcs:
        name = fc.rsplit("/", 1)[-1]
        add_fields(fc, ownership_fields(own_map))
        pieces = overlay_cells(fc, own_dis, own_field, land_fc, trpa_fc, work, name)
        import arcpy
        with arcpy.da.SearchCursor(fc, ["cell_key", "land_ha"]) as cur:
            land_ha = pd.Series({k: v for k, v in cur}, dtype=float)
        shares, over = summarize(pieces, own_map, land_ha)
        write_back(fc, shares, own_map)
        result[name] = stats(fc, own_map, min_land_frac, over)
        if log:
            log.info(f"{name}: ownership from {len(pieces):,} identity pieces; {over} cells rescaled for overlapping parcels")
    return result
