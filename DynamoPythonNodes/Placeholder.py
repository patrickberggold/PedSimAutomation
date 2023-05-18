###############################################################
# Load the Libraries
###############################################################
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

###############################################################
# Customize functions 
###############################################################
"""
Converts default unit in Dynamo into meter...
"""
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

"""
Provide perimeter lines from three dimensions...
"""
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

"""
Provide the geometry of slab by level...
"""
def slab_geometry_by_level(x,y,level,delta_z):
    zz = level.Elevation + delta_z
    xx = x
    yy = y 
    line_1 = Autodesk.Revit.DB.Line.CreateBound(XYZ(0,0,zz),    XYZ(xx,0,zz))
    line_2 = Autodesk.Revit.DB.Line.CreateBound(XYZ(xx,0,zz),   XYZ(xx,yy,zz))
    line_3 = Autodesk.Revit.DB.Line.CreateBound(XYZ(xx,yy,zz),  XYZ(0,yy,zz))
    line_4 = Autodesk.Revit.DB.Line.CreateBound(XYZ(0,yy,zz),   XYZ(0,0,zz))
    
    slab_geometry = CurveArray()
    slab_geometry.Append(line_1)
    slab_geometry.Append(line_2)
    slab_geometry.Append(line_3)
    slab_geometry.Append(line_4)
    return slab_geometry

###############################################################
# Current doc/app/ui
###############################################################
doc = DocumentManager.Instance.CurrentDBDocument
# uiapp = DocumentManager.Instance.CurrentUIApplication 
# app = uiapp.Application
# uidoc = uiapp.ActiveUIDocument

###############################################################
# Prepare the input
###############################################################
default_exterior_wall_type = UnwrapElement(IN[0])                   # Default exterior wall type
default_floor_type = UnwrapElement(IN[1])                           # Default Floor type
default_interior_wall_type = UnwrapElement(IN[2])				# Default interior wall type
### INPUT PARAMETERS ###
parameter_list = IN[3][1]
site_x = parameter_list[0]                                # the overall length of the site
site_y = parameter_list[1]                                # the overall widthness of the site
CORR_WIDTH = parameter_list[2] # convert_meter_to_unit(3)
NUM_ROOMS_SHORT_SIDE = parameter_list[3]
NUM_ROOMS_LONG_SIDE = parameter_list[4]
USE_BOTTLENECKS = parameter_list[5]

create_mode = IN[4]
DOOR_WIDTH_H = convert_meter_to_unit(float(IN[5])/2.)
OBSTACLE_WIDTH = float(IN[6])

number_story = 1                                          # the total amount of the stories;
story_z = [0]
site_z = 4                                              # the overall height of the site
ref_level_z = 0                                         # the z-position of the reference level (default level = level 0, created in the prepared .rvt)
###############################################################
# Transaction in Revit
###############################################################
TransactionManager.Instance.EnsureInTransaction(doc)
###############################################################
# Define the output
###############################################################

# Create room dict
room_dict = {}

