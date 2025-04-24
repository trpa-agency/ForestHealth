# imports
import arcpy
from arcpy.sa import *
from arcpy.ia import *
from arcpy.ddd import *
import pandas as pd
from pathlib import Path
import plotly.express as px
# functions
# function to classify raw raster into desired condition categories based on 90th and 10th percentile value comaprison 
def raster_categorize(input_raster, upper_raster, lower_raster, output_raster_name):
    input_raster_obj = Raster(input_raster)
    lower_raster_obj = Raster(lower_raster)
    upper_raster_obj = Raster(upper_raster)
    output_raster_obj = Con(input_raster_obj < lower_raster_obj, -1,
                        Con(input_raster_obj > upper_raster_obj, 1, 0))
    output_raster_obj.save(output_raster_name)

# calculate new field - acres
def add_acres(inFeatures):
    fieldName2 = "Acres"
    fieldPrecision = 18
    fieldScale = 11
    arcpy.management.AddField(inFeatures, fieldName2, "DOUBLE", fieldPrecision, fieldScale)
    arcpy.management.CalculateField(inFeatures, fieldName2,"!Count! * 0.222395", "PYTHON3")

# calculate category field for desire condition - target, low, high
def add_category(inFeatures, lookup_dict):
    arcpy.AddField_management(inFeatures, "Category", "TEXT")
    cursor =None
    with arcpy.da.UpdateCursor(inFeatures, ["Value", "Category"]) as cursor:
        for row in cursor:
            if row[0] in lookup_dict:
                row[1] = lookup_dict[row[0]]
            cursor.updateRow(row)

# function to reclassify fire severity raster
def reclassify_fire_severity(input_path, output_name):
    from arcpy.sa import Raster, Reclassify, RemapRange
    raster = Raster(str(input_path))
    out_reclass = Reclassify(raster, "Value", RemapRange([[0, 0.6, 0], [0.6, 1, 1]]))
    out_reclass.save(output_name)

# function to extract raster by mask to tahoe extent
def extract_by_mask_to_tahoe_extent(in_raster, output_name):
    out_raster = ExtractByMask(
        in_raster=in_raster,
        in_mask_data=r"F:\GIS\DB_CONNECT\Vector.sde\sde.SDE.Jurisdictions\sde.SDE.TRPA_bdy",
        extraction_area="INSIDE",
        analysis_extent='-214749.813147473 -338358.008101731 228897.27559438 457005.517540967 PROJCS["NAD_1983_California_Teale_Albers",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Albers"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",-4000000.0],PARAMETER["Central_Meridian",-120.0],PARAMETER["Standard_Parallel_1",34.0],PARAMETER["Standard_Parallel_2",40.5],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]'
    )
    out_raster.save(output_name)


# fucntion to add attribute table. add acres, and add category
def add_acres_category(raster, lookup_dict):
    # build an attribute table
    arcpy.BuildRasterAttributeTable_management(raster, "Overwrite")
    # calc Acres field
    add_acres(raster)
    # add and calc category field
    add_category(raster, lookup_dict)

# function to convert raster attribute table to pandas dataframe
def get_raster_attribute_table_as_dataframe(raster):
    fields = [f.name for f in arcpy.ListFields(raster)]
    cursor = arcpy.da.SearchCursor(raster, fields)
    data = [row for row in cursor]
    return pd.DataFrame(data, columns=fields)
    
# add acres to zonal stats tables that use 30x30 m cell size
def add_acres_to_table(table):
    arcpy.management.AddField(table, "Acres", "DOUBLE")
    # calculate the acres from 30x30 m cell size in count of cells COUNT
    arcpy.management.CalculateField(table, "Acres", "!SUM! * 0.2223948", "PYTHON3")

# calculate zonal stats for raster in each management area
def calculate_zonal_stats(mgmt_areas, zone_field, raster, zonal_stats):
    zones  = arcpy.MakeFeatureLayer_management(str(mgmt_areas))
    raster = Raster(raster)
    # zonal stats as table to get acres of high fire severity in each management area
    ZonalStatisticsAsTable(
        in_zone_data=zones,
        zone_field=zone_field,
        in_value_raster=raster,
        out_table=zonal_stats,
        statistics_type="SUM"
    )
    add_acres_to_table(zonal_stats)

# raster to dataframe function
def raster_to_df(raster_path, band=1):
    """Convert raster to dataframe."""
    # read raster
    raster = arcpy.Raster(str(raster_path))
    # check if band is valid
    if band > raster.bandCount:
        raise ValueError(f"Band {band} does not exist in raster {raster_path}.")
    # convert to numpy array
    arr = arcpy.RasterToNumPyArray(raster, band=band)
    # get raster properties
    cell_size = raster.meanCellHeight
    extent = raster.extent
    # get raster properties
    cols = raster.width
    rows = raster.height
    # create a dataframe
    df = pd.DataFrame(arr, columns=[f"Band_{band}"])
    # add cell size and extent to dataframe
    df["CellSize"] = cell_size
    df["Extent"] = extent
    df["Rows"] = rows
    df["Cols"] = cols
    return df


