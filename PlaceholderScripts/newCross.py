import clr

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
from Autodesk.Revit.DB.Architecture import *


convert_meter_to_unit = IN[5][0]
convert_to_meter = IN[5][1]

default_interior_wall_type = UnwrapElement(IN[0])

LENGTH = convert_meter_to_unit(IN[1][1][0])
WIDTH = convert_meter_to_unit(IN[1][1][1])
CORR_WIDTH = convert_meter_to_unit(IN[1][1][2])
NUM_ROOMS_PER_SIDE = IN[1][1][3]
INCLUDE_BOTTLENECK = IN[1][1][5]

DOOR_WIDTH_H = convert_meter_to_unit(float(IN[2]) / 2.)
OBSTACLE_WIDTH  = convert_meter_to_unit(float(IN[3]))
ROOM_WIDTH = convert_meter_to_unit(float(IN[4]))

DOOR_THICKNESS_H = convert_meter_to_unit(0.25)
DOOR_HEIGHT = convert_meter_to_unit(2.2)
MIN_ROOM_WIDTH = convert_meter_to_unit(4.)


def create_cross_geometry(start_level , end_level) : 
    z_level = start_level.Elevation

    room_dict = {}
    ceiling = start_level.Elevation
    obstacle_counter = 0

    doc = DocumentManager.Instance.CurrentDBDocument
    TransactionManager.Instance.EnsureInTransaction(doc)


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
    
    corridor_walls_left = [Wall.Create(doc, wall_l, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True) 
        for wall_l in corridor_lines_left]
    corridor_walls_right = [Wall.Create(doc, wall_r, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True) 
        for wall_r in corridor_lines_right]

    if INCLUDE_BOTTLENECK:
        bottleneck_lines = [
            Autodesk.Revit.DB.Line.CreateBound(p2_l, p2_r),
            Autodesk.Revit.DB.Line.CreateBound(p3_l, p3_r)
        ]
        bottleneck_walls = [Wall.Create(doc, b_wall, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True) 
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

    middle_walls_left = [Wall.Create(doc, wall_l, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True) 
        for wall_l in middle_lines_left
    ]
    middle_walls_right = [Wall.Create(doc, wall_r, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True) 
        for wall_r in middle_lines_right
    ]
    

    TransactionManager.Instance.TransactionTaskDone()

    return room_dict

OUT = create_cross_geometry    
