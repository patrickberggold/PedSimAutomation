import sys
import ezdxf
from ezdxf.acc.vector import Vec3
import argparse
import os
import random
from pdf2xml import convert_pdf_to_xml
from create_floorplan_images import create_input_images_and_crowdit_projects, create_input_images_and_crowdit_projects4eg_ice
import numpy as np
import itertools

def create_dxf_variation(dxf_filepath, sources_floorplan, destinations_floorplan, var_counter):
    dxf_variations_dir = os.path.join('\\'.join(dxf_filepath.split('\\')[:-1]), 'dxf_variations')

    if not os.path.isdir(dxf_variations_dir):
        os.mkdir(dxf_variations_dir)
    
    try:
        doc = ezdxf.readfile(dxf_filepath)
    except IOError:
        print(f"Not a DXF file or a generic I/O error.")
        sys.exit(1)
    except ezdxf.DXFStructureError:
        print(f"Invalid or corrupted DXF file.")
        sys.exit(2)

    doc.layers.add(name="crowdit", color=7, linetype="DASHED")
    model_space = doc.modelspace()

    for source in sources_floorplan:
        (s1, s2), (s3, s4) = source[0], source[1]
        # "0.9485693795314933,2.974038089426853,4.323054061934929,0.6475300164654794"
        or_polyline = model_space.add_polyline3d([
            Vec3(s1, s2, 0.),
            Vec3(s3, s2, 0.),
            Vec3(s3, s4, 0.),
            Vec3(s1, s4, 0.)],
            close=True,
            dxfattribs={"layer": "crowdit"}
        )
    
    for destination in destinations_floorplan:
        (d1, d2), (d3, d4) = destination[0], destination[1]
        # "16.1,19.3,19.5,15.5"
        dst_polyline = model_space.add_polyline3d([
            Vec3(d1, d2, 0.),
            Vec3(d3, d2, 0.),
            Vec3(d3, d4, 0.),
            Vec3(d1, d4, 0.)],
            close=True,
            dxfattribs={"layer": "crowdit"}
        )

    # remove unnecessary layers so crowdit works
    layer_removal_list = [layer.dxf.name for layer in doc.layers if layer.dxf.name=='Defpoints']# layer.dxf.name != 'crowdit' and not layer.dxf.name.startswith('A-WALL')]        
    for remove_layer in layer_removal_list:
        doc.layers.remove(remove_layer)

    store_path = os.path.join(dxf_variations_dir, dxf_filepath.split('\\')[-1].replace('.dxf', f'_variation_{var_counter}.dxf'))
    doc.saveas(store_path)