if create_mode:
    geo_site = []                                                       # archive all the input data
    ref_level = []                                                      # the reference level
    bbox_site = []                                                      # bounding box of the site

    # sys.path.append('C:\Users\ga78jem\Miniconda3\envs\trajectron++\Lib\site-packages')

    ###############################################################
    # Convert the Units | b = UnitUtils.ConvertToInternalUnits(a, UnitTypeId.Meters)  b = a*3 | c = UnitUtils.ConvertFromInternalUnits(a, UnitTypeId.Meters)  c = a*3
    ###############################################################

    # print "site x before conversion:" + str(site_x)
    # adjust the sizes to account for wall thickness
    site_x -= 0.3
    site_y -= 0.3
    site_x = convert_meter_to_unit(site_x)
    site_y = convert_meter_to_unit(site_y)
    site_z = convert_meter_to_unit(site_z)
    ref_level_z = convert_meter_to_unit(ref_level_z)
    CORR_WIDTH = convert_meter_to_unit(CORR_WIDTH)
    # print "site x after conversion:" + str(site_x)

    ###############################################################
    # Delete all levels apart from the reference level (when there are multiple levels)
    ###############################################################
    # Collect all levels
    levelArray = (FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Levels)
        .WhereElementIsNotElementType()
        .ToElements())

    def clear_model(bool_value):
        if bool_value:
            del_grid = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Grids).WhereElementIsNotElementType().ToElements()
            del_door = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType().ToElements()
            del_floor = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Floors).WhereElementIsNotElementType().ToElements()
            del_wall = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Walls).WhereElementIsNotElementType().ToElements()
            del_roof = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Roofs).WhereElementIsNotElementType().ToElements()
            del_all = [del_grid, del_door, del_floor, del_wall, del_roof]
            for element_type in del_all:
                for element in element_type:
                    doc.Delete(element.Id)

    clear_model(True)

    # Check the number of the existing levels, if multiple, delete and save only one
    if len(levelArray) > 1:
        #print "levelArray.Count > 1, from 01_Site"
        for levelElement in levelArray:
            if levelElement.Elevation != ref_level_z:
                doc.Delete(levelElement.Id)
    ref_level = levelArray[0]
    ref_level.Name = "Story Level 0"
    

    # Check the if the saved one is the reference level, correct it if not
    if ref_level.Elevation != ref_level_z:
        ref_level_new = Autodesk.Revit.DB.Level.Create(doc, ref_level_z)
        doc.Delete(ref_level.Id)
        ref_level = ref_level_new
        ref_level.Name = "Story Level 0"

    #--------------------------------------------------------------
    #------------------ OK NOW YOU CAN CODE -----------------------
    #--------------------------------------------------------------

    # Create Bounding Box
    bb = BoundingBoxXYZ()
    bb.Min = XYZ(0, 0, 0)
    bb.Max = XYZ(0, 0, site_z)
    bbox_site.append(bb.ToProtoType())                  # the bounding box of the entire site
    # Close and save the recording file
    # geo_site.append(site_x)
    # geo_site.append(site_y)
    # geo_site.append(site_z)

    ###############################################################
    # END OF SCRIPT 1
    # START OF SCRIPT 2
    ###############################################################

    archive_data = []                                                   # archive all the input data
    bbox_story = []
    exterior_wall_list = []
    floor_list = []
    roof_list = []
    entrance_door_list = []

    ###############################################################
    # Convert the Units | b = UnitUtils.ConvertToInternalUnits(a, UnitTypeId.Meters)  b = a*3 | c = UnitUtils.ConvertFromInternalUnits(a, UnitTypeId.Meters)  c = a*3
    ###############################################################
    story_z = convert_meter_to_unit(story_z)

    # Collect all levels
    levelArray = (FilteredElementCollector(doc)
        .OfCategory(BuiltInCategory.OST_Levels)
        .WhereElementIsNotElementType()
        .ToElements())

    # Check the number of the existing levels, if multiple, delete and save only one
    if len(levelArray) > 1:
        #print "levelArray.Count > 1, from 02_Story"
        for levelElement in levelArray:
            if levelElement.Elevation != ref_level.Elevation:
                doc.Delete(levelElement.Id)
    ref_level = levelArray[0]
    ref_level.Name = "Story Level 0"

    # Check the if the saved one is the reference level, correct it if not
    if ref_level.Elevation != 0:
        ref_level_new = Autodesk.Revit.DB.Level.Create(doc, 0)
        doc.Delete(ref_level.Id)
        ref_level = ref_level_new
        ref_level.Name = "Story Level 0"

    ###############################################################
    # Check the consistence with the bouning box of the side 
    ###############################################################
    # Check the z-position of the highest story against the site box

    check_site_story = True if max(story_z) < site_z else False
    #print "The stories are consistent with the overal site:" + str(check_site_story)

    # Create new story levels
    for ii in range(number_story):
        if ref_level.Elevation == story_z[ii]:
            continue
        new_level = Autodesk.Revit.DB.Level.Create(doc, story_z[ii])
        new_level.Name = "Story Level " + str(ii)

    # Create the roof level
    roof_level = Autodesk.Revit.DB.Level.Create(doc, site_z)
    roof_level.Name = "Roof Level"

    # all levels
    allLevels = FilteredElementCollector(doc).OfClass(Level).ToElements()

    # Create Bounding Box for each story level
    for ii in range(number_story):
        level_bbox_end_z = story_z[ii+1] if ii < (number_story-1) else site_z
        #print "Story"+str(ii)
        #print str(level_bbox_end_z)
        bb = BoundingBoxXYZ()
        bb.Min = XYZ(0, 0, story_z[ii])
        bb.Max = XYZ(site_x, site_y, level_bbox_end_z)
        bbox_story.append(bb.ToProtoType())

    ##############################################################################################################################
    ##############################################################################################################################
    # Create floorplan complexity
    ##############################################################################################################################
    ##############################################################################################################################

    WIDTH = site_y
    LENGTH = site_x
    print('x_length: ' + str(convert_to_meter(LENGTH)))
    print('y_width: ' + str(convert_to_meter(WIDTH)))
    print("")
    z_level = ref_level.Elevation
    ceiling = allLevels[0].Elevation

    obstacle_counter = 0

    # Create the exterior walls
    perimeter_lines = find_perimeter_lines(LENGTH, WIDTH, z_level)
    for ww in range(4):
        wall = Wall.Create(doc, perimeter_lines[ww], default_exterior_wall_type.Id, ref_level.Id, site_z, 0, False, True)
        exterior_wall_list.append(wall)

    # Create floor for each story level
    for ii in range(number_story):
        ll = allLevels[ii]
        floor_geometry = slab_geometry_by_level(LENGTH, WIDTH, ll, 0.0)
        floor = doc.Create.NewFloor(floor_geometry, default_floor_type, ll, True)
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
    corr_walls = [Wall.Create(doc, wall_line, default_interior_wall_type.Id, allLevels[0].Id, allLevels[1].Elevation - allLevels[0].Elevation, 0, False, True) \
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
        Wall.Create(doc, office_office_line, default_interior_wall_type.Id, allLevels[0].Id, allLevels[1].Elevation - allLevels[0].Elevation, 0, False, True)
    
    # create openings short offices
    for id in range(len(short_x_coord_list)-1):
        x_opening = (short_x_coord_list[id+1] + short_x_coord_list[id])/2.
        y_opening = P1_short[1]
        z_opening = z_level

        start_point = XYZ(x_opening-DOOR_WIDTH_H, y_opening-DOOR_THICKNESS_H, z_opening)
        end_point = XYZ(x_opening+DOOR_WIDTH_H, y_opening+DOOR_THICKNESS_H, z_opening+DOOR_HEIGHT)
        origin_opening_list.append(doc.Create.NewOpening(corr_walls[0], start_point, end_point))

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
        Wall.Create(doc, office_office_line, default_interior_wall_type.Id, allLevels[0].Id, allLevels[1].Elevation - allLevels[0].Elevation, 0, False, True)

    
    # create openings long offices
    for id in range(len(long_x_coord_list[:-1])):
        x_opening = (long_x_coord_list[id+1] + long_x_coord_list[id])/2.
        y_opening = P1_long[1]
        z_opening = z_level

        start_point = XYZ(x_opening-DOOR_WIDTH_H, y_opening-DOOR_THICKNESS_H, z_opening)
        end_point = XYZ(x_opening+DOOR_WIDTH_H, y_opening+DOOR_THICKNESS_H, z_opening+DOOR_HEIGHT)
        origin_opening_list.append(doc.Create.NewOpening(corr_walls[3], start_point, end_point))

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
        
        bottleneck_walls = [Wall.Create(doc, line, default_interior_wall_type.Id, allLevels[0].Id, allLevels[1].Elevation - allLevels[0].Elevation, 0, False, True)
            for line in bottleneck_lines]

        # some doors
        x_opening_1 = x_main_corridor_start/2.
        y_opening_1 = bottlneck_ys[0]
        z_opening_1 = z_level

        start_point_1 = XYZ(x_opening_1-DOOR_WIDTH_H, y_opening_1-DOOR_THICKNESS_H, z_opening_1)
        end_point_1 = XYZ(x_opening_1+DOOR_WIDTH_H, y_opening_1+DOOR_THICKNESS_H, z_opening+DOOR_HEIGHT)
        opening_1 = doc.Create.NewOpening(bottleneck_walls[0], start_point_1, end_point_1)

        x_opening_2 = x_main_corridor_end + (LENGTH-x_main_corridor_end)/2.
        y_opening_2 = bottlneck_ys[1]
        z_opening_2 = z_level

        start_point_2 = XYZ(x_opening_2-DOOR_WIDTH_H, y_opening_2-DOOR_THICKNESS_H, z_opening_2)
        end_point_2 = XYZ(x_opening_2+DOOR_WIDTH_H, y_opening_2+DOOR_THICKNESS_H, z_opening_2+DOOR_HEIGHT)
        opening_2 = doc.Create.NewOpening(bottleneck_walls[1], start_point_2, end_point_2)

    assert len(origin_opening_list) == len([key for key in room_dict if key.startswith('CROWDIT_ORIGIN_')])
    
#--------------------------------------------------------------
#------------------ OK NOW END THE CODE -----------------------
#--------------------------------------------------------------

TransactionManager.Instance.TransactionTaskDone()

###############################################################
# Prepare the output 
###############################################################
OUT = room_dict # , len([key for key in room_dict if key.startswith('CROWDIT_OBSTACLE_')])