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
default_exterior_wall_type = UnwrapElement(IN[11])
exterior_wall_width = default_exterior_wall_type.Width

LENGTH = convert_meter_to_unit(IN[1][1][0])
WIDTH = convert_meter_to_unit(IN[1][1][1]) - exterior_wall_width
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

    def create_diagonal_wall(partition_lines , random_list , p) : 
        random_number = random_list[p]

        if random_number : 
            return Wall.Create(doc, partition_lines[p], default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True)
        return None

    def create_diagonal_wall_old(partition_lines , first_random , second_random , p) : 
        # random_number = random.randint(0 , 2)
        random_number = first_random[p]

        if random_number == 1 and p + 2 < len(partition_lines) and p > 0 :
            start_diag_point = partition_lines[p].GetEndPoint(0)
            old_end_point = partition_lines[p].GetEndPoint(1)
            end_diag_point = partition_lines[p + 1].GetEndPoint(1)

            in_y = old_end_point[1] - start_diag_point[1] < 1E-10

            # random_number_diag = random.randint(0 , 2)
            random_number_diag = second_random[p]
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

    x_corridor = ROOM_WIDTH + CORR_WIDTH/2.
    y_corridor = WIDTH - ROOM_WIDTH - CORR_WIDTH/2.

    y_main_corridor = 0.5*WIDTH
    x_main_corridor_start = CORR_WIDTH
    x_main_corridor_end = LENGTH-CORR_WIDTH

    p2_l = XYZ(x_corridor-CORR_WIDTH/2., y_corridor - 4 * CORR_WIDTH, ceiling)
    p4_l = XYZ(LENGTH-(CORR_WIDTH * 2), y_corridor+CORR_WIDTH/2., ceiling)
    p2_r = XYZ(x_corridor+CORR_WIDTH/2., CORR_WIDTH, ceiling)
    p4_r = XYZ(LENGTH-(CORR_WIDTH * 2), y_corridor-CORR_WIDTH/2., ceiling)

    corridor_lines_left = [
        Autodesk.Revit.DB.Line.CreateBound(p2_l, XYZ(x_corridor-CORR_WIDTH/2., y_corridor+CORR_WIDTH/2., ceiling)),
        Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor-CORR_WIDTH/2., y_corridor+CORR_WIDTH/2., ceiling), p4_l)
    ]

    corridor_lines_right = [
        Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor+CORR_WIDTH/2., y_corridor - 4 * CORR_WIDTH , ceiling), XYZ(x_corridor+CORR_WIDTH/2., y_corridor-CORR_WIDTH/2., ceiling)),
        Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor+CORR_WIDTH/2., y_corridor-CORR_WIDTH/2., ceiling), p4_r)
    ]

    # assign room
    # room_dict.update({
    #     'CROWDIT_DESTINATION_'+str(0): [
    #             (convert_to_meter(x_corridor-CORR_WIDTH)+0.5, convert_to_meter(0)+0.5),
    #             (convert_to_meter(x_corridor+CORR_WIDTH)-0.5, convert_to_meter(CORR_WIDTH)-0.5)
    #         ]
    #     }
    # )

    # room_dict.update({
    #     'CROWDIT_DESTINATION_'+str(1): [
    #             (convert_to_meter(LENGTH-CORR_WIDTH)+0.5, convert_to_meter(y_corridor-CORR_WIDTH)+0.5),
    #             (convert_to_meter(LENGTH)-0.5, convert_to_meter(y_corridor+CORR_WIDTH)-0.5)
    #         ]
    #     }
    # )

    corridor_walls_left = [Wall.Create(doc, wall_l, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True) 
        for wall_l in corridor_lines_left]
    corridor_walls_right = [Wall.Create(doc, wall_r, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True) 
        for wall_r in corridor_lines_right]

    partition_openings = []

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

    edge_room_x = ROOM_WIDTH

    # side rooms along y
    y_start_rooms = 2*CORR_WIDTH
    y_start_rooms = y_corridor - 4. * CORR_WIDTH
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
            # room_dict.update({
            #     'CROWDIT_ORIGIN_'+str(idy): [
            #             (convert_to_meter(0)+0.5, convert_to_meter(y_pos_part)+0.5),
            #             (convert_to_meter(x_corridor-CORR_WIDTH/2.)-0.5, convert_to_meter(y_pos_partitions_long[idy+1])-0.5)
            #         ]
            #     }
            # )
            # a door
            start_point_part = XYZ(x_corridor-CORR_WIDTH/2.-DOOR_THICKNESS_H, (y_pos_partitions_long[idy+1]+y_pos_part)/2.-DOOR_WIDTH_H, z_level)
            end_point_part = XYZ(x_corridor-CORR_WIDTH/2.+DOOR_THICKNESS_H, (y_pos_partitions_long[idy+1]+y_pos_part)/2.+DOOR_WIDTH_H, z_level+DOOR_HEIGHT)
            partition_openings.append(doc.Create.NewOpening(corridor_walls_left[0], start_point_part, end_point_part))

            # obstacles
            if idy % 2 == 0:
                obstacle_length = 2.
                x_obst_min, x_obst_max = convert_to_meter(x_corridor-CORR_WIDTH/2.)+0.1, convert_to_meter(x_corridor-CORR_WIDTH/2.)+0.1+OBSTACLE_WIDTH
                y_obst_min, y_obst_max = convert_to_meter(y_pos_part)-obstacle_length/2., convert_to_meter(y_pos_part)+obstacle_length/2.

                # room_dict.update({
                #     'CROWDIT_OBSTACLE_'+str(obstacle_counter)+'_2_1_': [
                #             (x_obst_min, y_obst_min),
                #             (x_obst_max, y_obst_max)
                #         ]
                #     }
                # )
                # obstacle_counter += 1

    partition_lines_y_short = []
    for idy, y_pos_part in enumerate(y_pos_partitions_short[:-1]):
        line_y_short = Autodesk.Revit.DB.Line.CreateBound(XYZ(x_corridor+CORR_WIDTH/2., y_pos_part, ceiling), XYZ(x_corridor+CORR_WIDTH/2.+ROOM_WIDTH, y_pos_part, ceiling))
        partition_lines.append(
            line_y_short
        )
        partition_lines_y_short.append(line_y_short)
        if idy < len(y_pos_partitions_short)-1:
            # # assign room
            # room_dict.update({
            #     'CROWDIT_ORIGIN_'+str(idy+len(y_pos_partitions_long)-1): [
            #             (convert_to_meter(x_corridor+CORR_WIDTH/2.)+0.5, convert_to_meter(y_pos_part)+0.5),
            #             (convert_to_meter(x_corridor+CORR_WIDTH/2.+ROOM_WIDTH)-0.5, convert_to_meter(y_pos_partitions_short[idy+1])-0.5)
            #         ]
            #     }
            # )
            # a door
            start_point_part = XYZ(x_corridor+CORR_WIDTH/2.-DOOR_THICKNESS_H, (y_pos_partitions_short[idy+1]+y_pos_part)/2.-DOOR_WIDTH_H, z_level)
            end_point_part = XYZ(x_corridor+CORR_WIDTH/2.+DOOR_THICKNESS_H, (y_pos_partitions_short[idy+1]+y_pos_part)/2.+DOOR_WIDTH_H, z_level+DOOR_HEIGHT)
            partition_openings.append(doc.Create.NewOpening(corridor_walls_right[0], start_point_part, end_point_part))

            # obstacles
            if idy % 2 != 0:
                obstacle_length = 2.
                x_obst_min, x_obst_max = convert_to_meter(x_corridor+CORR_WIDTH/2.)-0.1-OBSTACLE_WIDTH, convert_to_meter(x_corridor+CORR_WIDTH/2.)-0.1
                y_obst_min, y_obst_max = convert_to_meter(y_pos_part)-obstacle_length/2., convert_to_meter(y_pos_part)+obstacle_length/2.

                # room_dict.update({
                #     'CROWDIT_OBSTACLE_'+str(obstacle_counter)+'_2_1_': [
                #             (x_obst_min, y_obst_min),
                #             (x_obst_max, y_obst_max)
                #         ]
                #     }
                # )
                # obstacle_counter += 1

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
            # room_dict.update({
            #     'CROWDIT_ORIGIN_'+str(idx+len(y_pos_partitions_short)-1+len(y_pos_partitions_long)-1): [
            #             (convert_to_meter(x_pos_part)+0.5, convert_to_meter(y_corridor+CORR_WIDTH/2.)+0.5),
            #             (convert_to_meter(x_pos_partitions_long[idx+1])-0.5, convert_to_meter(WIDTH)-0.5)
            #         ]
            #     }
            # )
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
            # # assign room
            # room_dict.update({
            #     'CROWDIT_ORIGIN_'+str(idx+len(x_pos_partitions_long)-1+len(y_pos_partitions_short)-1+len(y_pos_partitions_long)-1): [
            #             (convert_to_meter(x_pos_part)+0.5, convert_to_meter(y_corridor-CORR_WIDTH/2.-ROOM_WIDTH)+0.5),
            #             (convert_to_meter(x_pos_partitions_short[idx+1])-0.5, convert_to_meter(y_corridor-CORR_WIDTH/2.)-0.5)
            #         ]
            #     }
            # )
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

            # room_dict.update({
            #     'CROWDIT_OBSTACLE_'+str(obstacle_counter)+'_2_1_': [
            #             (x_obst_min, y_obst_min),
            #             (x_obst_max, y_obst_max)
            #         ]
            #     }
            # )
            # obstacle_counter += 1

    for idx, x_pos_part in enumerate(x_pos_partitions_short[::-1]):
        if idx % 2 != 0:
            obstacle_length = 2.
            x_obst_min, x_obst_max = convert_to_meter(x_pos_part)-obstacle_length/2., convert_to_meter(x_pos_part)+obstacle_length/2.
            y_obst_min, y_obst_max = convert_to_meter(y_corridor-CORR_WIDTH/2.)+0.1, convert_to_meter(y_corridor-CORR_WIDTH/2.)+0.1+OBSTACLE_WIDTH

            # room_dict.update({
            #     'CROWDIT_OBSTACLE_'+str(obstacle_counter)+'_2_1_': [
            #             (x_obst_min, y_obst_min),
            #             (x_obst_max, y_obst_max)
            #         ]
            #     }
            # )
            # obstacle_counter += 1

    # check if as many origin areas as room doors 
    # assert len(partition_openings) == len([key for key in room_dict if key.startswith('CROWDIT_ORIGIN')])

    first_random_list_x_long = []
    for i in range(len(partition_lines_x_long)) : 
        random_number = random.randint(0 , 1)
        if i > 1 :
            if first_random_list_x_long[i - 1] == 0 and first_random_list_x_long[i - 2] == 0 : 
                random_number = 1
        elif i == 0 or i == len(partition_lines_x_long) - 1 : random_number = 1

        first_random_list_x_long.append(random_number)

    first_random_list_x_short = []
    for i in range(len(partition_lines_x_short)) : 
        random_number = random.randint(0 , 1)
        if i > 1 :
            if first_random_list_x_short[i - 1] == 0 and first_random_list_x_short[i - 2] == 0 : 
                random_number = 1
        elif i == 0 or i == len(partition_lines_x_short) - 1 : random_number = 1

        first_random_list_x_short.append(random_number)

    first_random_list_y_long = []
    for i in range(len(partition_lines_y_long)) : 
        random_number = random.randint(0 , 1)
        if i > 1 :
            if first_random_list_y_long[i - 1] == 0 and first_random_list_y_long[i - 2] == 0 : 
                random_number = 1
        elif i == 0 or i == len(partition_lines_y_long) - 1 : random_number = 1

        first_random_list_y_long.append(random_number)

    first_random_list_y_short = []
    for i in range(len(partition_lines_y_short)) : 
        random_number = random.randint(0 , 1)
        if i > 1 :
            if first_random_list_y_short[i - 1] == 0 and first_random_list_y_short[i - 2] == 0: 
                random_number = 1
        elif i == 0 or i == len(partition_lines_y_short) - 1 : random_number = 1

        first_random_list_y_short.append(random_number)

    spatial_buffer = IN[10]
    source_counter = 0

    partition_walls_y_long = []
    wall_counter = 0
    for p in range(len(partition_lines_y_long)) : 
        wall = create_diagonal_wall(partition_lines_y_long , first_random_list_y_long , p)
        if wall != None : 
            partition_walls_y_long.append(wall)
            wall_counter = len(partition_walls_y_long)

            if wall_counter > 1 : 
                curve_iplus1 = partition_walls_y_long[wall_counter - 1].Location.Curve
                curve_i = partition_walls_y_long[wall_counter - 2].Location.Curve
                x_i = convert_to_meter(curve_i.GetEndPoint(0)[0] + exterior_wall_width / 2.)
                y_i = convert_to_meter(curve_i.GetEndPoint(0)[1] + exterior_wall_width / 2.)
                x_iplus1 = convert_to_meter(curve_iplus1.GetEndPoint(1)[0] -  exterior_wall_width / 2.)
                y_iplus1 = convert_to_meter(curve_iplus1.GetEndPoint(1)[1] -  exterior_wall_width / 2.)

                source_bbox = [
                    (x_i + spatial_buffer , y_i + spatial_buffer) , 
                    (x_iplus1 - spatial_buffer , y_iplus1 - spatial_buffer)
                ]

                room_dict.update({
                    f"CROWDIT_ORIGIN_{source_counter}" : source_bbox
                })
                source_counter += 1

            # if wall_counter == len(partition_lines_y_long) - 1 : 
            #     curve_iplus1 = partition_walls_x_long[0].Location.Curve
            #     curve_i = partition_walls_y_long[wall_counter - 1].Location.Curve

            #     x_i = convert_to_meter(curve_i.GetEndPoint(0)[0] + exterior_wall_width / 2.)
            #     y_i = convert_to_meter(curve_i.GetEndPoint(0)[1] + exterior_wall_width / 2.)
            #     x_iplus1 = convert_to_meter(curve_iplus1.GetEndPoint(1)[0] -  exterior_wall_width / 2.)
            #     y_iplus1 = convert_to_meter(curve_iplus1.GetEndPoint(1)[1])

            #     source_bbox = [
            #         (x_i + spatial_buffer , y_i + spatial_buffer) , 
            #         (x_iplus1 - spatial_buffer , y_iplus1 - spatial_buffer)
            #     ]

            #     room_dict.update({
            #         f"CROWDIT_ORIGIN_{source_counter}" : source_bbox
            #     })
            #     source_counter += 1

    
    partition_walls_x_long = []
    wall_counter = 0
    for p in range(len(partition_lines_x_long)) : 
        wall = create_diagonal_wall(partition_lines_x_long , first_random_list_x_long , p)
        if wall != None : 
            partition_walls_x_long.append(wall)
            wall_counter = len(partition_walls_x_long)

            if wall_counter > 1 : 
                curve_iplus1 = partition_walls_x_long[wall_counter - 1].Location.Curve
                curve_i = partition_walls_x_long[wall_counter - 2].Location.Curve
                x_i = convert_to_meter(curve_i.GetEndPoint(0)[0] + exterior_wall_width / 2.)
                y_i = convert_to_meter(curve_i.GetEndPoint(0)[1] + exterior_wall_width / 2.)
                x_iplus1 = convert_to_meter(curve_iplus1.GetEndPoint(1)[0] -  exterior_wall_width / 2.)
                y_iplus1 = convert_to_meter(curve_iplus1.GetEndPoint(1)[1] -  exterior_wall_width / 2.)

                source_bbox = [
                    (x_i + spatial_buffer , y_i + spatial_buffer) , 
                    (x_iplus1 - spatial_buffer , y_iplus1 - spatial_buffer)
                ]

                room_dict.update({
                    f"CROWDIT_ORIGIN_{source_counter}" : source_bbox
                })
                source_counter += 1

    partition_walls_x_short = []
    wall_counter = 0
    for p in range(len(partition_lines_x_short)) : 
        wall = create_diagonal_wall(partition_lines_x_short , first_random_list_x_short , p)
        if wall != None : 
            partition_walls_x_short.append(wall)
            wall_counter = len(partition_walls_x_short)

            if wall_counter > 1 : 
                curve_iplus1 = partition_walls_x_short[wall_counter - 1].Location.Curve
                curve_i = partition_walls_x_short[wall_counter - 2].Location.Curve
                x_i = convert_to_meter(curve_i.GetEndPoint(0)[0] +  exterior_wall_width / 2.)
                y_i = convert_to_meter(curve_i.GetEndPoint(0)[1] +  exterior_wall_width / 2.)
                x_iplus1 = convert_to_meter(curve_iplus1.GetEndPoint(1)[0] - exterior_wall_width / 2.)
                y_iplus1 = convert_to_meter(curve_iplus1.GetEndPoint(1)[1] - exterior_wall_width / 2.)

                source_bbox = [
                    (x_i + spatial_buffer , y_i + spatial_buffer) , 
                    (x_iplus1 - spatial_buffer , y_iplus1 - spatial_buffer)
                ]

                room_dict.update({
                    f"CROWDIT_ORIGIN_{source_counter}" : source_bbox
                })
                source_counter += 1

    partition_walls_y_short = []
    wall_counter = 0
    for p in range(len(partition_lines_y_short)) : 
        wall = create_diagonal_wall(partition_lines_y_short , first_random_list_y_short , p)
        if wall != None : 
            partition_walls_y_short.append(wall)
            wall_counter = len(partition_walls_y_short)

            if wall_counter > 1 : 
                curve_iplus1 = partition_walls_y_short[wall_counter - 1].Location.Curve
                curve_i = partition_walls_y_short[wall_counter - 2].Location.Curve
                x_i = convert_to_meter(curve_i.GetEndPoint(0)[0] +  exterior_wall_width / 2.)
                y_i = convert_to_meter(curve_i.GetEndPoint(0)[1] +  exterior_wall_width / 2.)
                x_iplus1 = convert_to_meter(curve_iplus1.GetEndPoint(1)[0] - exterior_wall_width / 2.)
                y_iplus1 = convert_to_meter(curve_iplus1.GetEndPoint(1)[1] - exterior_wall_width / 2.)

                source_bbox = [
                    (x_i + spatial_buffer , y_i + spatial_buffer) , 
                    (x_iplus1 - spatial_buffer , y_iplus1 - spatial_buffer)
                ]

                room_dict.update({
                    f"CROWDIT_ORIGIN_{source_counter}" : source_bbox
                })
                source_counter += 1

        if p == len(partition_lines_y_short) - 1 : 
            curve_iplus1 = partition_walls_x_short[0].Location.Curve
            curve_i = partition_walls_y_short[wall_counter - 1].Location.Curve

            x_i = convert_to_meter(curve_i.GetEndPoint(0)[0] +  exterior_wall_width / 2.)
            y_i = convert_to_meter(curve_i.GetEndPoint(0)[1] +  exterior_wall_width / 2.)
            x_iplus1 = convert_to_meter(curve_iplus1.GetEndPoint(1)[0] - exterior_wall_width / 2.)
            y_iplus1 = convert_to_meter(curve_iplus1.GetEndPoint(1)[1] - exterior_wall_width / 2.)

            source_bbox = [
                (x_i + spatial_buffer , y_i + spatial_buffer) , 
                (x_iplus1 - spatial_buffer , y_iplus1 - spatial_buffer)
            ]

            room_dict.update({
                f"CROWDIT_ORIGIN_{source_counter}" : source_bbox
            })
            source_counter += 1

    if INCLUDE_BOTTLENECK and len(partition_lines_y_short) > 2 and len(partition_lines_x_short) > 2 : 
        # first_index = len(partition_lines_y_short) - 3

        # bottleneck_line_bottom = Autodesk.Revit.DB.Line.CreateBound(
        #     partition_lines_y_long[first_index].GetEndPoint(1) , 
        #     partition_lines_y_short[first_index].GetEndPoint(0)
        # )
        bottleneck_line_mid = Autodesk.Revit.DB.Line.CreateBound(
            partition_lines_x_short[1].GetEndPoint(1),
            partition_lines_x_long[-(len(partition_lines_x_short) - 1)].GetEndPoint(0)
        )
        # bottleneck_line_top = Autodesk.Revit.DB.Line.CreateBound(
        #     partition_lines_x_short[-3].GetEndPoint(1),
        #     partition_lines_x_long[-3].GetEndPoint(0)
        # )

        Wall.Create(doc, bottleneck_line_mid, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True)

    #start_wall
    start_wall_start_point = XYZ(0. , y_corridor - 6 * CORR_WIDTH , ceiling)
    start_wall_end_point = XYZ(x_corridor+CORR_WIDTH/2. + ROOM_WIDTH , y_corridor - 6 * CORR_WIDTH , ceiling)
    start_wall_line = Autodesk.Revit.DB.Line.CreateBound(start_wall_start_point , start_wall_end_point)
    Wall.Create(doc, start_wall_line, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True)

    TransactionManager.Instance.TransactionTaskDone()

    file_name = f"{IN[9]}/partition_walls_asymm_edge_{start_level.Name}.txt"

    with open(file_name, "w") as file:
        file.write("x_long: ")
        for num in first_random_list_x_long:
            file.write(str(num))
        file.write("\nx_short: ")
        for num in first_random_list_x_short:
            file.write(str(num))
        file.write("\ny_long: ")
        for num in first_random_list_y_long:
            file.write(str(num))
        file.write("\ny_short: ")
        for num in first_random_list_y_short:
            file.write(str(num))

    return room_dict

OUT = create_edge_geometry    
