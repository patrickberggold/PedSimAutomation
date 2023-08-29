###############################################################
# Load the Libraries -> 5,6,7 = door obstacle room widths
###############################################################
import os
import clr
import sys
import math
import System

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
CORR_WIDTH = parameter_list[2]
MIN_ROOM_LENGTH = parameter_list[3]
INCLUDE_BOTTLENECK = parameter_list[4]
create_mode = IN[7][3]
DOOR_WIDTH_H = convert_meter_to_unit(float(IN[4])/2.)
OBSTACLE_WIDTH  = float(IN[5])
ROOM_WIDTH = convert_meter_to_unit(float(IN[6]))

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
    MIN_ROOM_LENGTH = convert_meter_to_unit(MIN_ROOM_LENGTH)
    
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

    LENGTH = site_x
    WIDTH = site_y
    print('x_length: ' + str(convert_to_meter(LENGTH)))
    print('y_width: ' + str(convert_to_meter(WIDTH)))
    z_level = ref_level.Elevation
    ceiling = allLevels[0].Elevation

    DOOR_HEIGHT = convert_meter_to_unit(2.2)
    DOOR_THICKNESS_H = convert_meter_to_unit(0.25)

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

    x_corridor = ROOM_WIDTH + CORR_WIDTH/2.
    y_corridor = WIDTH - ROOM_WIDTH - CORR_WIDTH/2.

    y_main_corridor = 0.5*WIDTH
    x_main_corridor_start = CORR_WIDTH
    x_main_corridor_end = LENGTH-CORR_WIDTH

    p2_l = XYZ(x_corridor-CORR_WIDTH/2., CORR_WIDTH, ceiling)
    p4_l = XYZ(LENGTH-CORR_WIDTH, y_corridor+CORR_WIDTH/2., ceiling)
    p2_r = XYZ(x_corridor+CORR_WIDTH/2., CORR_WIDTH, ceiling)
    p4_r = XYZ(LENGTH-CORR_WIDTH, y_corridor-CORR_WIDTH/2., ceiling)

    corridor_lines_left = [
        Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor-CORR_WIDTH, 0, ceiling), XYZ(x_corridor-CORR_WIDTH, CORR_WIDTH, ceiling)),
        Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor-CORR_WIDTH, CORR_WIDTH, ceiling), p2_l),
        Autodesk.Revit.DB.Line.CreateBound(p2_l, XYZ(x_corridor-CORR_WIDTH/2., y_corridor+CORR_WIDTH/2., ceiling)),
        Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor-CORR_WIDTH/2., y_corridor+CORR_WIDTH/2., ceiling), p4_l),
        Autodesk.Revit.DB.Line.CreateBound(p4_l, XYZ(LENGTH-CORR_WIDTH, y_corridor+CORR_WIDTH, ceiling)),
        Autodesk.Revit.DB.Line.CreateBound(XYZ(LENGTH-CORR_WIDTH, y_corridor+CORR_WIDTH, ceiling), XYZ(LENGTH, y_corridor+CORR_WIDTH, ceiling)),
    ]

    corridor_lines_right = [
        Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor+CORR_WIDTH, 0, ceiling), XYZ(x_corridor+CORR_WIDTH, CORR_WIDTH, ceiling)),
        Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor+CORR_WIDTH, CORR_WIDTH, ceiling), p2_r),
        Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor+CORR_WIDTH/2., CORR_WIDTH, ceiling), XYZ(x_corridor+CORR_WIDTH/2., y_corridor-CORR_WIDTH/2., ceiling)),
        Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor+CORR_WIDTH/2., y_corridor-CORR_WIDTH/2., ceiling), p4_r),
        Autodesk.Revit.DB.Line.CreateBound(p4_r, XYZ(LENGTH-CORR_WIDTH, y_corridor-CORR_WIDTH, ceiling)),
        Autodesk.Revit.DB.Line.CreateBound(XYZ(LENGTH-CORR_WIDTH, y_corridor-CORR_WIDTH, ceiling), XYZ(LENGTH, y_corridor-CORR_WIDTH, ceiling)),
    ]

    # assign room
    room_dict.update({
        'CROWDIT_DESTINATION_'+str(0): [
                (convert_to_meter(x_corridor-CORR_WIDTH)+0.5, convert_to_meter(0)+0.5),
                (convert_to_meter(x_corridor+CORR_WIDTH)-0.5, convert_to_meter(CORR_WIDTH)-0.5)
            ]
        }
    )

    room_dict.update({
        'CROWDIT_DESTINATION_'+str(1): [
                (convert_to_meter(LENGTH-CORR_WIDTH)+0.5, convert_to_meter(y_corridor-CORR_WIDTH)+0.5),
                (convert_to_meter(LENGTH)-0.5, convert_to_meter(y_corridor+CORR_WIDTH)-0.5)
            ]
        }
    )

    corridor_walls_left = [Wall.Create(doc, wall_l, default_interior_wall_type.Id, allLevels[0].Id, allLevels[1].Elevation - allLevels[0].Elevation, 0, False, True) 
        for wall_l in corridor_lines_left]
    corridor_walls_right = [Wall.Create(doc, wall_r, default_interior_wall_type.Id, allLevels[0].Id, allLevels[1].Elevation - allLevels[0].Elevation, 0, False, True) 
        for wall_r in corridor_lines_right]

    partition_openings = []

    if INCLUDE_BOTTLENECK:
        bottleneck_lines = [
            Autodesk.Revit.DB.Line.CreateBound(p2_l, p2_r),
            Autodesk.Revit.DB.Line.CreateBound(p4_l, p4_r)
        ]
        bottleneck_walls = [Wall.Create(doc, b_wall, default_interior_wall_type.Id, allLevels[0].Id, allLevels[1].Elevation - allLevels[0].Elevation, 0, False, True) 
            for b_wall in bottleneck_lines]

        # some doors
        x_door_1 = (p2_l.X + p2_r.X) / 2.
        y_door_1 = (p2_l.Y + p2_r.Y) / 2.
        x_door_2 = (p4_l.X + p4_r.X) / 2.
        y_door_2 = (p4_l.Y + p4_r.Y) / 2.
        
        start_point_1 = XYZ(x_door_1-DOOR_WIDTH_H, y_door_1-DOOR_THICKNESS_H, z_level)
        end_point_1 = XYZ(x_door_1+DOOR_WIDTH_H, y_door_1+DOOR_THICKNESS_H, z_level+DOOR_HEIGHT)
        opening_1 = doc.Create.NewOpening(bottleneck_walls[0], start_point_1, end_point_1)

        start_point_2 = XYZ(x_door_2-DOOR_THICKNESS_H, y_door_2-DOOR_WIDTH_H, z_level)
        end_point_2 = XYZ(x_door_2+DOOR_THICKNESS_H, y_door_2+DOOR_WIDTH_H, z_level+DOOR_HEIGHT)
        opening_2 = doc.Create.NewOpening(bottleneck_walls[1], start_point_2, end_point_2)

    outter_office_lines = [
        Autodesk.Revit.DB.Line.CreateBound(
            XYZ(x_corridor+ROOM_WIDTH+CORR_WIDTH/2, 0, ceiling), 
            XYZ(x_corridor+ROOM_WIDTH+CORR_WIDTH/2, y_corridor - ROOM_WIDTH - CORR_WIDTH/2., ceiling)),
        Autodesk.Revit.DB.Line.CreateBound(
            XYZ(x_corridor+ROOM_WIDTH+CORR_WIDTH/2, y_corridor - ROOM_WIDTH - CORR_WIDTH/2., ceiling),
            XYZ(LENGTH, y_corridor - ROOM_WIDTH - CORR_WIDTH/2., ceiling))
    ]
    outter_office_walls = [Wall.Create(doc, o_wall, default_interior_wall_type.Id, allLevels[0].Id, allLevels[1].Elevation - allLevels[0].Elevation, 0, False, True) 
            for o_wall in outter_office_lines]

    edge_room_x = ROOM_WIDTH # + CORR_WIDTH
    # edge room door
    """ start_point_edge = XYZ((edge_room_x+ROOM_WIDTH)/2.-DOOR_WIDTH_H, y_corridor+CORR_WIDTH/2.-DOOR_THICKNESS_H, z_level)
    end_point_edge = XYZ((edge_room_x+ROOM_WIDTH)/2.+DOOR_WIDTH_H, y_corridor+CORR_WIDTH/2.+DOOR_THICKNESS_H, z_level+DOOR_HEIGHT)
    partition_openings.append(doc.Create.NewOpening(corridor_walls_left[3], start_point_edge, end_point_edge))

    # assign room
    room_dict.update({
        'CROWDIT_ORIGIN_'+str(0): [
                (convert_to_meter(0)+0.5, convert_to_meter(y_corridor+CORR_WIDTH/2.)+0.5),
                (convert_to_meter(edge_room_x)-0.5, convert_to_meter(WIDTH)-0.5)
            ]
        }
    ) """

    # side rooms along y
    y_start_rooms = 2*CORR_WIDTH
    y_end_rooms_long = y_corridor + CORR_WIDTH/2.
    y_end_rooms_short = y_corridor - CORR_WIDTH/2.

    NUM_ROOMS_LONG_Y = int((y_end_rooms_long-y_start_rooms) / MIN_ROOM_LENGTH)
    NUM_ROOMS_SHORT_Y = int((y_end_rooms_short-y_start_rooms) / MIN_ROOM_LENGTH)
    fractions_partitions = [1./NUM_ROOMS_LONG_Y*i for i in range(NUM_ROOMS_LONG_Y+1)] if NUM_ROOMS_LONG_Y > 0 else []
    y_pos_partitions_long = [y_start_rooms + fr * (y_end_rooms_long - y_start_rooms) for fr in fractions_partitions] if len(fractions_partitions) > 0 else [y_start_rooms, y_end_rooms_long]
    fractions_partitions = [1./NUM_ROOMS_SHORT_Y*i for i in range(NUM_ROOMS_SHORT_Y+1)] if NUM_ROOMS_SHORT_Y > 0 else []
    y_pos_partitions_short = [y_start_rooms + fr * (y_end_rooms_short - y_start_rooms) for fr in fractions_partitions] if len(fractions_partitions) > 0 else [y_start_rooms, y_end_rooms_short]

    partition_lines = []

    for idy, y_pos_part in enumerate(y_pos_partitions_long):

        partition_lines.append(
            Autodesk.Revit.DB.Line.CreateBound(XYZ(0, y_pos_part, ceiling), XYZ(x_corridor-CORR_WIDTH/2., y_pos_part, ceiling))
        )
        if idy < len(y_pos_partitions_long)-1:
            # assign room
            room_dict.update({
                'CROWDIT_ORIGIN_'+str(idy): [
                        (convert_to_meter(0)+0.5, convert_to_meter(y_pos_part)+0.5),
                        (convert_to_meter(x_corridor-CORR_WIDTH/2.)-0.5, convert_to_meter(y_pos_partitions_long[idy+1])-0.5)
                    ]
                }
            )
            # a door
            start_point_part = XYZ(x_corridor-CORR_WIDTH/2.-DOOR_THICKNESS_H, (y_pos_partitions_long[idy+1]+y_pos_part)/2.-DOOR_WIDTH_H, z_level)
            end_point_part = XYZ(x_corridor-CORR_WIDTH/2.+DOOR_THICKNESS_H, (y_pos_partitions_long[idy+1]+y_pos_part)/2.+DOOR_WIDTH_H, z_level+DOOR_HEIGHT)
            partition_openings.append(doc.Create.NewOpening(corridor_walls_left[2], start_point_part, end_point_part))

            # obstacles
            if idy % 2 == 0:
                obstacle_length = 2.
                x_obst_min, x_obst_max = convert_to_meter(x_corridor-CORR_WIDTH/2.)+0.1, convert_to_meter(x_corridor-CORR_WIDTH/2.)+0.1+OBSTACLE_WIDTH
                y_obst_min, y_obst_max = convert_to_meter(y_pos_part)-obstacle_length/2., convert_to_meter(y_pos_part)+obstacle_length/2.

                room_dict.update({
                    'CROWDIT_OBSTACLE_'+str(obstacle_counter)+'_2_1_': [
                            (x_obst_min, y_obst_min),
                            (x_obst_max, y_obst_max)
                        ]
                    }
                )
                obstacle_counter += 1

    for idy, y_pos_part in enumerate(y_pos_partitions_short[:-1]):

        partition_lines.append(
            Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor+CORR_WIDTH/2., y_pos_part, ceiling), XYZ(x_corridor+CORR_WIDTH/2.+ROOM_WIDTH, y_pos_part, ceiling))
        )
        if idy < len(y_pos_partitions_short)-1:
            # assign room
            room_dict.update({
                'CROWDIT_ORIGIN_'+str(idy+len(y_pos_partitions_long)-1): [
                        (convert_to_meter(x_corridor+CORR_WIDTH/2.)+0.5, convert_to_meter(y_pos_part)+0.5),
                        (convert_to_meter(x_corridor+CORR_WIDTH/2.+ROOM_WIDTH)-0.5, convert_to_meter(y_pos_partitions_short[idy+1])-0.5)
                    ]
                }
            )
            # a door
            start_point_part = XYZ(x_corridor+CORR_WIDTH/2.-DOOR_THICKNESS_H, (y_pos_partitions_short[idy+1]+y_pos_part)/2.-DOOR_WIDTH_H, z_level)
            end_point_part = XYZ(x_corridor+CORR_WIDTH/2.+DOOR_THICKNESS_H, (y_pos_partitions_short[idy+1]+y_pos_part)/2.+DOOR_WIDTH_H, z_level+DOOR_HEIGHT)
            partition_openings.append(doc.Create.NewOpening(corridor_walls_right[2], start_point_part, end_point_part))

            # obstacles
            if idy % 2 != 0:
                obstacle_length = 2.
                x_obst_min, x_obst_max = convert_to_meter(x_corridor+CORR_WIDTH/2.)-0.1-OBSTACLE_WIDTH, convert_to_meter(x_corridor+CORR_WIDTH/2.)-0.1
                y_obst_min, y_obst_max = convert_to_meter(y_pos_part)-obstacle_length/2., convert_to_meter(y_pos_part)+obstacle_length/2.

                room_dict.update({
                    'CROWDIT_OBSTACLE_'+str(obstacle_counter)+'_2_1_': [
                            (x_obst_min, y_obst_min),
                            (x_obst_max, y_obst_max)
                        ]
                    }
                )
                obstacle_counter += 1

    # side rooms along x
    x_end_rooms = LENGTH - 2*CORR_WIDTH
    x_start_rooms_long = edge_room_x
    x_start_rooms_short = x_corridor+CORR_WIDTH/2.+ROOM_WIDTH

    NUM_ROOMS_LONG_X = int((x_end_rooms-x_start_rooms_long) / MIN_ROOM_LENGTH)
    NUM_ROOMS_SHORT_X = int((x_end_rooms-x_start_rooms_short) / MIN_ROOM_LENGTH)

    fractions_partitions = [1./NUM_ROOMS_LONG_X*i for i in range(NUM_ROOMS_LONG_X+1)] if NUM_ROOMS_LONG_X > 0 else []
    x_pos_partitions_long = [x_start_rooms_long + fr * (x_end_rooms - x_start_rooms_long) for fr in fractions_partitions] if len(fractions_partitions) > 0 else [x_start_rooms_long, x_end_rooms]
    fractions_partitions = [1./NUM_ROOMS_SHORT_X*i for i in range(NUM_ROOMS_SHORT_X+1)] if NUM_ROOMS_SHORT_X > 0 else []
    x_pos_partitions_short = [x_start_rooms_short + fr * (x_end_rooms - x_start_rooms_short) for fr in fractions_partitions] if len(fractions_partitions) > 0 else [x_start_rooms_short, x_end_rooms]

    for idx, x_pos_part in enumerate(x_pos_partitions_long):

        if idx > 0:
            # Do not create a wall at x = edge_room_x
            partition_lines.append(
                Autodesk.Revit.DB.Line.CreateBound(XYZ(x_pos_part, y_corridor+CORR_WIDTH/2., ceiling), XYZ(x_pos_part, WIDTH, ceiling))
            )
        if idx < len(x_pos_partitions_long)-1:
            # assign room
            room_dict.update({
                'CROWDIT_ORIGIN_'+str(idx+len(y_pos_partitions_short)-1+len(y_pos_partitions_long)-1): [
                        (convert_to_meter(x_pos_part)+0.5, convert_to_meter(y_corridor+CORR_WIDTH/2.)+0.5),
                        (convert_to_meter(x_pos_partitions_long[idx+1])-0.5, convert_to_meter(WIDTH)-0.5)
                    ]
                }
            )
            # a door
            start_point_part = XYZ((x_pos_partitions_long[idx+1]+x_pos_part)/2.-DOOR_WIDTH_H, y_corridor+CORR_WIDTH/2.-DOOR_THICKNESS_H, z_level)
            end_point_part = XYZ((x_pos_partitions_long[idx+1]+x_pos_part)/2.+DOOR_WIDTH_H, y_corridor+CORR_WIDTH/2.+DOOR_THICKNESS_H, z_level+DOOR_HEIGHT)
            partition_openings.append(doc.Create.NewOpening(corridor_walls_left[3], start_point_part, end_point_part))

    
    for idx, x_pos_part in enumerate(x_pos_partitions_short):

        partition_lines.append(
            Autodesk.Revit.DB.Line.CreateBound(XYZ(x_pos_part, y_corridor-CORR_WIDTH/2.-ROOM_WIDTH, ceiling), XYZ(x_pos_part, y_corridor-CORR_WIDTH/2., ceiling))
        )
        if idx < len(x_pos_partitions_short)-1:
            # assign room
            room_dict.update({
                'CROWDIT_ORIGIN_'+str(idx+len(x_pos_partitions_long)-1+len(y_pos_partitions_short)-1+len(y_pos_partitions_long)-1): [
                        (convert_to_meter(x_pos_part)+0.5, convert_to_meter(y_corridor-CORR_WIDTH/2.-ROOM_WIDTH)+0.5),
                        (convert_to_meter(x_pos_partitions_short[idx+1])-0.5, convert_to_meter(y_corridor-CORR_WIDTH/2.)-0.5)
                    ]
                }
            )
            # a door
            start_point_part = XYZ((x_pos_partitions_short[idx+1]+x_pos_part)/2.-DOOR_WIDTH_H, y_corridor-CORR_WIDTH/2.-DOOR_THICKNESS_H, z_level)
            end_point_part = XYZ((x_pos_partitions_short[idx+1]+x_pos_part)/2.+DOOR_WIDTH_H, y_corridor-CORR_WIDTH/2.+DOOR_THICKNESS_H, z_level+DOOR_HEIGHT)
            partition_openings.append(doc.Create.NewOpening(corridor_walls_right[3], start_point_part, end_point_part))

    # obstacles
    # iterate through partition walls in reverse order to generate obstacles
    for idx, x_pos_part in enumerate(x_pos_partitions_long[::-1]):
        if idx % 2 == 0 and idx < len(x_pos_partitions_long)-1:
            obstacle_length = 2.
            x_obst_min, x_obst_max = convert_to_meter(x_pos_part)-obstacle_length/2., convert_to_meter(x_pos_part)+obstacle_length/2.
            y_obst_min, y_obst_max = convert_to_meter(y_corridor+CORR_WIDTH/2.)-0.1-OBSTACLE_WIDTH, convert_to_meter(y_corridor+CORR_WIDTH/2.)-0.1

            room_dict.update({
                'CROWDIT_OBSTACLE_'+str(obstacle_counter)+'_2_1_': [
                        (x_obst_min, y_obst_min),
                        (x_obst_max, y_obst_max)
                    ]
                }
            )
            obstacle_counter += 1

    for idx, x_pos_part in enumerate(x_pos_partitions_short[::-1]):
        if idx % 2 != 0:
            obstacle_length = 2.
            x_obst_min, x_obst_max = convert_to_meter(x_pos_part)-obstacle_length/2., convert_to_meter(x_pos_part)+obstacle_length/2.
            y_obst_min, y_obst_max = convert_to_meter(y_corridor-CORR_WIDTH/2.)+0.1, convert_to_meter(y_corridor-CORR_WIDTH/2.)+0.1+OBSTACLE_WIDTH

            room_dict.update({
                'CROWDIT_OBSTACLE_'+str(obstacle_counter)+'_2_1_': [
                        (x_obst_min, y_obst_min),
                        (x_obst_max, y_obst_max)
                    ]
                }
            )
            obstacle_counter += 1


    # check if as many origin areas as room doors 
    assert len(partition_openings) == len([key for key in room_dict if key.startswith('CROWDIT_ORIGIN')])

    partition_walls = [Wall.Create(doc, p_wall, default_interior_wall_type.Id, allLevels[0].Id, allLevels[1].Elevation - allLevels[0].Elevation, 0, False, True) 
            for p_wall in partition_lines]
    

#--------------------------------------------------------------
#------------------ OK NOW END THE CODE -----------------------
#--------------------------------------------------------------

TransactionManager.Instance.TransactionTaskDone()

###############################################################
# Prepare the output 
###############################################################
OUT = room_dict