## From CR DASHBOARD ##

# Gets spatially enabled dataframe from TRPA server
def get_fs_data_spatial(service_url):
    feature_layer = FeatureLayer(service_url)
    query_result = feature_layer.query().sdf
    return query_result

# Gets data from the TRPA server
def get_fs_data(service_url):
    feature_layer = FeatureLayer(service_url)
    query_result = feature_layer.query()
    # Convert the query result to a list of dictionaries
    feature_list = query_result.features
    # Create a pandas DataFrame from the list of dictionaries
    all_data = pd.DataFrame([feature.attributes for feature in feature_list])
    # return data frame
    return all_data

# Stacked Percent Bar chart
def stackedbar(
    df,
    path_html,
    div_id,
    x,
    y,
    color,
    color_sequence,
    orders,
    y_title,
    x_title,
    custom_data,
    hovertemplate,
    hovermode,
    format,
    name=None,
    additional_formatting=None,
    orientation=None,
    facet=None,
    facet_row=None,
):
    config = {"displayModeBar": False}
    fig = px.bar(
        df,
        x=x,
        y=y,
        color=color,
        barmode="stack",
        facet_col=facet,
        facet_row=facet_row,
        color_discrete_sequence=color_sequence,
        category_orders=orders,
        orientation=orientation,
        custom_data=custom_data,
    )

    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    fig.update_layout(
        yaxis=dict(tickformat=format, hoverformat=format, title=y_title),
        xaxis=dict(title=x_title),
        hovermode=hovermode,
        template="plotly_white",
        dragmode=False,
        legend_title=None,
    )
    fig.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True, tickformat=format))
    # fig.for_each_yaxis(lambda yaxis: yaxis.update(tickfont = dict(color = 'rgba(0,0,0,0)')), secondary_y=True)
    fig.update_yaxes(
        col=2, row=1, showticklabels=False, tickfont=dict(color="rgba(0,0,0,0)"), title=None
    )
    fig.update_yaxes(
        col=3, row=1, showticklabels=False, tickfont=dict(color="rgba(0,0,0,0)"), title=None
    )
    fig.update_xaxes(tickformat=".0f")
    fig.update_traces(hovertemplate=hovertemplate)
    fig.update_layout(additional_formatting)

    fig.write_html(
        config=config,
        file=path_html,
        include_plotlyjs="directory",
        div_id=div_id,
    )

# natural_systems.py
def get_data_forest_fuel():
    eipForestTreatments = "https://www.laketahoeinfo.org/WebServices/GetReportedEIPIndicatorProjectAccomplishments/JSON/e17aeb86-85e3-4260-83fd-a2b32501c476/19"
    data = pd.read_json(eipForestTreatments)
    df = data[data["PMSubcategoryName1"] == "Treatment Zone"]
    df = df.rename(
        columns={
            "IndicatorProjectYear": "Year",
            "PMSubcategoryOption1": "Treatment Zone",
            "IndicatorProjectValue": "Acres",
        }
    )
    # change value Community Defense Zone to Defense Zone for consistency
    df["Treatment Zone"] = df["Treatment Zone"].replace("Community Defense Zone", "Defense Zone")
    df["Year"] = df["Year"].astype(str)
    df = df.groupby(["Year", "Treatment Zone"]).agg({"Acres": "sum"}).reset_index()
    return df


def plot_forest_fuel(df):
    stackedbar(
        df,
        path_html="DataVisualizations\FuelTreatment_Chart.html",
        div_id="ForestFuelsTreatement_Chart",
        x="Year",
        y="Acres",
        facet=None,
        color="Treatment Zone",
        # color_sequence=["#208385", "#FC9A62", "#F9C63E", "#632E5A", "#A48352", "#BCEDB8"],
        color_sequence=["#ABCD66", "#E69800", "#A87000", "#F5CA7A"],
        orders={
            "Year": [
                "2007",
                "2008",
                "2009",
                "2010",
                "2011",
                "2012",
                "2013",
                "2014",
                "2015",
                "2016",
                "2017",
                "2018",
                "2019",
                "2020",
                "2021",
                "2022",
                "2023",
            ]
        },
        y_title="Acres Treated",
        x_title="Year",
        custom_data=["Treatment Zone"],
        hovertemplate="<br>".join(
            ["<b>%{y:,.0f} acres</b> of forest health treatment", "in the <i>%{customdata[0]}</i>"]
        )
        + "<extra></extra>",
        hovermode="x unified",
        orientation=None,
        format=",.0f",
        additional_formatting=dict(
            # title = "Forest Health Treatment",
            legend=dict(
                title= "Forest Health Treatment Zone",
                orientation="h",
                entrywidth=85,
                yanchor="bottom",
                y=1.05,
                xanchor="right",
                x=0.95,
            )
        ),
    )


