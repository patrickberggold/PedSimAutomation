# site_x , site_y = [square or max 1.2/1.3 ar (y / x)]
# corr_width = [1/20 site_x/y , 1/5 site_x/y]
# num_rooms_short_side (room length) = [1.5*corr_width , 5*corr_width]
# room_width = [1.5*corr_width , 5*corr_width]

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

import random


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

DOOR_THICKNESS_H = convert_meter_to_unit(IN[6])
DOOR_HEIGHT = convert_meter_to_unit(IN[7])

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

    p2_l = XYZ(x_corridor-CORR_WIDTH/2., 2 * CORR_WIDTH, ceiling)
    p4_l = XYZ(LENGTH-(CORR_WIDTH * 2), y_corridor+CORR_WIDTH/2., ceiling)
    p2_r = XYZ(x_corridor+CORR_WIDTH/2., CORR_WIDTH, ceiling)
    p4_r = XYZ(LENGTH-(CORR_WIDTH * 2), y_corridor-CORR_WIDTH/2., ceiling)

    corridor_lines_left = [
        # Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor-CORR_WIDTH, 0, ceiling), XYZ(x_corridor-CORR_WIDTH, CORR_WIDTH, ceiling)),
        # Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor-CORR_WIDTH, CORR_WIDTH, ceiling), p2_l),
        Autodesk.Revit.DB.Line.CreateBound(p2_l, XYZ(x_corridor-CORR_WIDTH/2., y_corridor+CORR_WIDTH/2., ceiling)),
        Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor-CORR_WIDTH/2., y_corridor+CORR_WIDTH/2., ceiling), p4_l),
        # Autodesk.Revit.DB.Line.CreateBound(p4_l, XYZ(LENGTH-CORR_WIDTH, y_corridor+CORR_WIDTH, ceiling)),
        # Autodesk.Revit.DB.Line.CreateBound(XYZ(LENGTH-CORR_WIDTH, y_corridor+CORR_WIDTH, ceiling), XYZ(LENGTH, y_corridor+CORR_WIDTH, ceiling)),
    ]

    corridor_lines_right = [
        # Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor+CORR_WIDTH, 0, ceiling), XYZ(x_corridor+CORR_WIDTH, CORR_WIDTH, ceiling)),
        # Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor+CORR_WIDTH, CORR_WIDTH, ceiling), p2_r),
        Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor+CORR_WIDTH/2., 2 * CORR_WIDTH, ceiling), XYZ(x_corridor+CORR_WIDTH/2., y_corridor-CORR_WIDTH/2., ceiling)),
        Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor+CORR_WIDTH/2., y_corridor-CORR_WIDTH/2., ceiling), p4_r),
        # Autodesk.Revit.DB.Line.CreateBound(p4_r, XYZ(LENGTH-CORR_WIDTH, y_corridor-CORR_WIDTH, ceiling)),
        # Autodesk.Revit.DB.Line.CreateBound(XYZ(LENGTH-CORR_WIDTH, y_corridor-CORR_WIDTH, ceiling), XYZ(LENGTH, y_corridor-CORR_WIDTH, ceiling)),
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

    partition_lines_y_long = []
    for idy, y_pos_part in enumerate(y_pos_partitions_long):
        line_y_long = Autodesk.Revit.DB.Line.CreateBound(XYZ(0, y_pos_part, ceiling), XYZ(x_corridor-CORR_WIDTH/2., y_pos_part, ceiling))
        partition_lines.append(
            line_y_long
        )
        partition_lines_y_long.append(line_y_long)
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
            # partition_openings.append(doc.Create.NewOpening(corridor_walls_left[2], start_point_part, end_point_part))
            partition_openings.append(doc.Create.NewOpening(corridor_walls_left[0], start_point_part, end_point_part))

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

    partition_lines_y_short = []
    for idy, y_pos_part in enumerate(y_pos_partitions_short[:-1]):
        line_y_short = Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor+CORR_WIDTH/2., y_pos_part, ceiling), XYZ(x_corridor+CORR_WIDTH/2.+ROOM_WIDTH, y_pos_part, ceiling))
        partition_lines.append(
            line_y_short
        )
        partition_lines_y_short.append(line_y_short)
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
            # partition_openings.append(doc.Create.NewOpening(corridor_walls_right[2], start_point_part, end_point_part))
            partition_openings.append(doc.Create.NewOpening(corridor_walls_right[0], start_point_part, end_point_part))

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

    partition_lines_x_long = []
    for idx, x_pos_part in enumerate(x_pos_partitions_long):

        if idx > 0:
            # Do not create a wall at x = edge_room_x
            line_x_long = Autodesk.Revit.DB.Line.CreateBound(XYZ(x_pos_part, y_corridor+CORR_WIDTH/2., ceiling), XYZ(x_pos_part, WIDTH, ceiling))
            partition_lines.append(
                line_x_long
            )
            partition_lines_x_long.append(line_x_long)

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
            partition_openings.append(doc.Create.NewOpening(corridor_walls_left[1], start_point_part, end_point_part))

    partition_lines_x_short = []
    for idx, x_pos_part in enumerate(x_pos_partitions_short):
        line_x_short = Autodesk.Revit.DB.Line.CreateBound(XYZ(x_pos_part, y_corridor-CORR_WIDTH/2.-ROOM_WIDTH, ceiling), XYZ(x_pos_part, y_corridor-CORR_WIDTH/2., ceiling))
        partition_lines.append(
            line_x_short
        )
        partition_lines_x_short.append(line_x_short)
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
            partition_openings.append(doc.Create.NewOpening(corridor_walls_right[1], start_point_part, end_point_part))

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

    def create_diagonal_wall(partition_lines , p) : 
        random_number = random.randint(0 , 2)

        if random_number == 1 and p + 2 < len(partition_lines) and p > 0 :
            start_diag_point = partition_lines[p].GetEndPoint(0)
            old_end_point = partition_lines[p].GetEndPoint(1)
            end_diag_point = partition_lines[p + 1].GetEndPoint(1)

            in_y = old_end_point[1] - start_diag_point[1] < 1E-10

            random_number_diag = random.randint(0 , 2)
            if random_number_diag > 0 : #create L shape
                mid_x = (old_end_point[0] + start_diag_point[0]) / 2.
                mid_y = (old_end_point[1] + start_diag_point[1]) / 2.
                mid_z = (old_end_point[2] + start_diag_point[2]) / 2.

                if in_y : mid_x += DOOR_WIDTH_H + convert_meter_to_unit(IN[8]) / 2.
                else : mid_y += DOOR_WIDTH_H + convert_meter_to_unit(IN[8]) / 2.

                mid_point = XYZ(
                    mid_x , mid_y , mid_z
                )

                line1 = Autodesk.Revit.DB.Line.CreateBound(start_diag_point , mid_point)
                Wall.Create(doc, line1, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True)

                if random_number_diag == 2 : #w/out diagonal
                    end_x , end_y , end_z = mid_x , mid_y , mid_z
                    if in_y : 
                        end_y = end_diag_point[1]
                    else : 
                        end_x = end_diag_point[0]

                    end_l_point = XYZ(
                        end_x , end_y , end_z
                    )
                    line = Autodesk.Revit.DB.Line.CreateBound(mid_point , end_l_point)
                else : 
                    line = Autodesk.Revit.DB.Line.CreateBound(mid_point , end_diag_point)
            else : 
                line = Autodesk.Revit.DB.Line.CreateBound(start_diag_point , end_diag_point)

            return Wall.Create(doc, line, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True)
        elif random_number == 2 and p + 2 < len(partition_lines) and p > 0 :
            return None
        
        return Wall.Create(doc, partition_lines[p], default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True)


    # partition_walls = [Wall.Create(doc, partition_lines[p], default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True) for p in range(len(partition_lines))]
    # partition_walls = [create_diagonal_wall(partition_lines , p) for p in range(len(partition_lines))]

    partition_walls_y_long = [create_diagonal_wall(partition_lines_y_long , p) for p in range(len(partition_lines_y_long))]
    partition_walls_y_short = [create_diagonal_wall(partition_lines_y_short , p) for p in range(len(partition_lines_y_short))]
    partition_walls_x_long = [create_diagonal_wall(partition_lines_x_long , p) for p in range(len(partition_lines_x_long))]
    partition_walls_x_short = [create_diagonal_wall(partition_lines_x_short , p) for p in range(len(partition_lines_x_short))]

    def create_opening(partition_wall , for_y = True) :

        partition_line = partition_wall.Location.Curve

        start_point = partition_line.GetEndPoint(0)
        end_point = partition_line.GetEndPoint(1)

        mid_point_x = (end_point[0] - start_point[0]) / 2.
        mid_point_y = (end_point[1] - start_point[1]) / 2.

        if for_y :
            opening_start_point = XYZ(
                mid_point_x - DOOR_WIDTH_H , mid_point_y - DOOR_THICKNESS_H , z_level
            )
            opening_end_point = XYZ(
                mid_point_x + DOOR_WIDTH_H , mid_point_y + DOOR_THICKNESS_H , z_level + DOOR_HEIGHT
            )
        else : 
            opening_end_point = XYZ(
                mid_point_x - DOOR_THICKNESS_H , mid_point_y - DOOR_WIDTH_H , z_level
            )
            opening_start_point = XYZ(
                mid_point_x + DOOR_WIDTH_H , mid_point_y + DOOR_THICKNESS_H , z_level + DOOR_HEIGHT
            )

        return doc.Create.NewOpening(partition_wall, opening_start_point, opening_end_point)

    openings_y_long = [create_opening(partition_walls_y_long[i] , True) for i in range(len(partition_walls_y_long)) if partition_walls_y_long[i] is not None]
    openings_y_short = [create_opening(partition_walls_y_short[i] , False) for i in range(len(partition_walls_y_short)) if partition_walls_y_short[i] is not None]
    openings_x_long = [create_opening(partition_walls_x_long[i] , False) for i in range(len(partition_walls_x_long)) if partition_walls_x_long[i] is not None]
    openings_x_short = [create_opening(partition_walls_x_short[i] , False) for i in range(len(partition_walls_x_short)) if partition_walls_x_short[i] is not None]

    

    TransactionManager.Instance.TransactionTaskDone()
    # return len(partition_walls_y_long) , len(partition_walls_y_short) , len(partition_lines_x_long) , len(partition_lines_x_short)
    return room_dict

OUT = create_edge_geometry    
