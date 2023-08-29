###############################################################
# Load the Libraries Cross 5,6 = door obstacle widths
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
CORR_WIDTH = parameter_list[2] # convert_meter_to_unit(3)
NUM_ROOMS_PER_SIDE = parameter_list[3]
INCLUDE_BOTTLENECK = parameter_list[4]
create_mode = IN[7][1]
DOOR_WIDTH_H = convert_meter_to_unit(float(IN[4])/2.)
OBSTACLE_WIDTH = float(IN[5])

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
    # convert to Revit units
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

    LENGTH = site_x
    WIDTH = site_y
    print('x_length: ' + str(convert_to_meter(LENGTH)))
    print('y_width: ' + str(convert_to_meter(WIDTH)))
    z_level = ref_level.Elevation
    ceiling = allLevels[0].Elevation

    obstacle_counter = 0

    # DOOR_WIDTH_H = convert_meter_to_unit(0.5)
    DOOR_HEIGHT = convert_meter_to_unit(2.2)
    DOOR_THICKNESS_H = convert_meter_to_unit(0.25)

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

    MIN_ROOM_WIDTH = convert_meter_to_unit(4.)

    y_main_corridor = 0.5*WIDTH
    x_main_corridor_start = CORR_WIDTH
    x_main_corridor_end = LENGTH-CORR_WIDTH
    
    x_cross_start = x_main_corridor_start + 2*CORR_WIDTH
    x_cross_end = x_main_corridor_end - 2*CORR_WIDTH

    fractions_partitions = [1./NUM_ROOMS_PER_SIDE*i for i in range(NUM_ROOMS_PER_SIDE+1)] # if NUM_ROOMS_PER_SIDE > 1 else [0.5]
    x_pos_partitions = [x_cross_start + fr * (x_cross_end - x_cross_start) for fr in fractions_partitions]

    middle_lines_left = []
    middle_lines_right = []

    p2_l = XYZ(x_main_corridor_start, y_main_corridor+CORR_WIDTH/2., ceiling)
    p3_l = XYZ(x_main_corridor_end, y_main_corridor+CORR_WIDTH/2., ceiling)
    p2_r = XYZ(x_main_corridor_start, y_main_corridor-CORR_WIDTH/2., ceiling)
    p3_r = XYZ(x_main_corridor_end, y_main_corridor-CORR_WIDTH/2., ceiling)

    corridor_lines_left = [
        Autodesk.Revit.DB.Line.CreateBound(XYZ(0, y_main_corridor+CORR_WIDTH, ceiling), XYZ(x_main_corridor_start, y_main_corridor+CORR_WIDTH, ceiling)),
        Autodesk.Revit.DB.Line.CreateBound(XYZ(x_main_corridor_start, y_main_corridor+CORR_WIDTH, ceiling), p2_l),
        Autodesk.Revit.DB.Line.CreateBound(p2_l, p3_l),
        Autodesk.Revit.DB.Line.CreateBound(p3_l, XYZ(x_main_corridor_end, y_main_corridor+CORR_WIDTH, ceiling)),
        Autodesk.Revit.DB.Line.CreateBound(XYZ(x_main_corridor_end, y_main_corridor+CORR_WIDTH, ceiling), XYZ(LENGTH, y_main_corridor+CORR_WIDTH, ceiling)),
    ]

    corridor_lines_right = [
        Autodesk.Revit.DB.Line.CreateBound(XYZ(0, y_main_corridor-CORR_WIDTH, ceiling), XYZ(x_main_corridor_start, y_main_corridor-CORR_WIDTH, ceiling)),
        Autodesk.Revit.DB.Line.CreateBound(XYZ(x_main_corridor_start, y_main_corridor-CORR_WIDTH, ceiling), p2_r),
        Autodesk.Revit.DB.Line.CreateBound(p2_r, p3_r),
        Autodesk.Revit.DB.Line.CreateBound(p3_r, XYZ(x_main_corridor_end, y_main_corridor-CORR_WIDTH, ceiling)),
        Autodesk.Revit.DB.Line.CreateBound(XYZ(x_main_corridor_end, y_main_corridor-CORR_WIDTH, ceiling), XYZ(LENGTH, y_main_corridor-CORR_WIDTH, ceiling)),
    ]
    
    corridor_walls_left = [Wall.Create(doc, wall_l, default_interior_wall_type.Id, allLevels[0].Id, allLevels[1].Elevation - allLevels[0].Elevation, 0, False, True) 
        for wall_l in corridor_lines_left]
    corridor_walls_right = [Wall.Create(doc, wall_r, default_interior_wall_type.Id, allLevels[0].Id, allLevels[1].Elevation - allLevels[0].Elevation, 0, False, True) 
        for wall_r in corridor_lines_right]

    if INCLUDE_BOTTLENECK:
        bottleneck_lines = [
            Autodesk.Revit.DB.Line.CreateBound(p2_l, p2_r),
            Autodesk.Revit.DB.Line.CreateBound(p3_l, p3_r)
        ]
        bottleneck_walls = [Wall.Create(doc, b_wall, default_interior_wall_type.Id, allLevels[0].Id, allLevels[1].Elevation - allLevels[0].Elevation, 0, False, True) 
            for b_wall in bottleneck_lines]

        # some doors
        x_door_1 = x_main_corridor_start
        x_door_2 = x_main_corridor_end
        
        start_point_1 = XYZ(x_door_1-DOOR_THICKNESS_H, y_main_corridor-DOOR_WIDTH_H, z_level)
        end_point_1 = XYZ(x_door_1+DOOR_THICKNESS_H, y_main_corridor+DOOR_WIDTH_H, z_level+DOOR_HEIGHT)
        opening_1 = doc.Create.NewOpening(bottleneck_walls[0], start_point_1, end_point_1)

        start_point_2 = XYZ(x_door_2-DOOR_THICKNESS_H, y_main_corridor-DOOR_WIDTH_H, z_level)
        end_point_2 = XYZ(x_door_2+DOOR_THICKNESS_H, y_main_corridor+DOOR_WIDTH_H, z_level+DOOR_HEIGHT)
        opening_2 = doc.Create.NewOpening(bottleneck_walls[1], start_point_2, end_point_2)
    
    # destination areas
    room_x_min, room_x_max = 0, x_main_corridor_start
    room_y_min, room_y_max = y_main_corridor-CORR_WIDTH, y_main_corridor+CORR_WIDTH
    room_dict.update({
        'CROWDIT_DESTINATION_0': [
                (convert_to_meter(room_x_min)+0.5, convert_to_meter(room_y_min)+0.5),
                (convert_to_meter(room_x_max)-0.5, convert_to_meter(room_y_max)-0.5)
            ]
        }
    )

    room_x_min, room_x_max = x_main_corridor_end, LENGTH
    room_y_min, room_y_max = y_main_corridor-CORR_WIDTH, y_main_corridor+CORR_WIDTH
    room_dict.update({
        'CROWDIT_DESTINATION_1': [
                (convert_to_meter(room_x_min)+0.5, convert_to_meter(room_y_min)+0.5),
                (convert_to_meter(room_x_max)-0.5, convert_to_meter(room_y_max)-0.5)
            ]
        }
    )

    for idx, x_pos_part in enumerate(x_pos_partitions):

        middle_lines_left.append(
                Autodesk.Revit.DB.Line.CreateBound(XYZ(x_pos_part, y_main_corridor+CORR_WIDTH/2., ceiling), XYZ(x_pos_part, WIDTH, ceiling))
        )
        middle_lines_right.append(
            Autodesk.Revit.DB.Line.CreateBound(XYZ(x_pos_part, y_main_corridor-CORR_WIDTH/2., ceiling), XYZ(x_pos_part, 0, ceiling))
        )

        # some doors
        if idx < len(x_pos_partitions)-1:
            x_opening = (x_pos_partitions[idx]+x_pos_partitions[idx+1]) / 2.
            y_opening_l = y_main_corridor+CORR_WIDTH/2.
            y_opening_r = y_main_corridor-CORR_WIDTH/2.
            z_opening = z_level

            # left door
            start_point_l = XYZ(x_opening-DOOR_WIDTH_H, y_opening_l-DOOR_THICKNESS_H, z_opening)
            end_point_l = XYZ(x_opening+DOOR_WIDTH_H, y_opening_l+DOOR_THICKNESS_H, z_opening+DOOR_HEIGHT)
            opening_l = doc.Create.NewOpening(corridor_walls_left[2], start_point_l, end_point_l)

            # right door
            start_point_r = XYZ(x_opening-DOOR_WIDTH_H, y_opening_r-DOOR_THICKNESS_H, z_opening)
            end_point_r = XYZ(x_opening+DOOR_WIDTH_H, y_opening_r+DOOR_THICKNESS_H, z_opening+DOOR_HEIGHT)
            opening_r = doc.Create.NewOpening(corridor_walls_right[2], start_point_r, end_point_r)

            # assign areas
            room_x_min, room_x_max = min(x_pos_partitions[idx], x_pos_partitions[idx+1]), max(x_pos_partitions[idx], x_pos_partitions[idx+1])
            room_y_min1, room_y_max1 = 0, y_main_corridor-CORR_WIDTH/2.
            room_y_min2, room_y_max2 = y_main_corridor+CORR_WIDTH/2., WIDTH

            room_dict.update({
                'CROWDIT_ORIGIN_'+str(2*idx): [
                        (convert_to_meter(room_x_min)+0.5, convert_to_meter(room_y_min1)+0.5),
                        (convert_to_meter(room_x_max)-0.5, convert_to_meter(room_y_max1)-0.5)
                    ]
                }
            )

            room_dict.update({
                'CROWDIT_ORIGIN_'+str(1+2*idx): [
                        (convert_to_meter(room_x_min)+0.5, convert_to_meter(room_y_min2)+0.5),
                        (convert_to_meter(room_x_max)-0.5, convert_to_meter(room_y_max2)-0.5)
                    ]
                }
            )
        
        # obstacles
        obstacle_length = 2.

        x_obst_min, x_obst_max = convert_to_meter(x_pos_part)-obstacle_length/2., convert_to_meter(x_pos_part)+obstacle_length/2.
        y_obst_min = convert_to_meter(y_main_corridor+CORR_WIDTH/2.)-0.1-OBSTACLE_WIDTH if idx%2 == 0 else convert_to_meter(y_main_corridor-CORR_WIDTH/2.)+0.1
        y_obst_max = convert_to_meter(y_main_corridor+CORR_WIDTH/2.)-0.1 if idx%2 == 0 else convert_to_meter(y_main_corridor-CORR_WIDTH/2.)+0.1+OBSTACLE_WIDTH

        room_dict.update({
            'CROWDIT_OBSTACLE_'+str(obstacle_counter)+'_2_1_': [
                    (x_obst_min, y_obst_min),
                    (x_obst_max, y_obst_max)
                ]
            }
        )
        obstacle_counter += 1

    middle_walls_left = [Wall.Create(doc, wall_l, default_interior_wall_type.Id, allLevels[0].Id, allLevels[1].Elevation - allLevels[0].Elevation, 0, False, True) 
        for wall_l in middle_lines_left
    ]
    middle_walls_right = [Wall.Create(doc, wall_r, default_interior_wall_type.Id, allLevels[0].Id, allLevels[1].Elevation - allLevels[0].Elevation, 0, False, True) 
        for wall_r in middle_lines_right
    ]


#--------------------------------------------------------------
#------------------ OK NOW END THE CODE -----------------------
#--------------------------------------------------------------

TransactionManager.Instance.TransactionTaskDone()

###############################################################
# Prepare the output 
###############################################################
OUT = room_dict
