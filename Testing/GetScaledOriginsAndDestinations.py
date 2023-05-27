#IN[0]: room dict.
#IN[1]: scales from transformation script
#IN[2]: view's bounding box and bounding box's width and height from getviewdimensions script

import sys
import clr
import System
from System.IO import *
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager 

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference('System.Drawing')
import System.Drawing
from System.Drawing import *
import os
import tempfile

def extract_lists_with_string(room_dict, type):
    extracted_lists = []
    for key in room_dict:
        if type in key:
            extracted_lists.append(room_dict[key])
    return extracted_lists

def convert_meter_to_unit(pre_value):
    tempo_list = []
    tempo_value = 0
    if isinstance(pre_value, list):
        len_list = len(pre_value)
        for ii in range(len_list):
            tempo_list.append (float(UnitUtils.ConvertToInternalUnits(pre_value[ii], UnitTypeId.Meters)))
        pre_value = tempo_list
    else:
        tempo_value = float(UnitUtils.ConvertToInternalUnits(pre_value, UnitTypeId.Meters))
        pre_value = tempo_value
    return pre_value
    
dict = IN[0]
scale_in_x , scale_in_y = IN[1]
x_min_view , y_min_view = IN[2][:2]

origins = extract_lists_with_string(dict , "ORIGIN")
destinations = extract_lists_with_string(dict , "DESTINATION")

transform_in_x = lambda pre_transformation_value : convert_meter_to_unit(pre_transformation_value) * scale_in_x - x_min_view
transform_in_y = lambda pre_transformation_value : convert_meter_to_unit(pre_transformation_value) * scale_in_y - y_min_view

origins_in_view = []
for origin in origins : 
    origin_in_view =  [
        [transform_in_x(origin[0][0]) , transform_in_y(origin[0][1])] , [transform_in_x(origin[1][0]) , transform_in_y(origin[1][1])]
    ]
    origins_in_view.append(origin_in_view)

destinations_in_view = []
for destination in destinations : 
    destination_in_view =  [
        [transform_in_x(destination[0][0]) , transform_in_y(destination[0][1])] , [transform_in_x(destination[1][0]) , transform_in_y(destination[1][1])]
    ]
    destinations_in_view.append(destination_in_view)

OUT = origins_in_view , destinations_in_view