def create_ors_dsts_and_export_dxf(dxf_filepath, txt_filepath, layout_setting = 'original', export_dxf: bool = False):

    # Create Crowdit folder
    crowdit_folderpath = os.path.join(dxf_filepath.split('Revit')[0], 'Crowdit')
    if not os.path.isdir(crowdit_folderpath): os.mkdir(crowdit_folderpath)

    origin_coords = []
    destination_coords = []
    obstacle_coords = []

    with open(dxf_filepath, 'r') as f_dxf:
        dxf_lines = f_dxf.readlines()
        min_id = dxf_lines.index('$EXTMIN\n')
        max_id = dxf_lines.index('$EXTMAX\n')
        min_x_dxf = float(dxf_lines[min_id+2])
        min_y_dxf = float(dxf_lines[min_id+4])
        max_x_dxf = float(dxf_lines[max_id+2])
        max_y_dxf = float(dxf_lines[max_id+4])
    f_dxf.close()
    sizes = {'x': [min_x_dxf, max_x_dxf], 'y': [min_y_dxf, max_y_dxf]}

    if layout_setting == 'original':

        dxf_variations_dir = os.path.join('\\'.join(dxf_filepath.split('\\')[:-1]), 'dxf_variations')

        if not os.path.isdir(dxf_variations_dir):
            os.mkdir(dxf_variations_dir)

        rooms = []
        room = []

        num_origins = 1
        num_destinations = 1

        z_value_string = dxf_filepath.split('\\')[-1].split('zPos_')[-1].split('_')[0]
        if z_value_string=='0.0' or z_value_string=='0': 
            z_wall_there = True

        with open(txt_filepath, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.endswith('\n'): line = line.strip().replace('\n', '')
                if line.startswith('ROOM_'):
                    if len(room) > 0:
                        rooms.append(room)
                        room = []
                elif line.startswith('COORD_'):
                    x,y = line.split('COORD_')[-1].split(',')
                    coord = (float(x), float(y))
                    room.append(coord)
            if len(room) > 0:
                rooms.append(room)
        f.close()

        # Sort rooms list by room coordinates (first x, then y)
        sorted_rooms_by_x = sorted(rooms, key=lambda element: (element[0][0], element[0][1]), reverse=False)
        sorted_rooms_dict = {f'room_{i}': room_coords for i, room_coords in enumerate(sorted_rooms_by_x)}
        permuted_rooms = [combi for combi in itertools.permutations(sorted_rooms_dict, num_origins+num_destinations)]

        for idx, room_comb in enumerate(permuted_rooms[:2]):

            origin_room = sorted_rooms_dict[room_comb[0]]
            destination_room = sorted_rooms_dict[room_comb[1]]

            #origin_room, destination_room = random.sample(rooms, num_origins + num_destinations)
            distance_to_borders = 0.5
            s1 = origin_room[0][0] + distance_to_borders
            s2 = origin_room[0][1] + distance_to_borders
            s3 = origin_room[1][0] - distance_to_borders
            s4 = origin_room[1][1] - distance_to_borders
            assert s3 > s1+0.5
            assert s4 > s2+0.5

            d1 = destination_room[0][0] + distance_to_borders
            d2 = destination_room[0][1] + distance_to_borders
            d3 = destination_room[1][0] - distance_to_borders
            d4 = destination_room[1][1] - distance_to_borders
            assert d3 > d1+0.5
            assert d4 > d2+0.5

            origin_coords.append([(s1, s2), (s3, s4)])
            destination_coords.append([(d1, d2), (d3, d4)])

            if export_dxf:
                create_dxf_variation(dxf_filepath, [(s1, s2), (s3, s4)], [(d1, d2), (d3, d4)], idx)

    else:
        with open(txt_filepath, 'r') as f:
            lines = f.readlines()

            idx_fixed_rooms = [] # areas that are fixed
            idx_var_rooms = [] # areas that are fixed but not sure how many
            idx_varset_rooms_left = [] # group of areas of which only one is used for permutations, then iterate over groups
            idx_varset_rooms_right = [] # group of areas of which only one is used for permutations, then iterate over groups

            idx_fixed_obstacles = [] # obstacles that are fixed
            idx_var_obstacles = [] # obstacles that are fixed but not sure how many
            idx_varset_obstacles = [] # group of obstacles of which only one is used for permutations, then iterate over groups
            for i, line in enumerate(lines):
                if line.startswith('CROWDIT_FIXED'):
                    idx_fixed_rooms.append((i+1, i+2))
                elif line.startswith('CROWDIT_VAR_'):
                    idx_var_rooms.append((i+1, i+2))
                elif line.startswith('CROWDIT_VARSET_LEFT_'):
                    idx_varset_rooms_left.append((i+1, i+2))
                elif line.startswith('CROWDIT_VARSET_RIGHT_'):
                    idx_varset_rooms_right.append((i+1, i+2))
                elif line.startswith('OBS_FIXED'):
                    idx_fixed_obstacles.append((i+1, i+2))
                elif line.startswith('OBS_VAR_'):
                    idx_var_obstacles.append((i+1, i+2))
                elif line.startswith('OBS_VARSET_'):
                    idx_varset_obstacles.append((i+1, i+2))
                elif line.startswith('COORD') or line.startswith('\n'):
                    pass
                else:
                    raise NotImplementedError

            fixed_rooms = [
                [
                    [float(lines[i1].split('COORD_')[-1].split(',')[0]), float(lines[i1].split('COORD_')[-1].split(',')[1])],
                    [float(lines[i2].split('COORD_')[-1].split(',')[0]), float(lines[i2].split('COORD_')[-1].split(',')[1])]
                ] for (i1, i2) in idx_fixed_rooms]
            var_rooms = [
                [
                    [float(lines[i1].split('COORD_')[-1].split(',')[0]), float(lines[i1].split('COORD_')[-1].split(',')[1])],
                    [float(lines[i2].split('COORD_')[-1].split(',')[0]), float(lines[i2].split('COORD_')[-1].split(',')[1])]
                ] for (i1, i2) in idx_var_rooms]
            
            varset_rooms_left = {}
            for idx, (i1, i2) in enumerate(idx_varset_rooms_left):
                setting, room_number = lines[i1-1].strip().split('_')[-2:]
                if not lines[i1].split('COORD_')[-1].startswith('EMPTY'):
                    room_coords = \
                        [float(lines[i1].split('COORD_')[-1].split(',')[0]), float(lines[i1].split('COORD_')[-1].split(',')[1])], \
                        [float(lines[i2].split('COORD_')[-1].split(',')[0]), float(lines[i2].split('COORD_')[-1].split(',')[1])]
                if setting not in varset_rooms_left:
                    varset_rooms_left.update({setting: [(int(room_number), room_coords)]})
                else:
                    varset_rooms_left[setting].append((int(room_number), room_coords))

            varset_rooms_right = {}
            for idx, (i1, i2) in enumerate(idx_varset_rooms_right):
                setting, room_number = lines[i1-1].strip().split('_')[-2:]
                if not lines[i1].split('COORD_')[-1].startswith('EMPTY'):
                    room_coords = \
                        [float(lines[i1].split('COORD_')[-1].split(',')[0]), float(lines[i1].split('COORD_')[-1].split(',')[1])], \
                        [float(lines[i2].split('COORD_')[-1].split(',')[0]), float(lines[i2].split('COORD_')[-1].split(',')[1])]
                if setting not in varset_rooms_right:
                    varset_rooms_right.update({setting: [(int(room_number), room_coords)]})
                else:
                    varset_rooms_right[setting].append((int(room_number), room_coords))
            
            fixed_obstacles = [
                [
                    [float(lines[i1].split('COORD_')[-1].split(',')[0]), float(lines[i1].split('COORD_')[-1].split(',')[1])],
                    [float(lines[i2].split('COORD_')[-1].split(',')[0]), float(lines[i2].split('COORD_')[-1].split(',')[1])]
                ] for (i1, i2) in idx_fixed_obstacles]

            var_obstacles = [[float(lines[i].split('COORD_')[-1].split(',')[0]), float(lines[i].split('COORD_')[-1].split(',')[1])] for i in idx_var_obstacles]
            varset_obstacles = [[float(lines[i].split('COORD_')[-1].split(',')[0]), float(lines[i].split('COORD_')[-1].split(',')[1])] for i in idx_varset_obstacles]

            if len(var_rooms) > 0: assert len(varset_rooms_left) == 0 and len(varset_rooms_right) == 0
            if len(varset_rooms_left) > 0 and len(varset_rooms_right) > 0: assert len(var_rooms) == 0

        f.close()
        
        if len(var_rooms) > 0:
            var_rooms_permuted = []
            for i in range(1, len(var_rooms)+1):
                var_rooms_permuted += list(itertools.combinations(var_rooms, i))
        else:
            var_rooms_permuted_left, var_rooms_permuted_right = [], []
            for setting in varset_rooms_left:
                room_list = [el[1] for el in varset_rooms_left[setting]]
                var_rooms_permuted_left.append(room_list)
            
            for setting in varset_rooms_right:
                room_list = [el[1] for el in varset_rooms_right[setting]]
                var_rooms_permuted_right.append(room_list)


        fixed_rooms_combinations = []
        for i in range(1, len(fixed_rooms)+1):
            fixed_rooms_combinations += list(itertools.combinations(fixed_rooms, i))

        # Select only those combinations that shall be included in the dataset
        if layout_setting in ['corr_e2e', 'corr_cross']:
            if layout_setting=='corr_e2e':
                var_rooms_permuted = [var_rooms_comb for var_rooms_comb in var_rooms_permuted if len(var_rooms_comb) <= 2]
                fixed_rooms_combinations = [fixed_rooms_comb for fixed_rooms_comb in fixed_rooms_combinations if len(fixed_rooms_comb) <= 2]
            elif layout_setting == 'corr_cross':
                var_rooms_permuted = [var_rooms_comb for var_rooms_comb in var_rooms_permuted if len(var_rooms_comb) == 2]
                fixed_rooms_combinations = [fixed_rooms_comb for fixed_rooms_comb in fixed_rooms_combinations if len(fixed_rooms_comb) == 2]
            fixed_rooms_combinations.reverse()
            var_rooms_permuted.reverse()
            permuted_rooms = list(itertools.product(fixed_rooms_combinations, var_rooms_permuted))
            permuted_rooms += list(itertools.product(var_rooms_permuted, fixed_rooms_combinations))

        elif layout_setting=='train_station':
            # Possible settings:
            # option 1) one track side -> escalators
            # option 2) one track side -> escalators + other tracks side
            # option 3) escalators -> one track side
            # option 4) escalators -> both track sides
            # TODO option 5) both tracks -> escalators
            # At least two escalators because if only one, a queue might be generated which the simulator struggles to immitate realistically, maybe even artefacts are generated (simulator gets stuck) 

            # fix at least two escalators
            escalators = []
            for rooms_comb in fixed_rooms_combinations:
                valid_comb = []
                if len(rooms_comb) > 1:
                    for room in rooms_comb:
                        valid_comb.append((room[0], room[1]))
                    escalators.append(valid_comb)
            # escalators = [(rooms[0], rooms[1]) for rooms in fixed_rooms_combinations if len(rooms) >= 2]
            
            assert len(escalators) > 0

            # option 1 one track side -> escalators
            permuted_rooms = list(itertools.product(var_rooms_permuted_left, escalators))
            permuted_rooms += list(itertools.product(var_rooms_permuted_right, escalators))

            # option 2 one track side -> escalators + other tracks side
            left_track_esc = [
                room_esc_comb[0]+room_esc_comb[1] for room_esc_comb in list(itertools.product(var_rooms_permuted_left, escalators))
                ]
            right_track_esc = [
                room_esc_comb[0]+room_esc_comb[1] for room_esc_comb in list(itertools.product(var_rooms_permuted_right, escalators))
                ]

            permuted_rooms += list(itertools.product(var_rooms_permuted_left, right_track_esc))
            permuted_rooms += list(itertools.product(var_rooms_permuted_right, left_track_esc))

            # option 3 escalators -> one track side (exclude no spawn/dst area combinations)
            permuted_rooms += list(itertools.product(escalators, var_rooms_permuted_right))
            permuted_rooms += list(itertools.product(escalators, [right_comb for right_comb in var_rooms_permuted_right if len(right_comb[0])>0]))

            # option 4) escalators -> both track sides (exclude no spawn/dst area combinations)
            both_tracks = list(itertools.product(
                [left_comb for left_comb in var_rooms_permuted_left if len(left_comb[0]) > 0], 
                [right_comb for right_comb in var_rooms_permuted_right if len(right_comb[0]) > 0]
                ))
            both_tracks = [both_comb[0]+both_comb[1] for both_comb in both_tracks]
            permuted_rooms += list(itertools.product(escalators, both_tracks))

        if len(permuted_rooms) > 1000:
            indices = list(range(len(permuted_rooms)))
            random.seed(20)
            random.shuffle(indices)
            permuted_rooms = [permuted_rooms[i] for i in indices[:1000]]

        # Draw origin and destination areas
        for idx, room_comb in enumerate(permuted_rooms):

            origin_areas = room_comb[0]
            destination_areas = room_comb[1]

            #origin_room, destination_room = random.sample(rooms, num_origins + num_destinations
            combin_or = []
            for origin in origin_areas:
                s1 = origin[0][0]
                s2 = origin[0][1]
                s3 = origin[1][0]
                s4 = origin[1][1]
                x_min, x_max = min(s1, s3), max(s1, s3)
                y_min, y_max = min(s2, s4), max(s2, s4)
                assert x_max > x_min+0.5
                assert y_max > y_min+0.5
                area = (x_max-x_min)*(y_max-y_min) # rectangle area for now
                combin_or.append([(x_min, y_min), (x_max, y_max), area])

            combin_dst = []
            for destination in destination_areas:
                d1 = destination[0][0]
                d2 = destination[0][1]
                d3 = destination[1][0]
                d4 = destination[1][1]
                x_min, x_max = min(d1, d3), max(d1, d3)
                y_min, y_max = min(d2, d4), max(d2, d4)
                assert x_max > x_min+0.5
                assert y_max > y_min+0.5
                area = (x_max-x_min)*(y_max-y_min) # rectangle area for now
                combin_dst.append([(x_min, y_min), (x_max, y_max), area])
            
            origin_coords.append(combin_or)                
            destination_coords.append(combin_dst)

            if export_dxf:
                create_dxf_variation(dxf_filepath, combin_or, combin_dst, idx)

        # Draw obstacle areas
        for obstacle in fixed_obstacles:
            o1 = obstacle[0][0]
            o2 = obstacle[0][1]
            o3 = obstacle[1][0]
            o4 = obstacle[1][1]
            x_min, x_max = min(o1, o3), max(o1, o3)
            y_min, y_max = min(o2, o4), max(o2, o4)
            obstacle_coords.append([(x_min, y_min), (x_max, y_max)])
        

    return origin_coords, destination_coords, obstacle_coords, sizes

def create_ors_dsts_egice(dxf_filepath, txt_filepath, export_dxf: bool = False):

    # Create Crowdit folder
    crowdit_folderpath = os.path.join(dxf_filepath.split('Revit')[0], 'Crowdit')
    if not os.path.isdir(crowdit_folderpath): os.mkdir(crowdit_folderpath)

    origin_coords = []
    destination_coords = []
    obstacle_coords = []

    with open(dxf_filepath, 'r') as f_dxf:
        dxf_lines = f_dxf.readlines()
        min_id = dxf_lines.index('$EXTMIN\n')
        max_id = dxf_lines.index('$EXTMAX\n')
        min_x_dxf = round(float(dxf_lines[min_id+2]),2)
        min_y_dxf = round(float(dxf_lines[min_id+4]),2)
        max_x_dxf = round(float(dxf_lines[max_id+2]),2)
        max_y_dxf = round(float(dxf_lines[max_id+4]),2)
    f_dxf.close()
    sizes = {'x': [min_x_dxf, max_x_dxf], 'y': [min_y_dxf, max_y_dxf]}

    with open(txt_filepath, 'r') as f:
        lines = f.readlines()

        idx_destination_areas = []
        idx_origin_areas = []
        idx_obstacle_areas = []

        for i, line in enumerate(lines):
            if line.startswith('CROWDIT_DESTINATION_'):
                idx_destination_areas.append((i+1, i+2))
            elif line.startswith('CROWDIT_ORIGIN_'):
                idx_origin_areas.append((i+1, i+2))
            elif line.startswith('CROWDIT_OBSTACLE_'):
                idx_obstacle_areas.append((i+1, i+2))
            elif line.startswith('COORD') or line.startswith('\n'):
                pass
            else:
                raise NotImplementedError

        destination_areas = [
            [
                [float(lines[i1].split('COORD_')[-1].split(',')[0]), float(lines[i1].split('COORD_')[-1].split(',')[1])],
                [float(lines[i2].split('COORD_')[-1].split(',')[0]), float(lines[i2].split('COORD_')[-1].split(',')[1])]
            ] for (i1, i2) in idx_destination_areas]
        origin_areas = [
            [
                [float(lines[i1].split('COORD_')[-1].split(',')[0]), float(lines[i1].split('COORD_')[-1].split(',')[1])],
                [float(lines[i2].split('COORD_')[-1].split(',')[0]), float(lines[i2].split('COORD_')[-1].split(',')[1])]
            ] for (i1, i2) in idx_origin_areas]
        obstacle_areas = [
            [
                [float(lines[i1].split('COORD_')[-1].split(',')[0]), float(lines[i1].split('COORD_')[-1].split(',')[1])],
                [float(lines[i2].split('COORD_')[-1].split(',')[0]), float(lines[i2].split('COORD_')[-1].split(',')[1])]
            ] for (i1, i2) in idx_obstacle_areas]

    f.close()

    destination_combinations = []
    for i in range(1, len(destination_areas)+1):
        destination_combinations += list(itertools.combinations(destination_areas, i))

    origin_combinations = []
    for i in range(1, len(origin_areas)+1):
        origin_combinations += list(itertools.combinations(origin_areas, i))

    destination_combinations.reverse()
    origin_combinations.reverse()
    permuted_areas = list(itertools.product(origin_combinations, destination_combinations))

    # if len(permuted_areas) > 1000:
    #     indices = list(range(len(permuted_areas)))
    #     random.seed(20)
    #     random.shuffle(indices)
    #     permuted_areas = [permuted_areas[i] for i in indices[:1000]]

    # Draw origin and destination areas
    for idx, room_comb in enumerate(permuted_areas):

        origin_areas = room_comb[0]
        destination_areas = room_comb[1]

        #origin_room, destination_room = random.sample(rooms, num_origins + num_destinations
        combin_or = []
        for origin in origin_areas:
            s1 = origin[0][0]
            s2 = origin[0][1]
            s3 = origin[1][0]
            s4 = origin[1][1]
            x_min, x_max = min(s1, s3), max(s1, s3)
            y_min, y_max = min(s2, s4), max(s2, s4)
            assert x_max > x_min+0.5
            assert y_max > y_min+0.5
            area = (x_max-x_min)*(y_max-y_min) # rectangle area for now
            combin_or.append([(x_min, y_min), (x_max, y_max), area])

        combin_dst = []
        for destination in destination_areas:
            d1 = destination[0][0]
            d2 = destination[0][1]
            d3 = destination[1][0]
            d4 = destination[1][1]
            x_min, x_max = min(d1, d3), max(d1, d3)
            y_min, y_max = min(d2, d4), max(d2, d4)
            assert x_max > x_min+0.5
            assert y_max > y_min+0.5
            area = (x_max-x_min)*(y_max-y_min) # rectangle area for now
            combin_dst.append([(x_min, y_min), (x_max, y_max), area])
        
        origin_coords.append(combin_or)                
        destination_coords.append(combin_dst)

        if export_dxf:
            create_dxf_variation(dxf_filepath, combin_or, combin_dst, idx)

    # Draw obstacle areas
    for obstacle in obstacle_areas:
        o1 = obstacle[0][0]
        o2 = obstacle[0][1]
        o3 = obstacle[1][0]
        o4 = obstacle[1][1]
        x_min, x_max = min(o1, o3), max(o1, o3)
        y_min, y_max = min(o2, o4), max(o2, o4)
        obstacle_coords.append([(x_min, y_min), (x_max, y_max)])
    

    return origin_coords, destination_coords, obstacle_coords, sizes

REVIT_PATH = "C:\\Users\\ga78jem\\Documents\\Revit\\Exports_EGICE\\"
ONLY_DO = 'corr_cross'

for id_b, building_folder in enumerate(os.listdir(REVIT_PATH)):

    print(f'\n\n####################################y###########')
    print(f'BUILDING FOLDER [{id_b+1}/{len(os.listdir(REVIT_PATH))}]')
    print(f'###############################################\n\n')

    building_folder_abs = os.path.join(REVIT_PATH, building_folder)

    for id_s, setting_dir in enumerate(os.listdir(building_folder_abs)):

        # print(f'\n\nSTEP [{id_s+1}/{len(os.listdir(building_folder_abs))}]\n\n')

        filepath = os.path.join(building_folder_abs, setting_dir)

        txt_filepath = os.path.join(filepath, setting_dir.split('__')[-1]+'.txt')
        dxf_filepath = os.path.join(filepath, setting_dir.split('__')[-1]+'.dxf')
        pdf_filepath = os.path.join(filepath, setting_dir.split('__')[-1]+'.pdf')

        txt_true = os.path.isfile(txt_filepath)
        pdf_true = os.path.isfile(pdf_filepath)
        dxf_true = os.path.isfile(dxf_filepath)

        setting = building_folder_abs.split('\\')[-1] # 'original'

        if building_folder_abs.split('\\')[-1] != 'corr_edge':
            continue
        if int(setting_dir.split('__')[0]) < 3:
            continue
        # else:
        #     setting = ONLY_DO
        # if building_folder_abs.split('\\')[-1] == 'corr_e2e':  continue #setting = 'corr_e2e'
        # elif building_folder_abs.split('\\')[-1] == 'corr_cross': setting = 'corr_cross'
        # elif building_folder_abs.split('\\')[-1] == 'train_station': continue #setting = 'train_station'
        # else:
            # raise NotImplementedError
        xml_path = convert_pdf_to_xml(pdf_filepath)

        # origins, destinations, obstacles, resolutions = create_ors_dsts_and_export_dxf(dxf_filepath, txt_filepath, layout_setting=setting)
        origins, destinations, obstacles, resolutions = create_ors_dsts_egice(dxf_filepath, txt_filepath)

        # if setting == 'corr_cross' and xml_path.split('\\')[-2].startswith('0__'):
        #     continue
        # create_input_images_and_crowdit_projects(xml_path, building_folder_abs, origins, destinations, obstacles, resolutions, setting=setting)
        create_input_images_and_crowdit_projects4eg_ice(xml_path, building_folder_abs, origins, destinations, obstacles, resolutions, setting)


"""
corr_edge
0 & 1: 189 * 36
2 & 3: 765 * 36
4 & 5: 765 * 36

until corr_edge-project_4_598.crowdit:
All simulations took in total 362.6639 min
Sim duration mean: 10.5126 s, std: 3.3568 s

until corr_edge-project_2_104.crowdit:
All simulations took in total 364.3857 min
Sim duration mean: 10.1844 s, std: 4.8841 s

until corr_edge-project_2_398.crowdit:
All simulations took in total 462.3723 min
Sim duration mean: 10.4845 s, std: 3.2496 s

until corr_edge-project_4_130.crowdit_wObs:
All simulations took in total 460.3689 min
Sim duration mean: 10.3529 s, std: 4.5833 

until corr_edge-project_2_111.crowdit_wObs:
All simulations took in total 668.5191 min
Sim duration mean: 9.3177 s, std: 3.8520 s

corr_edge-project_4_536.crowdit_wObs:
All simulations took in total 669.6070 min
Sim duration mean: 10.9743 s, std: 3.6761 s

corr_edge-project_2_508.crowdit_wObs
All simulations took in total 614.3311 min
Sim duration mean: 10.3295 s, std: 3.6297 s

corr_edge-project_5_200.crowdit
All simulations took in total 612.9892 min
Sim duration mean: 9.5208 s, std: 3.5882 s

All simulations took in total 780.5889 min
Sim duration mean: 10.1299 s, std: 3.4686 s

All simulations took in total 780.5175 min
Sim duration mean: 8.6981 s, std: 2.7969 s

All simulations took in total 740.9663 min
Sim duration mean: 8.6580 s, std: 3.3971 s

corr_e2e
0 & 1: 189 * 36
2 & 3: 189 * 36
4 & 5: 381 * 36
All simulations took in total 4575.7032 min
Sim duration mean: 10.0465 s, std: 3.3940 s

corr_cross
0 & 1: 189 * 36
2 & 3: 189 * 36
4 & 5: 765 * 36
All simulations took in total 118.6985 min
Sim duration mean: 6.0269 s, std: 1.5618 s
"""