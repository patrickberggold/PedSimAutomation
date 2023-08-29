###############################################################
# Load the Libraries
###############################################################
import os
import clr
import sys
import math
import System
import time

from System import Array
from System.Collections.Generic import *

clr.AddReference("RevitNodes")
import Revit

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager 
from RevitServices.Transactions import TransactionManager 

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

clr.AddReference('ProtoGeometry')
import Autodesk 
from Autodesk.DesignScript.Geometry import *
from Autodesk.Revit.DB import *
#from Autodesk.Revit.UI import *
from Autodesk.Revit.DB import StairsEditScope
from Autodesk.Revit.DB import Parameter
from Autodesk.Revit.DB.Architecture import StairsRun
from Autodesk.Revit.DB.Architecture import *
from Autodesk.Revit.DB import IFailuresPreprocessor

doc = DocumentManager.Instance.CurrentDBDocument

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

def convert_to_meter(internal_value):
	if isinstance(internal_value, list):
		return [UnitUtils.ConvertFromInternalUnits(value, UnitTypeId.Meters) for value in internal_value]
	return float(UnitUtils.ConvertFromInternalUnits(internal_value, UnitTypeId.Meters))

def find_perimeter_lines(x,y,z):
    line_list = []
    xx = x
    yy = y
    zz = z 
    # print "find_perimeter_lines x: " + str(x)
    # print "find_perimeter_lines y: " + str(y)
    # print "find_perimeter_lines z: " + str(z)
	
    line_1 = Autodesk.Revit.DB.Line.CreateBound(XYZ(0,0,zz),    XYZ(xx,0,zz))
    line_2 = Autodesk.Revit.DB.Line.CreateBound(XYZ(xx,0,zz),   XYZ(xx,yy,zz))
    line_3 = Autodesk.Revit.DB.Line.CreateBound(XYZ(xx,yy,zz),  XYZ(0,yy,zz))
    line_4 = Autodesk.Revit.DB.Line.CreateBound(XYZ(0,yy,zz),   XYZ(0,0,zz))

    line_list.append(line_1)
    line_list.append(line_2)
    line_list.append(line_3)
    line_list.append(line_4)
    
    return line_list

def create_slab_geometry(x_min , x_max , y_min , y_max , z) : 

    bottom_left_point = XYZ(x_min , y_min , z)
    bottom_right_point = XYZ(x_max , y_min , z)
    top_right_point = XYZ(x_max , y_max , z)
    top_left_point = XYZ(x_min , y_max , z)

    bottom_line = Autodesk.Revit.DB.Line.CreateBound(bottom_left_point , bottom_right_point)
    right_vertical_line = Autodesk.Revit.DB.Line.CreateBound(bottom_right_point , top_right_point)
    top_line = Autodesk.Revit.DB.Line.CreateBound(top_right_point , top_left_point)
    left_vertical_line = Autodesk.Revit.DB.Line.CreateBound(top_left_point , bottom_left_point)

    slab_geometry = CurveArray()
    slab_geometry.Append(bottom_line)
    slab_geometry.Append(right_vertical_line)
    slab_geometry.Append(top_line)
    slab_geometry.Append(left_vertical_line)

    return slab_geometry

def create_one_stair(start_x , start_y , start_z , end_x , end_y , end_z , level , floor_type) : 
    stair_thickness = end_z - start_z
    
    stair_type = floor_type.Duplicate(f"{stair_thickness}_starts_at_{start_x}_{start_y}_{start_z}_at_{time.time()}")
    compound = stair_type.GetCompoundStructure()
    compound.SetLayerWidth(0, stair_thickness)
    stair_type.SetCompoundStructure(compound)
    
    stair_geom = create_slab_geometry(start_x , end_x , start_y , end_y , start_z + stair_thickness)
    
    return doc.Create.NewFloor(stair_geom , stair_type , level , True)

def slab_geometry_by_level(x,y,level,delta_z):
    return create_slab_geometry(0. , x , 0. , y , level.Elevation + delta_z)

def create_staircase(start_x , start_y , start_level , end_x , end_y , end_level , thickness , floor_type , inXDirection = False) : 
    number_stairs = int((end_level.Elevation - start_level.Elevation) / min(thickness , end_level.Elevation - start_level.Elevation))
    thickness = (end_level.Elevation - start_level.Elevation) / float(number_stairs) if number_stairs > 1 else thickness

    if inXDirection :
        stair_delta_x = (end_x - start_x) / float(number_stairs)
        stair_delta_y = end_y - start_y
        translation_vector = XYZ(stair_delta_x , 0. , thickness)
    else : 
        stair_delta_x = end_x - start_x
        stair_delta_y = (end_y - start_y) / float(number_stairs)
        translation_vector = XYZ(0. , stair_delta_y , thickness)

    initial_stair = create_one_stair(start_x , start_y , start_level.Elevation , start_x + stair_delta_x , start_y + stair_delta_y , start_level.Elevation + thickness , start_level , floor_type)

    stair_ids = [initial_stair.Id]
    for _ in range(number_stairs - 1) : 
        stair_id = ElementTransformUtils.CopyElement(doc , stair_ids[-1] , translation_vector)
        stair_ids.append(stair_id[0])

    return stair_ids


OUT = convert_meter_to_unit , convert_to_meter , find_perimeter_lines , create_slab_geometry , create_one_stair , slab_geometry_by_level , create_staircase