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
# @param x_min: float Minimum x-value
# @param y_min: float Minimum y-value
# @param z_min: float Minimum z-value
# @param x_max: float Maximum x-value
# @param y_max: float Maximum y-value
# @param z_max: float Maximum z-value
# @returns bounding_box: BoundingBox object
def create_bounding_box(x_min , y_min , z_min , x_max , y_max , z_max) :
    bounding_box = BoundingBoxXYZ()
    bounding_box.Min = XYZ(x_min , y_min , z_min)
    bounding_box.Max = XYZ(x_max , y_max , z_max)

    return bounding_box

## Create new stories in a Revit document
# Creates a new story for each elevation except for the reference elevation
# @param doc: DBDocument Revit document
# @param number_of_stories
# @param ref_elevation: float Reference elevation
# @param story_z: list<float> List of the elevation of all stories
# @return None
# @raises ValueError
def create_new_stories(doc , number_of_stories , ref_elevation , story_z) : 
    if len(story_z) != number_of_stories : 
        raise ValueError("Number of stories and elevations are not equal.")

    for i in range(number_of_stories) : 
        if ref_elevation != story_z[i] : 
            new_level = Autodesk.Revit.DB.Level.Create(doc, story_z[i])
            new_level.Name = f"Story Level {i}"

## Creates the roof level in a given Revit document
# @param doc: DBDocument Revit document
# @param site_z: float Total height of model
# @return None
def create_roof_level(doc , site_z) : 
    roof_level = Autodesk.Revit.DB.Level.Create(doc, site_z)
    roof_level.Name = "Roof Level"


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
## Script 1/Create reference level
# Deletes all geometries in the Revit document
# Deletes all levels except for a reference level
# Creates a new bounding box for reference level
# Outputs:
# a list of bounding boxes with one entry
# dimensions of site in revit units
# reference level

site_b_boxes = []

site_x , site_y , site_z = convert_to_revit_units(SITE_X - 0.3) , convert_to_revit_units(SITE_Y - 0.3) , convert_to_revit_units(total_height)

level_array = get_all_levels(DOC)
clear_model(DOC)

ref_level = verify_number_of_levels(DOC , convert_to_revit_units(ref_level_z))
site_b_boxes.append(create_bounding_box(0 , 0 , 0 , 0 , 0 , site_z))

#-----------------------------------------------------------------------------------------------------------------#
# Create levels and roofs...

corridor_width = convert_to_revit_units(CORRIDOR_WIDTH)
story_z = convert_to_revit_units(story_z)

create_new_stories(DOC , total_num_stories , ref_level.Elevation , story_z)
create_roof_level(DOC , site_z)

all_levels = FilteredElementCollector(doc).OfClass(Level).ToElements()

# Create Bounding Box for each story
for i in range(total_num_stories) : 
    max_z_in_bbox = story_z[i + 1] if i < (total_num_stories - 1) else site_z

    site_b_boxes.append(
        create_bounding_box(0 , 0 , story_z[i] , site_x , site_y , max_z_in_bbox)
    )

