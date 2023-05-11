import os
import xml.etree.ElementTree as ET
import numpy as np
import pylab as plt
from matplotlib.path import Path
import math
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
import h5py
from scipy import ndimage
from create_crowdit_projects import export2crowdit_project, export2crowdit_project_EGICE

def get_customized_colormap(class_names):

    len_classes = len(class_names.keys())
    
    viridis = cm.get_cmap('viridis', len_classes)
    custom_colors = viridis(np.linspace(0, 1, len_classes)) 
    # define colors
    for idx, key in enumerate(class_names):
        custom_colors[idx] = class_names[key]
    customed_colormap = ListedColormap(custom_colors)
    return customed_colormap

def plot_examples(cms):
    """
    helper function to plot two colormaps
    """
    np.random.seed(19680801)
    data = np.random.randn(30, 30)

    fig, axs = plt.subplots(1, 2, figsize=(6, 3), constrained_layout=True)
    for [ax, cmap] in zip(axs, cms):
        psm = ax.pcolormesh(data, cmap=cmap, rasterized=True, vmin=-4, vmax=4)
        fig.colorbar(psm, ax=ax)
    plt.show()

def point_plotter(points_dict):
    points = list(points_dict.keys())
    points = np.array(points)

    x = points[:,0]
    y = points[:,1]

    plt.scatter(x, y)
    plt.show()
    quit()

def line_plotter(line_list):
    for line in line_list:
        point1 = line[0]
        point2 = line[1]
        x_values = [point1[0], point2[0]]
        y_values = [point1[1], point2[1]]
        plt.plot(x_values, y_values, 'bo', linestyle="--")
        plt.text(point1[0]-0.015, point1[1]+0.25, f"({point1[0]}, {point1[1]})")
        plt.text(point2[0]-0.050, point2[1]-0.25, f"({point2[0]}, {point2[1]})")
    plt.show()

def check_num_values(line_list):
    sorted_by_val = {}
    for line in line_list:
        for coord in line:
            if coord not in sorted_by_val:
                sorted_by_val.update({coord: [1, [line]]})
            else:
                sorted_by_val[coord][0] += 1
                sorted_by_val[coord][1].append(line)
    return sorted_by_val

def preprocess_delete_short_lines(line_list):
    lines_per_point = check_num_values(line_list) # dict(key==coord: [num_lines, [lines_per_point]])
    preprocessed_line_list = []
    deleted_lines = []
    line_delete_count = 0
    duplicate_lines = []
    for key in lines_per_point:
        assert lines_per_point[key][0] >= 2
        if lines_per_point[key][0] > 2:
            line_delete_count += 1
            assert lines_per_point[key][0] == 3
            line1 = lines_per_point[key][1][0]
            dist1 =  math.dist(line1[0], line1[1])

            line2 = lines_per_point[key][1][1]
            dist2 =  math.dist(line2[0], line2[1])
            
            line3 = lines_per_point[key][1][2]
            dist3 =  math.dist(line3[0], line3[1])

            if dist1 <= dist2 and dist1 <= dist2:
                if lines_per_point[key][1][0] not in deleted_lines:
                    deleted_lines.append(lines_per_point[key][1][0])
                del lines_per_point[key][1][0]
            elif dist2 <= dist1 and dist2 <= dist3:
                if lines_per_point[key][1][1] not in deleted_lines:
                    deleted_lines.append(lines_per_point[key][1][1])
                del lines_per_point[key][1][1]
            elif dist3 <= dist1 and dist3 <= dist2:
                if lines_per_point[key][1][2] not in deleted_lines:
                    deleted_lines.append(lines_per_point[key][1][2])
                del lines_per_point[key][1][2]
            else:
                raise ValueError('No smallest distance-> no line to delete in case of more than 2 lines...')

        for line in lines_per_point[key][1]:
            if line not in preprocessed_line_list:
                preprocessed_line_list.append(line)
            else:
                duplicate_lines.append(line)
    
    return preprocessed_line_list, deleted_lines

# Input: current point coordinate, min floorplan coord, max floorplan coord, min resolution coord, max resolution coord -> output: projected coordinated
def linear_interpolation(curr_point_or, lim_min_or, lim_max_or, lim_min_proj, lim_max_proj):
    return lim_min_proj + (curr_point_or - lim_min_or) * (lim_max_proj - lim_min_proj) / (lim_max_or - lim_min_or)

