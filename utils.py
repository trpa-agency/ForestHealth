# imports
# import packages
import arcpy
from arcpy.sa import *
from arcpy.ia import *
from arcpy.ddd import *
import pandas as pd
from pathlib import Path

# functions
# iterate over raster attribute table 
def export_attributes_as_rasters(in_raster, output_folder):
    # Set local variables
    arcpy.env.workspace = output_folder
    # get field names to loop through and create rasters from
    field_names = [f.name for f in arcpy.ListFields(featureclass)]
    fields_to_remove = ['OBJECTID', 'Value', 'Count']
    fields = [x for x in field_names if x not in fields_to_remove]
    # Iterate over the unique attribute values and export each as a separate raster

    for field in fields:
        # Execute Lookup
        out_raster = Lookup(in_raster, field, value)
        # Save the output raster
        out_raster_path = f"{in_raster}_{field}"
        out_raster.save(out_raster_path)
        print("Exported raster for field: ", field)

        
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

# 
def CreateRasterLookup(raster, field, name):
    Lookup(
        in_raster    =raster,
        lookup_field =field,
        out_raster   =name
    )