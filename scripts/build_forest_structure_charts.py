"""Regenerate the forest structure HTML from the CSVs in output/.

No arcpy. Run after scripts/rerun_forest_structure.py, from the repo root, in any
environment with pandas, plotly, and pyyaml:

    python scripts/build_forest_structure_charts.py

Writes (DataVisualizations/):
    CompositionAge_Chart.html                       Results cell 24, verbatim. LIVE in the
                                                    Seral Stage and Canopy Cover StoryMap.
    StandDensity_Chart_ForestType_PercentTarget.html Results cell 15, verbatim
    StandDensity_Chart_SNRRK.html                   Results cell 12, verbatim
    CompositionAge_Table_Updated.html               AG Grid table, rows from the seral CSV
    Composition_Action_Table.html                   AG Grid table, acres to target by type

Check CompositionAge_Chart.html in a browser before committing: the StoryMap serves it
straight from GitHub Pages with no review step.
"""

import json
import logging
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import yaml

ROOT = Path(__file__).resolve().parents[1]
log = logging.getLogger("charts")


def load_config() -> dict:
    with open(ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def layout(fig, cfg: dict, title: str, x_title: str, y_title: str, showlegend: bool) -> None:
    """The shared update_layout block every Results chart uses."""
    c = cfg["charts"]
    fig.update_layout(
        title_x=0.5, title_font_size=20, uniformtext_minsize=8, uniformtext_mode="hide",
        title_font_color=c["title_color"], xaxis_title=x_title, yaxis_title=y_title,
        hovermode="x unified", template=c["template"],
        legend=dict(title_text="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        legend_title_text="", font_family=c["font"], font_color=c["title_color"],
        plot_bgcolor="white", showlegend=showlegend,
    )
    fig.update_layout(title_text=title)


def write(fig, path: Path) -> None:
    fig.write_html(config={"displayModeBar": False}, file=str(path), full_html=False, include_plotlyjs="cdn")
    log.info("wrote %s (%.0f KB)", path.name, path.stat().st_size / 1024)


# ----------------------------------------------------------------------------- charts
def composition_age_chart(cfg: dict, seral: pd.DataFrame, out: Path) -> None:
    """Results cell 24: stacked bar of seral stage by canopy class, basin-wide."""
    df = seral.rename(columns={"Seral Stage": "Category", "Area (acres)": "Acres"})
    df["SeralStage"] = df["Category"].replace(
        {"Early": "Early Seral", "Mid (closed canopy)": "Mid Seral", "Mid (open canopy)": "Mid Seral",
         "Late (open canopy)": "Late Seral", "Late (closed canopy)": "Late Seral"}
    )
    df = df.melt(id_vars=["SeralStage", "Category"], value_vars=["Acres"])
    df = df.groupby(["SeralStage", "Category"]).sum(numeric_only=True).reset_index()
    df = df.rename(columns={"value": "Acres"})
    df["SeralStage"] = pd.Categorical(df["SeralStage"], categories=["Early Seral", "Mid Seral", "Late Seral"], ordered=True)
    df["Percentage"] = (df["Acres"] / df["Acres"].sum() * 100).round(1)

    fig = px.bar(
        df, x="SeralStage", y="Acres", color="Category", text=df["Percentage"].astype(str) + "%",
        title="Seral Stage by Canopy Cover Class", color_discrete_sequence=["#ABCD66", "#728944"],
        custom_data=["Category"], category_orders={"SeralStage": ["Early Seral", "Mid Seral", "Late Seral"]},
    )
    fig.update_traces(
        marker_line_color="rgb(8,48,107)", marker_line_width=0.1, opacity=0.9, textfont_size=14, textposition="inside",
        hovertemplate="<br>".join(["<b>%{y:,.0f}</b> acres of the forested area is", "in class <i>%{customdata[0]}</i>"]) + "<extra></extra>",
    )
    layout(fig, cfg, "Seral Stage by Canopy Cover Class", "Seral Stage", "Acres", showlegend=True)
    fig.update_traces(showlegend=False)
    write(fig, out / "CompositionAge_Chart.html")


def density_by_type_chart(cfg: dict, density: pd.DataFrame, out: Path) -> None:
    """Results cell 15: grouped bar of percent meeting the density target by type and stage."""
    df = density
    fig = px.bar(
        df, x="Forest Type", y="Percent Meeting Threshold", color="Seral Stage",
        color_discrete_sequence=["#DEDE58", "#A2BC6E", "#728944"], custom_data=["Seral Stage"], barmode="group",
        title="% of Area Meeting Stand Density Targets", labels={"Percent Meeting Threshold": "% Meeting Threshold"},
    )
    fig.update_traces(
        marker_line_color="rgb(8,48,107)", marker_line_width=0.1, opacity=0.9, textfont_size=14, textposition="inside",
        hovertemplate="<br>".join(["<b>%{y:,.0f}%</b> of the", "<i>%{customdata[0]} Seral</i>"]) + "<extra></extra>",
    )
    layout(fig, cfg, "% of Area Meeting Stand Density Targets", "Forest Type & Seral Stage", "% Meeting Target", showlegend=True)
    fig.for_each_trace(lambda t: t.update(text=[f"{y:.0f}%" for y in t.y], textposition="auto"))
    fig.update_xaxes(tickangle=0, tickmode="array", tickvals=df["Forest Type"], ticktext=df["Forest Type"])
    write(fig, out / "StandDensity_Chart_ForestType_PercentTarget.html")


def density_status_chart(cfg: dict, status: pd.DataFrame, out: Path) -> None:
    """Results cell 12: within versus outside desired conditions, basin-wide."""
    df = status.copy()
    df["TargetStatus"] = df["Value"].map({0: "Within Desired Conditions", 1: "Outside Desired Conditions", -1: "N/A"})
    df = df.groupby("TargetStatus")["Acres"].sum().reset_index()
    df["Percentage"] = (df["Acres"] / df["Acres"].sum() * 100).round(1)
    fig = px.bar(
        df, x="TargetStatus", y="Acres", text=df["Percentage"].astype(str) + "%", title="Stand Density",
        color_discrete_sequence=["#ABCD66", "#728944"], custom_data=["TargetStatus"],
    )
    fig.update_traces(
        marker_line_color="rgb(8,48,107)", marker_line_width=0.1, opacity=0.9, textfont_size=14, textposition="inside",
        hovertemplate="<br>".join(["<b>%{y:,.0f} acres</b> of the forested area are", "<i>%{customdata[0]}</i> for resilience"]) + "<extra></extra>",
    )
    layout(fig, cfg, "Stand Density", "Stand Density - SNRRK", "Acres", showlegend=True)
    fig.update_traces(showlegend=False)
    write(fig, out / "StandDensity_Chart_SNRRK.html")


# ----------------------------------------------------------------------------- tables
AG_GRID_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{title}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-community/styles/core.css" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/ag-grid-community/styles/theme-alpine.css" />
  <script src="https://cdn.jsdelivr.net/npm/ag-grid-community/dist/ag-grid-community.min.js"></script>
  <style>
    html, body, #myGrid {{ height: 100%; width: 100%; margin: 0; padding: 0; }}
  </style>
</head>
<body>
  <div id="myGrid" class="ag-theme-alpine"></div>
"""

AG_GRID_TAIL = """
    const gridOptions = {{
      columnDefs,
      rowData,
      defaultColDef: {{ resizable: true, sortable: true, filter: true }}
    }};
    document.addEventListener("DOMContentLoaded", function () {{
      agGrid.createGrid(document.querySelector("#myGrid"), gridOptions);
    }});
  </script>
</body>
</html>
"""


def composition_table(seral: pd.DataFrame, out: Path) -> None:
    cols = ["Forest Type", "Seral Stage", "Desired % Range", "Classification", "Current Area %",
            "Area (acres)", "Total Area of Type (acres)", "Acres from Target"]
    rows = json.dumps(seral[cols].to_dict(orient="records"), ensure_ascii=False, indent=2)
    body = f"""  <div id="controls"><button onclick="onBtnExport()">Download CSV</button></div>
  <script>
    const rawData = {rows};
    const rowData = rawData.map((row, i, arr) => {{
      const showForest = i === 0 || row["Forest Type"] !== arr[i - 1]["Forest Type"];
      return {{ ...row, showForest }};
    }});
    const columnDefs = [
      {{ headerName: "Forest Type", field: "Forest Type", cellRenderer: (p) => p.data.showForest ? p.value : '' }},
      {{ headerName: "Seral Stage", field: "Seral Stage" }},
      {{ headerName: "Desired % Range", field: "Desired % Range" }},
      {{ headerName: "Classification", field: "Classification" }},
      {{ headerName: "Current Area %", field: "Current Area %", valueFormatter: (p) => `${{p.value.toFixed(2)}}%` }},
      {{ headerName: "Area (acres)", field: "Area (acres)", valueFormatter: (p) => Math.round(p.value).toLocaleString() }},
      {{ headerName: "Total Forest Area (acres)", field: "Total Area of Type (acres)", valueFormatter: (p) => Math.round(p.value).toLocaleString() }},
      {{ headerName: "Acres From Target", field: "Acres from Target",
        valueFormatter: (p) => {{ const v = Math.round(p.value); return `${{v > 0 ? '+' : ''}}${{v.toLocaleString()}}`; }} }}
    ];
    function onBtnExport() {{ gridOptions.api.exportDataAsCsv({{ fileName: 'composition_age_targets.csv' }}); }}
"""
    html = AG_GRID_HEAD.format(title="Forest Composition Table") + body + AG_GRID_TAIL.format()
    path = out / "CompositionAge_Table_Updated.html"
    path.write_text(html, encoding="utf-8")
    log.info("wrote %s", path.name)


def action_table(seral: pd.DataFrame, out: Path) -> None:
    """Acres to move per forest type, using the rule the old table used.

    Old columns were "Move Canopy from Closed to Open", "Move to Early Seral", "Grow into
    Late Seral". The numbers behind them were: total excess above the upper bound across
    all mid and late classes; the early seral deficit; the total deficit across mid and
    late classes. With the canopy fix the excess is no longer only in closed classes, so
    the headers now say what the columns are.
    """
    df = seral.copy()
    df["gap"] = df["Acres from Target"]
    is_early = df["Seral Stage"] == "Early"
    rows = []
    for ftype, g in df.groupby("Forest Type", sort=False):
        excess = -g.loc[g["gap"] < 0, "gap"].sum()
        early = g.loc[is_early & (g["gap"] > 0), "gap"].sum()
        later = g.loc[~is_early & (g["gap"] > 0), "gap"].sum()
        rows.append({"forestType": ftype, "excess": round(excess, 2), "earlySeral": round(early, 2),
                     "lateSeral": round(later, 2), "total": round(excess + early + later, 2)})
    rows.append({"forestType": "Total", **{k: round(sum(r[k] for r in rows), 2) for k in ("excess", "earlySeral", "lateSeral", "total")}})
    body = f"""  <script>
    const columnDefs = [
      {{ headerName: "Forest Type", field: "forestType", pinned: "left" }},
      {{ headerName: "Acres Above Desired Range", field: "excess", type: 'numericColumn', valueFormatter: fmt }},
      {{ headerName: "Early Seral Deficit", field: "earlySeral", type: 'numericColumn', valueFormatter: fmt }},
      {{ headerName: "Mid and Late Seral Deficit", field: "lateSeral", type: 'numericColumn', valueFormatter: fmt }},
      {{ headerName: "Total Acres to Target", field: "total", type: 'numericColumn', valueFormatter: fmt }},
    ];
    const rowData = {json.dumps(rows, indent=2)};
    function fmt(p) {{ return p.value.toLocaleString(undefined, {{ minimumFractionDigits: 0, maximumFractionDigits: 0 }}); }}
"""
    html = AG_GRID_HEAD.format(title="Forest Composition Actions Table") + body + AG_GRID_TAIL.format()
    path = out / "Composition_Action_Table.html"
    path.write_text(html, encoding="utf-8")
    log.info("wrote %s", path.name)


# ----------------------------------------------------------------------------- main
def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="write HTML here instead of DataVisualizations/ (for a dry run)")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg = load_config()
    out_dir, vis = ROOT / cfg["paths"]["output"], ROOT / cfg["paths"]["datavis"]
    if args.out:
        vis = Path(args.out)
        vis.mkdir(parents=True, exist_ok=True)
    seral = pd.read_csv(out_dir / "seral_stage_with_classification.csv")
    density = pd.read_csv(out_dir / "stand_density_forest_type_attainment_new.csv")

    composition_age_chart(cfg, seral, vis)
    composition_table(seral, vis)
    action_table(seral, vis)
    density_by_type_chart(cfg, density, vis)
    status_path = out_dir / "stand_density_status.csv"
    if status_path.exists():
        density_status_chart(cfg, pd.read_csv(status_path), vis)
    else:
        log.warning("%s not found, StandDensity_Chart_SNRRK.html not rebuilt (run the rerun first)", status_path.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