def get_wall_lines_from_crowdit_xml(xml_filename):

    crowdit_filename = xml_filename.split('_')[0] + '.crowdit'

    crowdit_tree = ET.parse(crowdit_filename)
    
    origin_names = []
    destination_names = []

    for origin in crowdit_tree.findall('meta/morphosis/origin'):
        origin_names.append(origin.attrib['wunderZone'])
    
    for destination in crowdit_tree.findall('meta/morphosis/destination'):
        destination_names.append(destination.attrib['wunderZone'])

    tree = ET.parse(xml_filename)

    wall_points = []
    wall_lines = []
    crowdit_points = []
    crowdit_lines = []
    origin_lines = []
    origin_lines_projected = []
    destination_lines = []
    destination_lines_projected = []

    min_x = float("inf")
    max_x = -float("inf")
    min_y = float("inf")
    max_y = -float("inf")

    class_names = ['unpassable', 'walkable area', 'spawn_zone', 'destination']
    n_classes = len(class_names) + 1 # 0 is background

    for layer in tree.findall('layer'):
        if len(layer.findall('wall')) > 0 or len(layer.findall('wunderZone')) > 0:
            for wunderZone in layer.findall('wunderZone'):
                line = []
                if wunderZone.attrib['id'] in origin_names:
                    for point in wunderZone.findall('point'):
                        x = float(point.attrib['x'])
                        y = float(point.attrib['y'])
                        # crowdit_points.append((float(point.attrib['x']), float(point.attrib['y'])))
                        line.append((x, y))
                    origin_lines.append(line)
                elif wunderZone.attrib['id'] in destination_names:
                    for point in wunderZone.findall('point'):
                        x = float(point.attrib['x'])
                        y = float(point.attrib['y'])
                        # crowdit_points.append((float(point.attrib['x']), float(point.attrib['y'])))
                        line.append((x, y))
                    destination_lines.append(line)
            else: 
                for wall in layer.findall('wall'):
                    line = []
                    for point in wall.findall('point'):
                        x = float(point.attrib['x'])
                        y = float(point.attrib['y'])
                        if min_x > x:
                            min_x = x
                        if max_x < x:
                            max_x = x
                        if min_y > y:
                            min_y =y
                        if max_y < y:
                            max_y = y
                        # wall_points.append((x, y))
                        line.append((x, y))
                    wall_lines.append(line)
    
    return wall_lines, origin_lines, destination_lines, {'min_x': min_x, 'max_x': max_x, 'min_y': min_y, 'max_y': max_y}

def get_wall_lines_from_pdf2xml_converter(xml_filename, dxf_sizes):

    tree = ET.parse(xml_filename)
    root = tree.getroot()

    wall_lines = []

    min_x = float("inf")
    max_x = -float("inf")
    min_y = float("inf")
    max_y = -float("inf")

    for child in root:
        for grandchild in child:
            if grandchild.tag == 'line':
                xyxy = grandchild.attrib['bbox'].split(',')
                line = [(float(xyxy[0]), float(xyxy[1])),(float(xyxy[2]), float(xyxy[3]))]
                for point in line:
                    x = float(point[0])
                    y = float(point[1])
                    if min_x > x:
                        min_x = x
                    if max_x < x:
                        max_x = x
                    if min_y > y:
                        min_y =y
                    if max_y < y:
                        max_y = y
                wall_lines.append(line)
                #print(grandchild.tag, grandchild.attrib)
        #print(child.tag, child.attrib)
    
    min_x_dxf = dxf_sizes['x'][0]
    min_y_dxf = dxf_sizes['y'][0]
    max_x_dxf = dxf_sizes['x'][1]
    max_y_dxf = dxf_sizes['y'][1]

    wall_lines_proj = []

    # project from pdf to dxf
    for line in wall_lines:
        line_proj = []
        for point in line:
            assert len(point) == 2
            x = point[0]
            y = point[1]
            x_proj = linear_interpolation(x, min_x, max_x, min_x_dxf, max_x_dxf)
            y_proj = linear_interpolation(y, min_y, max_y, min_y_dxf, max_y_dxf)
            line_proj.append((x_proj, y_proj))
        wall_lines_proj.append(line_proj)

    return wall_lines_proj

