import clr

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

## Converts a string to an integer
# @param int_as_string:str string to be converted
# @returns argument converted to an integer
# @raises ValueError
def convert_to_int(int_as_string) : 
    try : 
        return int(int_as_string)
    except : 
        raise ValueError(f"{int_as_string} cannot be converted to integer")

## Converts str to boolean : 
# @param bool_as_string:str string to be converted
# @returns argument converted to a boolean
# @note converted to integer first to counter edge case: "0" is casted to True
# @raises ValueError
def convert_to_bool(bool_as_string) : 
    try : 
        return bool(convert_to_int(bool_as_string))
    except ValueError as e : 
        if "False" in str(e) or "True" in str(e) : return bool(bool_as_string)
        else : raise ValueError("Argument string cannot be converted to boolean")

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

## Collects all levels from a Revit Doc
# @param doc: DBDocument Revit Document
# @returns list<Level> List of all levels in a Revit document
# @raises ValueError
def get_all_levels(doc) : 
    if doc == None : 
        raise ValueError("Empty Revit Doc")

    return (FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Levels)
        .WhereElementIsNotElementType()
        .ToElements())

## Delete all elements in a Revit document
# @param doc: DBDocument Revit Document
# @note element categories are hard coded into function
# @returns None
# @raises ValueError
def clear_model(doc) : 
    if doc == None : 
        raise ValueError("Empty Revit Doc")
    
    element_categories = [
        BuiltInCategory.OST_Grids , BuiltInCategory.OST_Doors , BuiltInCategory.OST_Floors , BuiltInCategory.OST_Walls , BuiltInCategory.OST_Roofs
    ]

    for category in element_categories : 
        elements = FilteredElementCollector(doc).OfCategory(category).WhereElementIsNotElementType().ToElements()
        for element in elements : 
            doc.Delete(element.Id)

## Check the number of existing levels. 
# If there is more than one level in the document, delete all levels except the one at the reference height
# The height is then verified and if it doesn't match ref height, level is deleted and a new level is created.
# @param doc: DBDocument Revit Document
# @param ref_level_z: float Reference height
# @returns ref_level: Level Level located at reference height 
def verify_number_of_levels(doc , ref_level_z) : 
    levels = get_all_levels(doc)

    deleted_levels_counter = 0
    if len(levels) > 1 : 
        for level in levels : 
            if level.Elevation != ref_level_z : 
                doc.Delete(level.Id)
                deleted_levels_counter += 1

    if len(levels) - deleted_levels_counter == 0 : 
        print("Warning: Found no level at elevation = ref_level_z")

    ref_level = levels[0]

    if ref_level.Elevation != ref_level_z : 
        ref_level_new = Autodesk.Revit.DB.Level.Create(doc, ref_level_z)
        doc.Delete(ref_level.Id)
        ref_level = ref_level_new
    
    ref_level.Name = "Story Level 0"
    
    return ref_level
    
## Create bounding box from origin to a point at z = height
# @param height: float height of bounding box
# @returns bounding_box: BoundingBox object
def create_bounding_box(height) :
    bounding_box = BoundingBoxXYZ()
    bounding_box.Min = XYZ(0 , 0 , 0)
    bounding_box.Max = XYZ(0 , 0 , height)

    return bounding_box

#-----------------------------------------------------------------------------------------------------------------#
# Revit Doc
DOC = DocumentManager.Instance.CurrentDBDocument
TransactionManager.Instance.EnsureInTransaction(DOC)

#-----------------------------------------------------------------------------------------------------------------#
# Constants...
EXTERIOR_WALL_TYPE = UnwrapElement(IN[0])
EXTERIOR_WALL_THICKNESS = 0.3
INTERIOR_WALL_TYPE = UnwrapElement(IN[2])
INTERIOR_WALL_THICKNESS = 0.2
FLOOR_TYPE = UnwrapElement(IN[1])
FLOOR_THICKNESS = 0.3

parameter_list = UnwrapElement(IN[3][1])
SITE_X = parameter_list[0]
SITE_Y = parameter_list[1]
CORRIDOR_WIDTH = parameter_list[2]
NUM_ROOMS_NORTH_SIDE = parameter_list[3]
NUM_ROOMS_SIDE_SIDE = parameter_list[4]
USE_BOTTLENECKS = parameter_list[5]

new_parameter_list = UnwrapElement(IN[3][2])
DOOR_WIDTH_HALF = convert_to_revit_units(new_parameter_list[0] / 2.)
OBSTACLE_WIDTH = new_parameter_list[1]

CREATE_MODE_ON = convert_to_bool(IN[4])
#-----------------------------------------------------------------------------------------------------------------#
# Input parameters...

total_num_stories = 1
story_z = [0]
total_height = 4
ref_level_z = 0

#-----------------------------------------------------------------------------------------------------------------#
# Output dict...
room_dict = {}


#-----------------------------------------------------------------------------------------------------------------#
# Script 1...

site_x , site_y , site_z = convert_to_revit_units(SITE_X - 0.3) , convert_to_revit_units(SITE_Y - 0.3) , convert_to_revit_units(total_height)

level_array = get_all_levels(DOC)
clear_model(DOC)

ref_level = verify_number_of_levels(DOC , convert_to_revit_units(ref_level_z))
site_b_box = create_bounding_box(site_z)

#-----------------------------------------------------------------------------------------------------------------#
# Script 2...

corridor_width = convert_to_revit_units(CORRIDOR_WIDTH)
story_z = convert_to_revit_units(story_z)

