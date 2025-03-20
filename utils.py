# imports
import arcpy
from arcpy.sa import *
from arcpy.ia import *
from arcpy.ddd import *
import pandas as pd
from pathlib import Path

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