def get_sorted_polynomial_point_list(line_list):
    sorted_points_list = [line_list[0][0], line_list[0][1]]
    del line_list[0]

    closed_polygons = []

    def point_not_in_list(list_to_query, line_to_check):
        if line_to_check not in list_to_query: return True
        else: return False # basically the closing point (if point already in the list)

    def get_next_point(list_to_query, startpoint):
        res_ones = [(el[0], idp1) for idp1, el in enumerate(list_to_query) if el[0] == startpoint]
        res_twos = [(el[1], idp2) for idp2, el in enumerate(list_to_query) if el[1] == startpoint]

        assert len(res_ones)+len(res_twos)==1, 'more than one entry for a point'

        for line_idx, line in enumerate(list_to_query):
            for coord_idx, point in enumerate(line):
                if point[0] == startpoint[0] and point[1] == startpoint[1]:
                    del list_to_query[line_idx]
                    if coord_idx == 0:
                        return line[1]
                    elif coord_idx == 1:
                        return line[0]
                    else:
                        raise IndexError('coordinate index not in {0, 1}!')
        raise ValueError('Couldnt find successive point to given startpoint')

    while len(line_list) > 0:
        next_point = get_next_point(line_list, sorted_points_list[-1])
        if next_point and point_not_in_list(sorted_points_list, next_point):
            sorted_points_list.append(next_point)
        else:
            closed_polygons.append(sorted_points_list)
            if len(line_list) > 0:
                sorted_points_list = [line_list[0][0], line_list[0][1]]
                del line_list[0]

    return closed_polygons[1:] # asserting that the first closed polygon corresponds to exterior wall which arent necessary