#-----------------------------------------------------------------------------------------------------------------#
# Create floorplan complexity...

    WIDTH = site_y
    LENGTH = site_x
    print('x_length: ' + str(convert_to_meter(LENGTH)))
    print('y_width: ' + str(convert_to_meter(WIDTH)))
    print("")
    z_level = ref_level.Elevation
    ceiling = all_levels[0].Elevation

    obstacle_counter = 0

    # Create the exterior walls
    perimeter_lines = create_perimeter_lines(LENGTH , WIDTH , z_level)
    for ww in range(4):
        wall = Wall.Create(DOC, perimeter_lines[ww], default_exterior_wall_type.Id, ref_level.Id, site_z, 0, False, True)
        exterior_wall_list.append(wall)

    # Create floor for each story level
    for ii in range(total_num_stories):
        ll = all_levels[ii]
        floor_geometry = create_slab_geometry_by_level(LENGTH , WIDTH , 0. , ll)
        floor = DOC.Create.NewFloor(floor_geometry, FLOOR_TYPE, ll, True)
        floor_list.append(floor)

    # Create corridor lines
    y_main_corridor = 0.5*WIDTH
    x_main_corridor_start = 1.5*CORR_WIDTH
    x_main_corridor_end = LENGTH-1.5*CORR_WIDTH
        
    bottlneck_ys = [CORR_WIDTH, WIDTH-CORR_WIDTH]

    P0_long = XYZ(x_main_corridor_start, 0, ceiling)
    P1_long = XYZ(x_main_corridor_start, y_main_corridor - CORR_WIDTH/2., ceiling)
    P2_long = XYZ(LENGTH, y_main_corridor - CORR_WIDTH/2., ceiling)

    line_corr_0_long = Autodesk.Revit.DB.Line.CreateBound(P0_long, P1_long)
    line_corr_1_long = Autodesk.Revit.DB.Line.CreateBound(P1_long, P2_long)

    P1_short = XYZ(0, y_main_corridor + CORR_WIDTH/2., ceiling)
    P2_short = XYZ(x_main_corridor_end, y_main_corridor + CORR_WIDTH/2., ceiling)
    P3_short = XYZ(x_main_corridor_end, WIDTH, ceiling)
    
    line_corr_1_short = Autodesk.Revit.DB.Line.CreateBound(P1_short, P2_short)
    line_corr_2_short = Autodesk.Revit.DB.Line.CreateBound(P2_short, P3_short)

    corr_room_lines = [line_corr_1_short, line_corr_2_short, line_corr_0_long, line_corr_1_long] # , line_corr_2_long, line_corr_3_long]
    # Create corridor-room walls
    corr_walls = [Wall.Create(DOC, wall_line, default_interior_wall_type.Id, all_levels[0].Id, all_levels[1].Elevation - all_levels[0].Elevation, 0, False, True) \
        for wall_line in corr_room_lines]

    # obstacles
    obstacle_length = 1.

    x_obst_min, x_obst_max = convert_to_meter(x_main_corridor_end)+0.1, convert_to_meter(x_main_corridor_end)+0.1+obstacle_length
    y_obst_min, y_obst_max = convert_to_meter(y_main_corridor + CORR_WIDTH/2.)+0.5, convert_to_meter(y_main_corridor + CORR_WIDTH/2.)+0.5+OBSTACLE_WIDTH
    room_dict.update({
        'CROWDIT_OBSTACLE_'+str(obstacle_counter)+'1_1': [
                (x_obst_min, y_obst_min),
                (x_obst_max, y_obst_max)
            ]
        }
    )
    obstacle_counter += 1

    x_obst_min, x_obst_max = convert_to_meter(x_main_corridor_start)-0.1-obstacle_length, convert_to_meter(x_main_corridor_start)-0.1
    y_obst_min, y_obst_max = convert_to_meter(y_main_corridor - CORR_WIDTH/2.)-0.5-OBSTACLE_WIDTH, convert_to_meter(y_main_corridor - CORR_WIDTH/2.)-0.5
    room_dict.update({
        'CROWDIT_OBSTACLE_'+str(obstacle_counter)+'1_1': [
                (x_obst_min, y_obst_min),
                (x_obst_max, y_obst_max)
            ]
        }
    )
    obstacle_counter += 1
    

    # destination areas
    bottlneck_ys_room_dict = [0, WIDTH]
    origin_opening_list = []
    
    x_min_fixed_1, x_max_fixed_1 = min(0, x_main_corridor_start), max(0, x_main_corridor_start)
    y_min_fixed_1, y_max_fixed_1 = min(bottlneck_ys[0], bottlneck_ys_room_dict[0]), max(bottlneck_ys[0], bottlneck_ys_room_dict[0])

    room_dict.update({
        'CROWDIT_DESTINATION_0': [
                (convert_to_meter(x_min_fixed_1)+0.5, convert_to_meter(y_min_fixed_1)+0.5),
                (convert_to_meter(x_max_fixed_1)-0.5, convert_to_meter(y_max_fixed_1)-0.5)
            ]
        }
    )

    x_min_fixed_2, x_max_fixed_2 = min(x_main_corridor_end, LENGTH), max(x_main_corridor_end, LENGTH)
    y_min_fixed_2, y_max_fixed_2 = min(bottlneck_ys[1], bottlneck_ys_room_dict[1]), max(bottlneck_ys[1], bottlneck_ys_room_dict[1])

    room_dict.update({
        'CROWDIT_DESTINATION_1': [
                (convert_to_meter(x_min_fixed_2)+0.5, convert_to_meter(y_min_fixed_2)+0.5),
                (convert_to_meter(x_max_fixed_2)-0.5, convert_to_meter(y_max_fixed_2)-0.5)
            ]
        }
    )

    ###############
    # Office rooms
    ###############
    # DOOR_WIDTH_H = convert_meter_to_unit(0.5)
    DOOR_HEIGHT = convert_meter_to_unit(2.2)
    DOOR_THICKNESS_H = convert_meter_to_unit(0.25)

    # short side
    fractions = [1./(NUM_ROOMS_SHORT_SIDE)*i for i in range(NUM_ROOMS_SHORT_SIDE+1)]
    short_x_coord_list = [P1_short[0] + fr * (P2_short[0] - P1_short[0]) for fr in fractions]
    
    for x_coord in short_x_coord_list[1:-1]:
        office_office_line = Autodesk.Revit.DB.Line.CreateBound(
                XYZ(x_coord, P2_short[1], ceiling),
                XYZ(x_coord, P3_short[1], ceiling))
        Wall.Create(DOC, office_office_line, default_interior_wall_type.Id, all_levels[0].Id, all_levels[1].Elevation - all_levels[0].Elevation, 0, False, True)
    
    # create openings short offices
    for id in range(len(short_x_coord_list)-1):
        x_opening = (short_x_coord_list[id+1] + short_x_coord_list[id])/2.
        y_opening = P1_short[1]
        z_opening = z_level

        start_point = XYZ(x_opening-DOOR_WIDTH_H, y_opening-DOOR_THICKNESS_H, z_opening)
        end_point = XYZ(x_opening+DOOR_WIDTH_H, y_opening+DOOR_THICKNESS_H, z_opening+DOOR_HEIGHT)
        origin_opening_list.append(DOC.Create.NewOpening(corr_walls[0], start_point, end_point))

        y_min_var_short, y_max_var_short = min(P1_short[1], P3_short[1]), max(P1_short[1], P3_short[1])

        room_dict.update({
            'CROWDIT_ORIGIN_'+str(id): [
                    (convert_to_meter(short_x_coord_list[id])+0.5, convert_to_meter(y_min_var_short)+0.5),
                    (convert_to_meter(short_x_coord_list[id+1])-0.5, convert_to_meter(y_max_var_short)-0.5)
                ]
            }
        )

        if id > 0:
            # obstacle: rectangle (e.g. table: 2x1 m rectangle)
            obstacle_length = 2.
            if y_opening < y_main_corridor:
                y_obst_min = convert_to_meter(y_opening)+0.1
                y_obst_max = convert_to_meter(y_opening)+0.1+OBSTACLE_WIDTH
            else:
                y_obst_min = convert_to_meter(y_opening)-0.1-OBSTACLE_WIDTH
                y_obst_max = convert_to_meter(y_opening)-0.1

            room_dict.update({
                'CROWDIT_OBSTACLE_'+str(obstacle_counter)+'2_1': [
                        (convert_to_meter(short_x_coord_list[id])-obstacle_length/2., y_obst_min),
                        (convert_to_meter(short_x_coord_list[id])+obstacle_length/2., y_obst_max)
                    ]
                }
            )
            obstacle_counter += 1


    # long side
    # create openings long offices
    fractions = [1./(NUM_ROOMS_LONG_SIDE)*i for i in range(NUM_ROOMS_LONG_SIDE+1)]
    long_x_coord_list = [P1_long[0] + fr * (P2_long[0] - P1_long[0]) for fr in fractions]

    for x_coord in long_x_coord_list[1:-1]:
        office_office_line = Autodesk.Revit.DB.Line.CreateBound(
                XYZ(x_coord, P2_long[1], ceiling),
                XYZ(x_coord, P0_long[1], ceiling))
        Wall.Create(DOC, office_office_line, default_interior_wall_type.Id, all_levels[0].Id, all_levels[1].Elevation - all_levels[0].Elevation, 0, False, True)

    
    # create openings long offices
    for id in range(len(long_x_coord_list[:-1])):
        x_opening = (long_x_coord_list[id+1] + long_x_coord_list[id])/2.
        y_opening = P1_long[1]
        z_opening = z_level

        start_point = XYZ(x_opening-DOOR_WIDTH_H, y_opening-DOOR_THICKNESS_H, z_opening)
        end_point = XYZ(x_opening+DOOR_WIDTH_H, y_opening+DOOR_THICKNESS_H, z_opening+DOOR_HEIGHT)
        origin_opening_list.append(DOC.Create.NewOpening(corr_walls[3], start_point, end_point))

        y_min_var_long, y_max_var_long = min(P0_long[1], P1_long[1]), max(P0_long[1], P1_long[1])
        room_dict.update({
            'CROWDIT_ORIGIN_'+str(id+len(short_x_coord_list)-1): [
                    (convert_to_meter(long_x_coord_list[id])+0.5, convert_to_meter(y_min_var_long)+0.5),
                    (convert_to_meter(long_x_coord_list[id+1])-0.5, convert_to_meter(y_max_var_long)-0.5)
                ]
            }
        )

        if id > 0:
            # obstacle: rectangle (e.g. table: 2x1 m rectangle)
            obstacle_length = 2.
            if y_opening < y_main_corridor:
                y_obst_min = convert_to_meter(y_opening)+0.1
                y_obst_max = convert_to_meter(y_opening)+0.1+OBSTACLE_WIDTH
            else:
                y_obst_min = convert_to_meter(y_opening)-0.1-OBSTACLE_WIDTH
                y_obst_max = convert_to_meter(y_opening)-0.1

            room_dict.update({
                'CROWDIT_OBSTACLE_'+str(obstacle_counter)+'2_1': [
                        (convert_to_meter(long_x_coord_list[id])-obstacle_length/2., y_obst_min),
                        (convert_to_meter(long_x_coord_list[id])+obstacle_length/2., y_obst_max)
                    ]
                }
            )
            obstacle_counter += 1


    if USE_BOTTLENECKS:
        bottleneck_lines = [
            Autodesk.Revit.DB.Line.CreateBound(
                XYZ(0, bottlneck_ys[0], ceiling),
                XYZ(x_main_corridor_start, bottlneck_ys[0], ceiling)),
            
            Autodesk.Revit.DB.Line.CreateBound(
                XYZ(x_main_corridor_end, bottlneck_ys[1], ceiling),
                XYZ(LENGTH, bottlneck_ys[1], ceiling))
        ]
        
        bottleneck_walls = [Wall.Create(DOC, line, default_interior_wall_type.Id, all_levels[0].Id, all_levels[1].Elevation - all_levels[0].Elevation, 0, False, True)
            for line in bottleneck_lines]

        # some doors
        x_opening_1 = x_main_corridor_start/2.
        y_opening_1 = bottlneck_ys[0]
        z_opening_1 = z_level

        start_point_1 = XYZ(x_opening_1-DOOR_WIDTH_H, y_opening_1-DOOR_THICKNESS_H, z_opening_1)
        end_point_1 = XYZ(x_opening_1+DOOR_WIDTH_H, y_opening_1+DOOR_THICKNESS_H, z_opening+DOOR_HEIGHT)
        opening_1 = DOC.Create.NewOpening(bottleneck_walls[0], start_point_1, end_point_1)

        x_opening_2 = x_main_corridor_end + (LENGTH-x_main_corridor_end)/2.
        y_opening_2 = bottlneck_ys[1]
        z_opening_2 = z_level

        start_point_2 = XYZ(x_opening_2-DOOR_WIDTH_H, y_opening_2-DOOR_THICKNESS_H, z_opening_2)
        end_point_2 = XYZ(x_opening_2+DOOR_WIDTH_H, y_opening_2+DOOR_THICKNESS_H, z_opening_2+DOOR_HEIGHT)
        opening_2 = DOC.Create.NewOpening(bottleneck_walls[1], start_point_2, end_point_2)

    assert len(origin_opening_list) == len([key for key in room_dict if key.startswith('CROWDIT_ORIGIN_')])
    
#-----------------------------------------------------------------------------------------------------------------#
TransactionManager.Instance.TransactionTaskDone()

OUT = room_dict