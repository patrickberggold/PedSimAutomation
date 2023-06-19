#IN[0]: room dict.

import clr
from System.Drawing import *
from Autodesk.DesignScript.Geometry import *
from RevitServices.Persistence import DocumentManager 
from Autodesk.Revit.DB import *

def extract_lists_with_string(room_dict, type):
    extracted_lists = []
    for key in room_dict:
        if type in key:
            extracted_lists.append(room_dict[key])
    return extracted_lists
    
if UnwrapElement(IN[1]) :  
    dict = IN[0]
    
    origins = extract_lists_with_string(dict , "ORIGIN")
    destinations = extract_lists_with_string(dict , "DESTINATION")
    obstacles = extract_lists_with_string(dict , "OBSTACLE")

    OUT = origins , destinations , obstacles