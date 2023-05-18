import clr

from System.Collections.Generic import *

clr.AddReference("RevitNodes")
import Revit

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager 
from RevitServices.Transactions import TransactionManager 

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

clr.AddReference('ProtoGeometry')
import Autodesk 
from Autodesk.DesignScript.Geometry import *
from Autodesk.Revit.DB import *
#from Autodesk.Revit.UI import *
from Autodesk.Revit.DB.Architecture import *

#-----------------------------------------------------------------------------------------------------------------#
# Helper functions...

## Converts str to float : 
# @param float_as_string:str string to be converted
# @returns argument converted to a float
# @raises ValueError
def convert_to_float(float_as_string) : 
    try : 
        return float(float_as_string)
    except : 
        raise ValueError("Argument string cannot be converted to float")

## Converts a value or list of values from meters to Revit units
# Checks if arg is a single value, and converts it to Revit units
# Otherwise, arg is a list and all values are converted in a loop
# @param values_in_meter: list<float> (float) list of values (value) to be converted
# @uses convert_to_float()
# @returns values_in_revit_units: list<float> (float) list of values (value) in Revit units
# @raises ValueError
def convert_to_revit_units(values_in_meter) : 
    if values_in_meter == None : 
        raise ValueError("Received a null value or list of values.")

    if not isinstance(values_in_meter , list) : 
        return convert_to_float(UnitUtils.ConvertToInternalUnits(values_in_meter , UnitTypeId.Meters))
    
    return [
        convert_to_float(
            UnitUtils.ConvertToInternalUnits(value, UnitTypeId.Meters)
        ) for value in values_in_meter
    ]

## Converts a value or list of values from Revit units to meter
# Checks if arg is a single value, and converts it to meter
# Otherwise, arg is a list and all values are converted in a loop
# @param values_in_revit_units: list<float> (float) list of values to be converted
# @uses convert_to_float()
# @returns values_in_meter: list<float> (float) list of values (value) in Revit units
# @raises ValueError
def convert_to_meter(values_in_revit_units) : 
    if values_in_revit_units == None : 
        raise ValueError("Received a null value or list of values.")

    if not isinstance(values_in_revit_units , list) : 
        return convert_to_float(
            UnitUtils.ConvertFromInternalUnits(values_in_revit_units, UnitTypeId.Meters)
        )
    
    return [
        convert_to_float(
            UnitUtils.ConvertFromInternalUnits(value, UnitTypeId.Meters)
        ) for value in values_in_revit_units
    ]

## Create four lines for a given point in 3D space and two index lists (min and max)
# Four possible vertices are stored in a  list and accessed using two index lists (min_indices and max_indices)
# create_bound is only created for convenience
# @param point: list<float> list containing the x, y and z poisitions of a point in space
# @param min_indices: list<int> list of indices of the start vertices of all four perimeter lines
# @param max_indices: list<int> list of indices of the end vertices of all four perimeter lines
# @returns list<Revit.DB.Line> list containing four lines
# @raises ValueError
def create_lines_from_point_and_indices(point , min_indices , max_indices) : 
    if len(point) != 3 :
        raise ValueError("Point must be a 3D vector.")
    
    if len(min_indices) != 4 or len(min_indices) != len(max_indices) :
        raise ValueError("Both index lists must be equal in length and the length must be 4.")

    create_bound = lambda min_point , max_point : Autodesk.Revit.DB.Line.CreateBound(min_point , max_point)

    x , y , z = point
    vertices = [
        XYZ(0 , 0 , z) , XYZ(x , 0 , z) , XYZ(0 , y , z) , XYZ(x , y , z)
    ]

    return [
        create_bound(vertices[min_indices[i]] , vertices[max_indices[i]]) for i in range(len(min_indices))
    ]

## Create four perimeter lines for a point in space, given its x, y and z position
# @param x: float x-position of point
# @param y: float y-position of point
# @param z: float z-position of point
# @uses create_lines_from_point_and_indices()
# @note min and max index lists are hard coded into function; refer to the description of create_lines_from_point_and_indices() for definitions of min_indices and max_indices
# @returns list<Revit.DB.Line> list containing four perimeter lines
def create_perimeter_lines(x , y , z) : 
    min_indices , max_indices = [0 , 1 , 2 , 3] , [1 , 3 , 2 , 0]
    point = [x , y , z]

    return create_lines_from_point_and_indices(point , min_indices , max_indices)

## Create slab geometry for a given x and y position, level and difference in z
# The slab is a CurveArray(), with appended perimeter lines (4 in total)
# @param x: float x-position of point
# @param y: float y-position of point
# @param level: Level Revit level element object
# @param delta_z: float difference in z-position
# @uses create_perimeter_lines()
# @returns slab_geometry: CurveArray CurveArray with four perimeter lines appended to it
# @raises TypeError , ValueError
def create_slab_geometry_by_level(x , y , delta_z , level) : 
    if not isinstance(level, Level):
        raise TypeError("Arg level must be a valid Level object")
    if level == None : 
        raise ValueError("level is null")
    
    z = level.Elevation + delta_z

    lines = create_perimeter_lines(x , y , z)

    slab_geometry = CurveArray()
    for i in range(len(lines)) : 
        slab_geometry.append(lines[i])
    
    return slab_geometry
#-----------------------------------------------------------------------------------------------------------------#