def get_old_growth_forest():
    data = get_fs_data(
        "https://maps.trpa.org/server/rest/services/Vegetation_Late_Seral/FeatureServer/0"
    )
    # df = data.groupby(["SeralStage","SpatialVar"]).agg({"Acres": "sum"}).reset_index()
    df = data[["SeralStage", "SpatialVar", "TRPA_VegType", "Acres"]]
    return df


def plot_old_growth_forest(df):
    seral = df.groupby("SeralStage").agg({"Acres": "sum"}).reset_index()
    stackedbar(
        seral,
        path_html="html/2.1.b_OldGrowthForest_SeralStage.html",
        div_id="2.1.b_OldGrowthForest_SeralStage",
        x="SeralStage",
        y="Acres",
        facet=None,
        color=None,
        color_sequence=["#208385"],
        orders=None,
        y_title="Acres",
        x_title="Seral Stage",
        custom_data=["SeralStage"],
        hovertemplate="<br>".join(["<b>%{y:,.0f}</b> acres of", "<i>%{customdata[0]}</i> forest"])
        + "<extra></extra>",
        hovermode="x unified",
        orientation=None,
        format=",.0f",
    )
    structure = df.groupby("SpatialVar").agg({"Acres": "sum"}).reset_index()
    stackedbar(
        structure,
        path_html="html/2.1.b_OldGrowthForest_Structure.html",
        div_id="2.1.b_OldGrowthForest_Structure",
        x="SpatialVar",
        y="Acres",
        facet=None,
        color=None,
        color_sequence=["#208385"],
        orders=None,
        y_title="Acres",
        x_title="Structure",
        custom_data=["SpatialVar"],
        hovertemplate="<br>".join(
            ["<b>%{y:,.0f}</b> acres of", "<i>%{customdata[0]}</i> old growth forest"]
        )
        + "<extra></extra>",
        hovermode="x unified",
        orientation=None,
        format=",.0f",
    )
    species = df.groupby("TRPA_VegType").agg({"Acres": "sum"}).reset_index()
    stackedbar(
        species,
        path_html="html/2.1.b_OldGrowthForest_Species.html",
        div_id="2.1.b_OldGrowthForest_Species",
        x="TRPA_VegType",
        y="Acres",
        facet=None,
        color=None,
        color_sequence=["#208385"],
        orders=None,
        y_title="Acres",
        x_title="Vegetation Type",
        custom_data=["TRPA_VegType"],
        hovertemplate="<br>".join(
            ["<b>%{y:,.0f}</b> acres of", "<i>%{customdata[0]}</i> old growth forest"]
        )
        + "<extra></extra>",
        hovermode="x unified",
        orientation=None,
        format=",.0f",
    )

def get_probability_of_high_severity_fire():
    highseverity = get_fs_data_spatial(
        "https://maps.trpa.org/server/rest/services/LTinfo_Climate_Resilience_Dashboard/MapServer/129"
    )
    df = highseverity.groupby(["Name", "gridcode"])["Acres"].sum().reset_index()
    df["Probability"] = np.where(
        df["gridcode"] == 1, "High Severity Fire", "Low to Moderate Severity Fire"
    )

    # standardize values to "Wilderness"
    df.loc[
        df["Name"].isin(
            ["Desolation Wilderness", "Mt. Rose Wilderness", "Granite Chief Wilderness"]
        )
    ] = "Wilderness"

    total = df.groupby("Name")["Acres"].sum().reset_index()

    df = df.merge(total, on="Name")
    df["Share"] = df["Acres_x"] / df["Acres_y"]
    df = df.rename(
        columns={"Name": "Forest Management Zone", "Acres_x": "Acres", "Acres_y": "Total"}
    )
    return df

def plot_probability_of_high_severity_fire(df):
    stackedbar(
        df,
        path_html="html/2.1.c_Probability_of_High_Severity_Fire.html",
        div_id="2.1.c_Probability_of_High_Severity_Fire",
        x="Forest Management Zone",
        y="Share",
        facet=None,
        color="Probability",
        color_sequence=["#208385", "#FCB42C"],
        orders=None,
        y_title="",
        x_title="Forest Management Zone",
        custom_data=["Probability"],
        hovertemplate="<br>".join(
            ["<b>%{y:.0%}</b> of the forested area is", "likely to burn as <i>%{customdata[0]}</i>"]
        )
        + "<extra></extra>",
        hovermode="x unified",
        orientation=None,
        format=".0%",
    )
