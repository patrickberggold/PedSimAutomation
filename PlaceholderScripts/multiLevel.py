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

convert_meter_to_unit = UnwrapElement(IN[8][0])
convert_to_meter = UnwrapElement(IN[8][1])
find_perimeter_lines = UnwrapElement(IN[8][2])
create_slab_geometry = UnwrapElement(IN[8][3])
create_one_stair = UnwrapElement(IN[8][4])
slab_geometry_by_level = UnwrapElement(IN[8][5])
create_staircase = UnwrapElement(IN[8][6])

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
create_mode = IN[7]
DOOR_WIDTH_H = convert_meter_to_unit(float(IN[4])/2.)
OBSTACLE_WIDTH  = float(IN[5])
ROOM_WIDTH = convert_meter_to_unit(float(IN[6]))
number_story = IN[9]
# site_z = float(IN[10])
# story_z = [
#     site_z / number_story * i for i in range(number_story)
# ]

story_z = [
    2.5 * i for i in range(number_story)
]
site_z = 2.5 * number_story

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

if any(create_mode):
    geo_site = []                                                       # archive all the input data
    ref_level = []                                                      # the reference level
    bbox_site = []                                                      # bounding box of the site

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

    floor_plan_family_type = None
    for view_type in FilteredElementCollector(doc).OfClass(ViewFamilyType):
        if view_type.ViewFamily == ViewFamily.FloorPlan:
            floor_plan_family_type = view_type
            break
    
    floor_plan_views = []
    for level in allLevels[1:]:
        floor_plan_view = ViewPlan.Create(doc, floor_plan_family_type.Id, level.Id)
        floor_plan_view.Name = level.Name
        floor_plan_views.append(floor_plan_view)

    stair_thickness = (allLevels[-1].Elevation - allLevels[-2].Elevation) / 4

    # stairs = create_staircase(
    #     start_x = site_x / 8. , 
    #     start_y = site_y / 4. , 
    #     start_level = allLevels[1] , 
    #     end_x = site_x / 2. , 
    #     end_y = site_y / 2. , 
    #     end_level = allLevels[2] , 
    #     thickness = stair_thickness , 
    #     floor_type = default_floor_type , 
    #     inXDirection = False
    # )
    # stairs = create_staircase(
    #     start_x = site_x / 8. , 
    #     start_y = site_y / 4. , 
    #     start_level = allLevels[0] , 
    #     end_x = site_x / 2. , 
    #     end_y = site_y / 2. , 
    #     end_level = allLevels[1] , 
    #     thickness = stair_thickness , 
    #     floor_type = default_floor_type , 
    #     inXDirection = False
    # )

    # floor_cutting_curve = create_slab_geometry(site_x / 2. , 3 * site_x / 4. , site_y / 2. , 3 * site_y / 4. , 0.)
    # floor_cutting = doc.Create.NewOpening(doc.GetElement(floor_list[1].Id), floor_cutting_curve, False)


    
#--------------------------------------------------------------
#------------------ OK NOW END THE CODE -----------------------
#--------------------------------------------------------------

    TransactionManager.Instance.TransactionTaskDone()

###############################################################
# Prepare the output 
###############################################################
    OUT = floor_list , allLevels