def create_input_images_and_crowdit_projects(xml_filename, root_dir, origins, destinations, obstacles, resolutions, setting = 'original'):

    assert setting in ['corr_e2e', 'corr_cross', 'train_station']
    assert len(resolutions) == 2
    resolution_width, resolution_height = (resolutions['x'][1]-resolutions['x'][0])/20.*800, (resolutions['y'][1]-resolutions['y'][0])/20.*800
    # round to next lowest hundred
    resolution_width, resolution_height = int(resolution_width/100)*100, int(resolution_height/100)*100

    img_variations_dir = os.path.join('\\'.join(xml_filename.split('\\')[:-1]), f'img_variations_resolution_{int(resolution_width)}_{int(resolution_height)}')

    if not os.path.isdir(img_variations_dir):
        os.mkdir(img_variations_dir)

    # Separate GT segmented images directory
    array_gt_variations_dir = os.path.join(root_dir, f'..\\HDF5_GT_resolution_{int(resolution_width)}_{int(resolution_height)}')
    # if not os.path.isdir(array_gt_variations_dir):
    #     os.mkdir(array_gt_variations_dir)

    HDF_STORE_PATH = 'C:\\Users\\ga78jem\\Documents\\Revit\\ADVANCED_FLOORPLANS_NEW'
    if not os.path.isdir(HDF_STORE_PATH): os.mkdir(HDF_STORE_PATH)

    # Separate flooplan images directory
    array_images_variations_dir = os.path.join(HDF_STORE_PATH, root_dir.split('\\')[-1])
    if not os.path.isdir(array_images_variations_dir): os.mkdir(array_images_variations_dir)

    # Create floorplan-specific variations folder
    subgroup_folder = os.path.join(array_images_variations_dir, xml_filename.split('\\')[-2])
    if not os.path.isdir(subgroup_folder):
        os.mkdir(subgroup_folder)

    # write txt file with relevant information
    txt_filepath = os.path.join(array_images_variations_dir, xml_filename.split('\\')[-2], 'data.txt')
    f_txt = open(txt_filepath, 'w')
    site_x = xml_filename.split('\\')[-1].split('siteX_')[-1].split('_')[0]
    site_y = xml_filename.split('\\')[-1].split('siteY_')[-1].split('_')[0]
    f_txt.write(f'site_x: {site_x}\nsite_y: {site_y}\n')
    f_txt.close()

    wall_lines = get_wall_lines_from_pdf2xml_converter(xml_filename, resolutions)

    min_x_dxf = resolutions['x'][0]
    min_y_dxf = resolutions['y'][0]
    max_x_dxf = resolutions['x'][1]
    max_y_dxf = resolutions['y'][1]

    # delete small, unnecessary lines between outside wall and interior
    preprocessed_lines, deleted_lines = preprocess_delete_short_lines(wall_lines)

    num_agents = [15, 50] if setting in ['corr_e2e', 'corr_cross'] else [15, 25]
    export2crowdit_project(preprocessed_lines, origins, destinations, obstacles, '\\'.join(xml_filename.split('\\')[-3:-1]), num_agents)
    # line_plotter(preprocessed_lines)
    # project polygon points
    # import cv2
    proj_lines = []
    repeated_lines = []
    # img = np.zeros((resolution_height, resolution_width, 3))
    for line in preprocessed_lines:
        proj_line = []
        for point in line:
            x_proj = int(linear_interpolation(float(point[0]), min_x_dxf, max_x_dxf, 0, resolution_width))
            y_proj = int(linear_interpolation(float(point[1]), min_y_dxf, max_y_dxf, 0, resolution_height))
            proj_line.append((x_proj, y_proj))
        if proj_line not in proj_lines:
            proj_lines.append(proj_line)
            # cv2.line(img, (proj_line[0][0], proj_line[0][1]), (proj_line[1][0], proj_line[1][1]), (0,1.,0), thickness=5)
        else:
            repeated_lines.append(proj_line)
    
    # plt.imshow(img)
    layout_mask = np.zeros((resolution_width, resolution_height)).astype(int) # new
    
    closed_polygon_point_lists = get_sorted_polynomial_point_list(proj_lines) # exclude outer walls for now
    
    for idx, polygon_points in enumerate(closed_polygon_point_lists):

        origin_rectangles_projected = []
        destination_rectangles_projected = []


        poly_path=Path(polygon_points)

        x, y = np.mgrid[:resolution_width, :resolution_height]
        coors = np.hstack((x.reshape(-1, 1), y.reshape(-1,1)))

        mask = poly_path.contains_points(coors)
        base_mask = mask.reshape(resolution_width, resolution_height)
        base_mask = np.array(base_mask).astype(int)
        if idx < 1 and setting != 'train_station':
            # switch true or false values to make multiple polygons compatible
            base_mask = 1-base_mask

        layout_mask = np.add(layout_mask, base_mask)

        # plt.imshow(base_mask)
        # plt.imshow(layout_mask)

    # project origins and destinations to image resolution
    for destination_areas in destinations:
        areas = []
        for destination in destination_areas:
            edges_proj = []
            for edge in destination[:2]:
                x = edge[0]
                y = edge[1]
                assert min_x_dxf <= x <= max_x_dxf
                assert min_y_dxf <= y <= max_y_dxf
                x_proj = int(linear_interpolation(x, min_x_dxf, max_x_dxf, 0, resolution_width))
                y_proj = int(linear_interpolation(y, min_y_dxf, max_y_dxf, 0, resolution_height))
                edges_proj.append((x_proj, y_proj))
            areas.append(edges_proj)
        destination_rectangles_projected.append(areas)
    
    for origin_areas in origins:
        areas = []
        for origin in origin_areas:
            edges_proj = []
            for edge in origin[:2]:
                x = edge[0]
                y = edge[1]
                assert min_x_dxf <= x <= max_x_dxf
                assert min_y_dxf <= y <= max_y_dxf
                x_proj = int(linear_interpolation(x, min_x_dxf, max_x_dxf, 0, resolution_width))
                y_proj = int(linear_interpolation(y, min_y_dxf, max_y_dxf, 0, resolution_height))
                edges_proj.append((x_proj, y_proj))
            areas.append(edges_proj)
        origin_rectangles_projected.append(areas)

    base_image = np.zeros((resolution_width, resolution_height, 3))

    zero_coords_base_image = np.argwhere(layout_mask==0)
    base_image[zero_coords_base_image[:,0], zero_coords_base_image[:,1]] = np.array([255, 255, 255])
    # plt.imshow(layout_mask)
    img_store_path = os.path.join('\\'.join(xml_filename.split('\\')[:-1]), 'base_floorplan.jpeg')

    for obstacle in obstacles:
        x_obs_start, x_obs_end = obstacle[0][0], obstacle[1][0]
        y_obs_start, y_obs_end = obstacle[0][1], obstacle[1][1]

        assert min_x_dxf <= x_obs_start <= max_x_dxf
        assert min_x_dxf <= x_obs_end <= max_x_dxf
        assert min_y_dxf <= y_obs_start <= max_y_dxf
        assert min_y_dxf <= y_obs_end <= max_y_dxf

        # project obstacle points to resolution
        x_obs_start = int(linear_interpolation(x_obs_start, min_x_dxf, max_x_dxf, 0, resolution_width))
        x_obs_end = int(linear_interpolation(x_obs_end, min_x_dxf, max_x_dxf, 0, resolution_width))
        y_obs_start = int(linear_interpolation(y_obs_start, min_y_dxf, max_y_dxf, 0, resolution_height))
        y_obs_end = int(linear_interpolation(y_obs_end, min_y_dxf, max_y_dxf, 0, resolution_height))

        black_coords = np.array([(x_dst, y_dst) for x_dst in range(x_obs_start, x_obs_end) for y_dst in range(y_obs_start, y_obs_end)])

        base_image[black_coords[:,0], black_coords[:,1]] = np.array([0, 0, 0])

    plt.imsave(img_store_path, ndimage.rotate(base_image, 90).astype(np.uint8), vmin=0, vmax=255)

    for idx, (origin_areas, destination_areas) in enumerate(zip(origin_rectangles_projected, destination_rectangles_projected)):
        # masked_img = layout_mask.copy()
        image_array = base_image.copy()
        for origin in origin_areas:

            x_or_start, x_or_end = origin[0][0], origin[1][0]
            y_or_start, y_or_end = origin[0][1], origin[1][1]

            image_array[x_or_start:x_or_end, y_or_start:y_or_end] = np.array([255, 0, 0])
        
            # red_coords = np.array([(x_or, y_or) for x_or in range(x_or_start, x_or_end) for y_or in range(y_or_start, y_or_end)])
            # image_array[red_coords[:,0], red_coords[:,1]] = np.array([255, 0, 0])

            # masked_img[red_coords[:,0], red_coords[:,1]] = 2

        for destination in destination_areas:

            x_dst_start, x_dst_end = destination[0][0], destination[1][0]
            y_dst_start, y_dst_end = destination[0][1], destination[1][1]

            image_array[x_dst_start:x_dst_end, y_dst_start:y_dst_end] =  np.array([0, 255, 0])

            # green_coords = np.array([(x_dst, y_dst) for x_dst in range(x_dst_start, x_dst_end) for y_dst in range(y_dst_start, y_dst_end)])
            # image_array[green_coords[:,0], green_coords[:,1]] = np.array([0, 255, 0])

            # masked_img[green_coords[:,0], green_coords[:,1]] = 3

        image_array = ndimage.rotate(image_array, 90)
        # masked_img = ndimage.rotate(masked_img, 90)

        # plt.axis('off')
        # plt.imshow(image_array, vmin=0, vmax=255)

        # Logging
        cropped_print = xml_filename.split("\\")[-2].split("__")[0]
        print(f'Saving jpeg of floorplan {cropped_print}, variation {idx} ...')
        
        # save mask + colormap (ground truth)
        img_store_path = os.path.join(img_variations_dir, xml_filename.split('\\')[-1].replace('.xml', f'_variation_{idx}.jpeg'))
        # plt.imsave(img_store_path.replace('.jpeg', '_gt_mask.jpeg'), masked_img, cmap=get_customized_colormap(class_names))
        # save RGB image (train data)
        if idx < 300:
            plt.imsave(img_store_path, image_array.astype(np.uint8), vmin=0, vmax=255)#
        
        # SAVE INPUT IMG ARRAY AS HDF5
        store_path = os.path.join(subgroup_folder, 'HDF5_'+xml_filename.split('\\')[-1].replace('.xml', f'_variation_{idx}.h5'))
        
        f_txt = open(txt_filepath, 'a')
        f_txt.write(f'variation_{idx}: ')
        f_txt.write('\nSRC real:')
        for or_coords in origins[idx]:
            (x_or_start, y_or_start), (x_or_end, y_or_end), _ = or_coords
            f_txt.write(f'[x=({x_or_start}, {x_or_end}), y=({y_or_start}, {y_or_end})]')

        f_txt.write(' ### DST real: ')
        for dst_coords in destinations[idx]:
            (x_dst_start, y_dst_start), (x_dst_end, y_dst_end), _ = dst_coords
            f_txt.write(f'[x=({x_dst_start}, {x_dst_end}), y=({y_dst_start}, {y_dst_end})]')
        
        f_txt.write('\nSRC pixel:')
        for origin in origin_areas:
            x_or_start, x_or_end = origin[0][0], origin[1][0]
            y_or_start, y_or_end = origin[0][1], origin[1][1]

            f_txt.write(f'[x=({x_or_start}, {x_or_end}), y=({y_or_start}, {y_or_end})]')

        f_txt.write(' ### DST pixel: ')
        for destination in destination_areas:
            x_dst_start, x_dst_end = destination[0][0], destination[1][0]
            y_dst_start, y_dst_end = destination[0][1], destination[1][1]

            f_txt.write(f'[x=({x_dst_start}, {x_dst_end}), y=({y_dst_start}, {y_dst_end})]')

        f_txt.write('\n')
        f_txt.close()

        hf = h5py.File(store_path, 'w')
        hf.create_dataset('img', data=image_array.astype(np.uint8))
        hf.create_dataset('dxf_sizes', data=np.array([min_x_dxf, max_x_dxf, min_y_dxf, max_y_dxf]))
        hf.close()

