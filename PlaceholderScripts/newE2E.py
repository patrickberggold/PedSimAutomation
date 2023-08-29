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
NUM_ROOMS_SHORT_SIDE = IN[1][1][3]
NUM_ROOMS_LONG_SIDE = IN[1][1][4]
USE_BOTTLENECKS = IN[1][1][5]

DOOR_WIDTH_H = convert_meter_to_unit(float(IN[2]) / 2.)
OBSTACLE_WIDTH  = convert_meter_to_unit(float(IN[3]))
ROOM_WIDTH = convert_meter_to_unit(float(IN[4]))

DOOR_THICKNESS_H = convert_meter_to_unit(0.25)
DOOR_HEIGHT = convert_meter_to_unit(2.2)
MIN_ROOM_WIDTH = convert_meter_to_unit(4.)


def create_e2e_geometry(start_level , end_level) : 
    z_level = start_level.Elevation

    room_dict = {}
    ceiling = start_level.Elevation
    obstacle_counter = 0

    doc = DocumentManager.Instance.CurrentDBDocument
    TransactionManager.Instance.EnsureInTransaction(doc)


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
    corr_walls = [Wall.Create(doc, wall_line, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True) \
        for wall_line in corr_room_lines]

    # obstacles
    obstacle_length = 1.

    x_obst_min, x_obst_max = convert_to_meter(x_main_corridor_end)+0.1, convert_to_meter(x_main_corridor_end)+0.1+obstacle_length
    y_obst_min, y_obst_max = convert_to_meter(y_main_corridor + CORR_WIDTH/2.)+0.5, convert_to_meter(y_main_corridor + CORR_WIDTH/2.)+0.5+OBSTACLE_WIDTH
    room_dict.update({
        'CROWDIT_OBSTACLE_'+str(obstacle_counter)+'_1_1_': [
                (x_obst_min, y_obst_min),
                (x_obst_max, y_obst_max)
            ]
        }
    )
    obstacle_counter += 1

    x_obst_min, x_obst_max = convert_to_meter(x_main_corridor_start)-0.1-obstacle_length, convert_to_meter(x_main_corridor_start)-0.1
    y_obst_min, y_obst_max = convert_to_meter(y_main_corridor - CORR_WIDTH/2.)-0.5-OBSTACLE_WIDTH, convert_to_meter(y_main_corridor - CORR_WIDTH/2.)-0.5
    room_dict.update({
        'CROWDIT_OBSTACLE_'+str(obstacle_counter)+'_1_1_': [
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
        Wall.Create(doc, office_office_line, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True)
    
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
                'CROWDIT_OBSTACLE_'+str(obstacle_counter)+'_2_1_': [
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
        Wall.Create(doc, office_office_line, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True)

    
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
                'CROWDIT_OBSTACLE_'+str(obstacle_counter)+'_2_1_': [
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
        
        bottleneck_walls = [Wall.Create(doc, line, default_interior_wall_type.Id, start_level.Id, end_level.Elevation - start_level.Elevation, 0, False, True)
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
    

    TransactionManager.Instance.TransactionTaskDone()

    return room_dict

OUT = create_e2e_geometry    
