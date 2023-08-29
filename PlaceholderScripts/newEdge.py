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
MIN_ROOM_LENGTH = convert_meter_to_unit(IN[1][1][3])
INCLUDE_BOTTLENECK = IN[1][1][5]

DOOR_WIDTH_H = convert_meter_to_unit(float(IN[2]) / 2.)
OBSTACLE_WIDTH  = convert_meter_to_unit(float(IN[3]))
ROOM_WIDTH = convert_meter_to_unit(float(IN[4]))

DOOR_THICKNESS_H = convert_meter_to_unit(0.25)
DOOR_HEIGHT = convert_meter_to_unit(2.2)

def create_edge_geometry(start_level , end_level) : 
    z_level = start_level.Elevation

    room_dict = {}
    ceiling = start_level.Elevation
    obstacle_counter = 0

    doc = DocumentManager.Instance.CurrentDBDocument
    TransactionManager.Instance.EnsureInTransaction(doc)


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

    corridor_walls_left = [Wall.Create(doc, wall_l, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True) 
        for wall_l in corridor_lines_left]
    corridor_walls_right = [Wall.Create(doc, wall_r, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True) 
        for wall_r in corridor_lines_right]

    partition_openings = []

    if INCLUDE_BOTTLENECK:
        bottleneck_lines = [
            Autodesk.Revit.DB.Line.CreateBound(p2_l, p2_r),
            Autodesk.Revit.DB.Line.CreateBound(p4_l, p4_r)
        ]
        bottleneck_walls = [Wall.Create(doc, b_wall, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True) 
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
    outter_office_walls = [Wall.Create(doc, o_wall, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True) 
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

    partition_walls = [Wall.Create(doc, p_wall, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True) 
            for p_wall in partition_lines]
    

    TransactionManager.Instance.TransactionTaskDone()

    return room_dict

OUT = create_edge_geometry    