def create_input_images_and_crowdit_projects4eg_ice(xml_filename, root_dir, origins, destinations, obstacles, resolutions, setting = 'original'):
    # origins = [origins[0]]
    # destinations = [destinations[0]]

    diff_x = resolutions['x'][1]-resolutions['x'][0]
    diff_y = resolutions['y'][1]-resolutions['y'][0]
    assert diff_x.is_integer() and diff_y.is_integer(), 'both real-size resolutions must be integer!'

    assert len(resolutions) == 2

    # 400/12.5 --> 32 pixel / meter
    resolution_width, resolution_height = round(diff_x/12.5*400), round(diff_y/12.5*400)
    assert resolution_width%16 == 0
    assert resolution_height%16 == 0

    resolution_width, resolution_height = int(resolution_width), int(resolution_height)

    # round to next lowest hundred
    # resolution_width, resolution_height = int(resolution_width/100)*100, int(resolution_height/100)*100

    DATASET_STORE_PATH = 'C:\\Users\\ga78jem\\Documents\\Revit\\FLOORPLANS_EGICE'
    if not os.path.isdir(DATASET_STORE_PATH): os.mkdir(DATASET_STORE_PATH)

    # Separate flooplan images directory
    if not os.path.isdir(os.path.join(DATASET_STORE_PATH, 'INPUT')): os.mkdir(os.path.join(DATASET_STORE_PATH, 'INPUT'))
    array_images_variations_dir = os.path.join(DATASET_STORE_PATH, 'INPUT', root_dir.split('\\')[-1])
    if not os.path.isdir(array_images_variations_dir): os.mkdir(array_images_variations_dir)

    # Create floorplan-specific variations folder
    subgroup_folder = os.path.join(array_images_variations_dir, xml_filename.split('\\')[-2])
    if not os.path.isdir(subgroup_folder): os.mkdir(subgroup_folder)
    # write txt file with relevant information
    txt_filepath = os.path.join(array_images_variations_dir, xml_filename.split('\\')[-2], 'data.txt')
    f_txt = open(txt_filepath, 'w')
    site_x = xml_filename.split('\\')[-1].split('siteX_')[-1].split('_')[0]
    site_y = xml_filename.split('\\')[-1].split('siteY_')[-1].split('_')[0]
    f_txt.write(f'site_x: {site_x}\nsite_y: {site_y}\n')
    f_txt.close()

    wall_lines = get_wall_lines_from_pdf2xml_converter(xml_filename, resolutions)

    min_x_dxf = resolutions['x'][0]
    min_y_dxf = resolutions['y'][0]
    max_x_dxf = resolutions['x'][1]
    max_y_dxf = resolutions['y'][1]

    # delete small, unnecessary lines between outside wall and interior
    preprocessed_lines, deleted_lines = preprocess_delete_short_lines(wall_lines)
    
    # project polygon points
    proj_lines = []
    repeated_lines = []
    # img = np.zeros((resolution_height, resolution_width, 3))
    for line in preprocessed_lines:
        proj_line = []
        for point in line:
            x_proj = int(linear_interpolation(float(point[0]), min_x_dxf, max_x_dxf, 0, resolution_width))
            y_proj = int(linear_interpolation(float(point[1]), min_y_dxf, max_y_dxf, 0, resolution_height))
            proj_line.append((x_proj, y_proj))
        if proj_line not in proj_lines:
            proj_lines.append(proj_line)
            # cv2.line(img, (proj_line[0][0], proj_line[0][1]), (proj_line[1][0], proj_line[1][1]), (0,1.,0), thickness=5)
        else:
            repeated_lines.append(proj_line)
    
    # plt.imshow(img)
    layout_mask = np.zeros((resolution_width, resolution_height)).astype(int) # new
    
    closed_polygon_point_lists = get_sorted_polynomial_point_list(proj_lines) # exclude outer walls for now
    
    for idx, polygon_points in enumerate(closed_polygon_point_lists):

        origin_rectangles_projected = []
        destination_rectangles_projected = []

        poly_path=Path(polygon_points)

        x, y = np.mgrid[:resolution_width, :resolution_height]
        coors = np.hstack((x.reshape(-1, 1), y.reshape(-1,1)))

        mask = poly_path.contains_points(coors)
        base_mask = mask.reshape(resolution_width, resolution_height) # 0=wall, 1=walkable
        base_mask = np.array(base_mask).astype(int)
        # plt.imshow(base_mask)
        
        if setting == 'train_station': raise NotImplementedError('Debug for train stations...')

        layout_mask = np.add(layout_mask, base_mask)

        layout_mask = np.clip(layout_mask, 0, 1)
        # plt.imshow(layout_mask)

    # project origins and destinations to image resolution
    for destination_areas in destinations:
        areas = []
        for destination in destination_areas:
            edges_proj = []
            for edge in destination[:2]:
                x = edge[0]
                y = edge[1]
                assert min_x_dxf <= x <= max_x_dxf
                assert min_y_dxf <= y <= max_y_dxf
                x_proj = int(linear_interpolation(x, min_x_dxf, max_x_dxf, 0, resolution_width))
                y_proj = int(linear_interpolation(y, min_y_dxf, max_y_dxf, 0, resolution_height))
                edges_proj.append((x_proj, y_proj))
            areas.append(edges_proj)
        destination_rectangles_projected.append(areas)
    
    for origin_areas in origins:
        areas = []
        for origin in origin_areas:
            edges_proj = []
            for edge in origin[:2]:
                x = edge[0]
                y = edge[1]
                assert min_x_dxf <= x <= max_x_dxf
                assert min_y_dxf <= y <= max_y_dxf
                x_proj = int(linear_interpolation(x, min_x_dxf, max_x_dxf, 0, resolution_width))
                y_proj = int(linear_interpolation(y, min_y_dxf, max_y_dxf, 0, resolution_height))
                edges_proj.append((x_proj, y_proj))
            areas.append(edges_proj)
        origin_rectangles_projected.append(areas)

    base_image = np.zeros((resolution_width, resolution_height, 3), dtype=np.uint8)

    zero_coords_base_image = np.argwhere(layout_mask==1)
    base_image[zero_coords_base_image[:,0], zero_coords_base_image[:,1]] = np.array([255, 255, 255])
    # plt.imshow(layout_mask)
    img_store_path = os.path.join('\\'.join(xml_filename.split('\\')[:-1]), 'base_floorplan.jpeg')

    obstacle_coord_list = []

    for obstacle in obstacles:
        x_obs_start, x_obs_end = obstacle[0][0], obstacle[1][0]
        y_obs_start, y_obs_end = obstacle[0][1], obstacle[1][1]

        assert min_x_dxf <= x_obs_start <= max_x_dxf
        assert min_x_dxf <= x_obs_end <= max_x_dxf
        assert min_y_dxf <= y_obs_start <= max_y_dxf
        assert min_y_dxf <= y_obs_end <= max_y_dxf

        # project obstacle points to resolution
        x_obs_start = int(linear_interpolation(x_obs_start, min_x_dxf, max_x_dxf, 0, resolution_width))
        x_obs_end = int(linear_interpolation(x_obs_end, min_x_dxf, max_x_dxf, 0, resolution_width))
        y_obs_start = int(linear_interpolation(y_obs_start, min_y_dxf, max_y_dxf, 0, resolution_height))
        y_obs_end = int(linear_interpolation(y_obs_end, min_y_dxf, max_y_dxf, 0, resolution_height))

        black_coords = np.array([(x_dst, y_dst) for x_dst in range(x_obs_start, x_obs_end) for y_dst in range(y_obs_start, y_obs_end)])
        obstacle_coord_list.append(black_coords)

        # base_image[black_coords[:,0], black_coords[:,1]] = np.array([0, 0, 0])

    # plt.imsave(img_store_path, ndimage.rotate(base_image, 90), vmin=0, vmax=255)
    base_image_cp = base_image.copy()
    for black_coords in obstacle_coord_list:
            base_image_cp[black_coords[:,0], black_coords[:,1]] = np.array([0, 0, 0])

    # plt.imsave(img_store_path, ndimage.rotate(base_image_cp, 90), vmin=0, vmax=255)
        
    for idx, (origin_areas, destination_areas) in enumerate(zip(origin_rectangles_projected, destination_rectangles_projected)):

        # masked_img = layout_mask.copy()
        image_array = base_image.copy()
        for origin in origin_areas:

            x_or_start, x_or_end = origin[0][0], origin[1][0]
            y_or_start, y_or_end = origin[0][1], origin[1][1]

            image_array[x_or_start:x_or_end, y_or_start:y_or_end] = np.array([255, 0, 0])
        
            # red_coords = np.array([(x_or, y_or) for x_or in range(x_or_start, x_or_end) for y_or in range(y_or_start, y_or_end)])
            # image_array[red_coords[:,0], red_coords[:,1]] = np.array([255, 0, 0])

            # masked_img[red_coords[:,0], red_coords[:,1]] = 2

        for destination in destination_areas:

            x_dst_start, x_dst_end = destination[0][0], destination[1][0]
            y_dst_start, y_dst_end = destination[0][1], destination[1][1]

            image_array[x_dst_start:x_dst_end, y_dst_start:y_dst_end] =  np.array([0, 255, 0])

            # green_coords = np.array([(x_dst, y_dst) for x_dst in range(x_dst_start, x_dst_end) for y_dst in range(y_dst_start, y_dst_end)])
            # image_array[green_coords[:,0], green_coords[:,1]] = np.array([0, 255, 0])

            # masked_img[green_coords[:,0], green_coords[:,1]] = 3

        """ image_array_wObs = image_array.copy()
        for black_coords in obstacle_coord_list:
            image_array_wObs[black_coords[:,0], black_coords[:,1]] = np.array([0, 0, 0])
        image_array_wObs = ndimage.rotate(image_array_wObs, 90) """

        image_array = ndimage.rotate(image_array, 90)

        # masked_img = ndimage.rotate(masked_img, 90)

        # plt.axis('off')
        # plt.imshow(image_array, vmin=0, vmax=255)

        # Logging
        cropped_print_layout = xml_filename.split("\\")[-3]
        cropped_print_layout_num = xml_filename.split("\\")[-2].split("__")[0]
        print(f'Saving jpeg in layout={cropped_print_layout} of floorplan {cropped_print_layout_num}, variation {idx} ...')
        
        # save mask + colormap (ground truth)
        img_variations_dir = os.path.join('\\'.join(xml_filename.split('\\')[:-1]), f'img_variations_resolution_{int(resolution_width)}_{int(resolution_height)}')
        if not os.path.isdir(img_variations_dir):
            os.mkdir(img_variations_dir)
        img_store_path = os.path.join(img_variations_dir, xml_filename.split('\\')[-1].replace('.xml', f'_variation_{idx}.jpeg'))
        # plt.imsave(img_store_path.replace('.jpeg', '_gt_mask.jpeg'), masked_img, cmap=get_customized_colormap(class_names))
        # save RGB image (train data)
        # if idx < 20:
        #     plt.imsave(img_store_path, image_array.astype(np.uint8), vmin=0, vmax=255)#
        
        # SAVE INPUT IMG ARRAY AS HDF5
        store_path = os.path.join(subgroup_folder, 'HDF5_'+xml_filename.split('\\')[-1].replace('.xml', f'_variation_{idx}.h5'))
        store_path_wObs = os.path.join(subgroup_folder, 'HDF5_'+xml_filename.split('\\')[-1].replace('.xml', f'_wObs_variation_{idx}.h5'))
        
        f_txt = open(txt_filepath, 'a')
        f_txt.write(f'variation_{idx}: ')
        f_txt.write('\nSRC real:')
        for or_coords in origins[idx]:
            (x_or_start, y_or_start), (x_or_end, y_or_end), _ = or_coords
            f_txt.write(f'[x=({x_or_start}, {x_or_end}), y=({y_or_start}, {y_or_end})]')

        f_txt.write(' ### DST real: ')
        for dst_coords in destinations[idx]:
            (x_dst_start, y_dst_start), (x_dst_end, y_dst_end), _ = dst_coords
            f_txt.write(f'[x=({x_dst_start}, {x_dst_end}), y=({y_dst_start}, {y_dst_end})]')
        
        f_txt.write('\nSRC pixel:')
        for origin in origin_areas:
            x_or_start, x_or_end = origin[0][0], origin[1][0]
            y_or_start, y_or_end = origin[0][1], origin[1][1]

            f_txt.write(f'[x=({x_or_start}, {x_or_end}), y=({y_or_start}, {y_or_end})]')

        f_txt.write(' ### DST pixel: ')
        for destination in destination_areas:
            x_dst_start, x_dst_end = destination[0][0], destination[1][0]
            y_dst_start, y_dst_end = destination[0][1], destination[1][1]

            f_txt.write(f'[x=({x_dst_start}, {x_dst_end}), y=({y_dst_start}, {y_dst_end})]')

        f_txt.write('\n')
        f_txt.close()

        # save with no obstacles
        hf = h5py.File(store_path, 'w')
        hf.create_dataset('img', data=image_array.astype(np.uint8))
        hf.create_dataset('dxf_sizes', data=np.array([min_x_dxf, max_x_dxf, min_y_dxf, max_y_dxf]))
        hf.close()

        # save with obstacles
        """ hf = h5py.File(store_path_wObs, 'w')
        hf.create_dataset('img', data=image_array_wObs.astype(np.uint8))
        hf.create_dataset('dxf_sizes', data=np.array([min_x_dxf, max_x_dxf, min_y_dxf, max_y_dxf]))
        hf.close() """

    # num_agents = [15, 50] if setting in ['corr_e2e', 'corr_cross'] else [15, 25]
    # export2crowdit_project_EGICE(preprocessed_lines, origins, destinations, obstacles, '\\'.join(xml_filename.split('\\')[-3:-1]), crowdit_folder_name='SIMULATIONS_EGICE')
    # line_plotter(preprocessed_lines)
    he = 2