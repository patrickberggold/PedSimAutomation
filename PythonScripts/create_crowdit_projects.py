import itertools
from math import ceil
import os
from transformers.models.beit import modeling_beit

def write_crowdit_meta_folder(meta_folder, source_dict, dst_dict, num_agents, spawn_times, velocity=[1.34, 0.46, 1.61]):
    intervals_text = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<root xmlFormat="0.10.2" isoDate="2022-05-25T09:02:45.691517600Z">\n'
    for id_s, key_s in enumerate(source_dict):
        intervals_text += f'\t<intervals id="{key_s}_INTERVALS">\n\t\t<interval from="0" to="{spawn_times[id_s]}" howMany="{num_agents}" group="false"/>\n\t</intervals>\n'
    for key_d in dst_dict:
        intervals_text += f'\t<intervals id="{key_d}_INTERVALS"/>\n'
    intervals_text += '</root>'
    
    intervals_file = os.path.join(meta_folder, 'intervals.xml')

    with open(intervals_file, 'w') as f_i:
        f_i.write(intervals_text)
    f_i.close()

    personas_text = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<agents xmlFormat="0.10.2" isoDate="2022-05-25T09:02:45.686517300Z">\n\t<persona id="DEFAULT">'
    personas_text += f'\n\t\t<velocity>\n\t\t\t<distribution min="{velocity[1]}" max="{velocity[2]}" mean="{velocity[0]}" deviation="0.26" type="normal"/>\n\t\t</velocity>'
    personas_text += '\n\t\t<torsoSize acceptedOverlap="0.15">\n\t\t\t<distribution min="0.42" max="0.46" mean="0.44" deviation="0.0" type="uniform"/>\n\t\t</torsoSize>\n\t\t<behavior perceptionRadius="2.0" socialDist="0.0"/>\n\t\t<ignoredSimulationObjects/>\n\t</persona>\n</agents>'
    personas_file = os.path.join(meta_folder, 'personas.xml')

    with open(personas_file, 'w') as f_p:
        f_p.write(personas_text)
    f_p.close()

    premove_times_text = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<root xmlFormat="0.10.2" isoDate="2022-05-25T09:02:45.693517400Z">\n'
    for key_s2 in source_dict:
        premove_times_text += f'\t<premovement allAtOnce="false" id="{key_s2}_PREMOVE">\n\t\t<distribution min="0.0" max="0.0" mean="0.0" deviation="0.0" type="none"/>\n\t</premovement>\n'
    premove_times_text += '</root>'
    
    premove_times_file = os.path.join(meta_folder, 'premovement-times.xml')
    with open(premove_times_file, 'w') as f_pt:
        f_pt.write(premove_times_text)
    f_pt.close()

def write_crowdit_project_file(project_filename, project_name, floor_filename, source_dict, dst_dict, path_combinations, path_prob, is_set):

    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n'
    scenario_header = f'<scenario xmlFormat="0.10.2" isoDate="2022-05-25T09:02:45.684518300Z" name="{project_name}">\n\t<spatial>\n'
    floor_line = f'\t\t<floor id="{floor_filename.split("/")[1].replace(".floor", "")}" floorAt="{floor_filename}" />\n'    
    scenario_bottom = '\t</spatial>\n\t<meta>\n\t\t<paths>\n'
    paths = ''
    for id_p, path in enumerate(path_combinations):
        paths += f'\t\t\t<path id="Pfad-{id_p}" ratio="{path_prob}">{path[0]},{path[1]}</path>\n'
    paths += '\t\t</paths>\n\t\t<backgroundImages />\n\t\t<pedCharacters>\n\t\t\t<type name="FPLMWalking" ratio="1.0" />\n\t\t</pedCharacters>\n'
    origins_data = '\t\t<morphosis>\n'
    for key_s in source_dict:
        origins_data += f'\t\t\t<origin id="{key_s}" wunderZone="{source_dict[key_s][0]}">\n'
        origins_data += '\t\t\t\t<personas>\n\t\t\t\t\t<persona ref="DEFAULT">1.0</persona>\n\t\t\t\t</personas>\n'
        origins_data += f'\t\t\t\t<premovement ref="{key_s}_PREMOVE" />\n\t\t\t\t<positioning generationPattern="quadratic" comfortDistance="0.0" />\n\t\t\t\t<intervals ref="{key_s}_INTERVALS" />\n'
        origins_data += '\t\t\t</origin>\n'
    destinations_data = ''
    for key_d in dst_dict:
        destinations_data += f'\t\t\t<destination id="{key_d}" wunderZone="{dst_dict[key_d][0]}" disableDynamicFlooding="false">\n\t\t\t\t<intervals ref="{key_d}_INTERVALS" />\n\t\t\t</destination>\n'
    filler = '\t\t</morphosis>\n'
    
    if is_set:
        sets = f'\t\t<sets>\n\t\t\t<set id="{path_combinations[0][1]}">\n\t\t\t\t<members>\n'
        for d_key in dst_dict:
            sets += f'\t\t\t\t\t<member>{d_key}</member>\n'
        sets += '\t\t\t\t</members>\n'
        sets += '\t\t\t\t<filterChains>\n\t\t\t\t\t<filterChain id="Naechstgelegen" fromSec="0.0" toSec="-1.0">\n'
        sets += '\t\t\t\t\t\t<filter type="distance" xBest="1" closest="true" />\n'
        sets += '\t\t\t\t\t</filterChain>\n\t\t\t\t</filterChains>\n\t\t\t</set>\n'
        sets += f'\t\t\t<set id="{path_combinations[0][0]}">\n\t\t\t\t<members>\n'
        for s_key in source_dict:
            sets += f'\t\t\t\t\t<member>{s_key}</member>\n'
        sets += '\t\t\t\t</members>\n'
        sets += '\t\t\t\t<filterChains>\n\t\t\t\t\t<filterChain id="Naechstgelegen" fromSec="0.0" toSec="-1.0">\n'
        sets += '\t\t\t\t\t\t<filter type="distance" xBest="1" closest="true" />\n'
        sets += '\t\t\t\t\t</filterChain>\n\t\t\t\t</filterChains>\n\t\t\t</set>\n\t\t</sets>\n'
    else:
        sets = '\t\t<sets />\n'

    filler2 = '\t\t<pathSnippets />\n\t\t<floorProps>\n'
    floorProps = f'\t\t\t<floorProp floor="{floor_filename.split("/")[1].replace(".floor", "")}" cellDist="0.1" elevation="0.0" height="2.5" />\n\t\t</floorProps>\n'
    filler3 = '\t\t<groups>\n\t\t\t<row>1,1.0</row>\n\t\t</groups>\n\t\t<elevatorMatrices />\n\t</meta>\n'
    bottom = '\t<settings />\n\t<evaluations>\n\t\t<measurements />\n\t</evaluations>\n\t<visualization>\n\t\t<colorings>\n\t\t\t<class rgba="232,139,15,100" visible="false">wunderZone</class>\n\t\t</colorings>\n\t</visualization>\n\t<reporting>\n\t\t<reportElements />\n\t</reporting>\n</scenario>'

    project_xml_text = xml_header + scenario_header + floor_line + scenario_bottom + paths + origins_data + destinations_data + filler 
    project_xml_text += sets + filler2 + floorProps + filler3 + bottom

    with open(project_filename, 'w') as f:
        f.write(project_xml_text)
    f.close()

def export2crowdit_project(preprocessed_lines, origins, destinations, obstacles, crowdit_descr, num_agents_list):

    crowdit_descr= crowdit_descr.replace('floorplan_', '') # necessary because of path lenght issues

    root_folder = 'C:\\Users\\ga78jem\\Documents\\Crowdit\\ADVANCED_EXPERIMENTS_NEW'
    for idf in range(len(crowdit_descr.split('\\'))):
        new_path = os.path.join(root_folder, '\\'.join(crowdit_descr.split('\\')[:idf]))
        if not os.path.isdir(new_path): os.mkdir(new_path)

    crowdit_folder = os.path.join(root_folder, crowdit_descr)
    if not os.path.isdir(crowdit_folder): os.mkdir(crowdit_folder)

    header = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    floor_header = '<floor isoDate="2022-05-24T13:17:59.807407200Z" srcFile="INSERT_SRC_DXF" xmlFormat="0.10.2">\n'
    layer_0 = '\t<layer id="0"/>\n'
    layer_A_WALL = '\t<layer id="A-WALL-____-MCUT">\n'
    layer_A_WALL_bottom = '\t</layer>\n'
    layer_crowdit = '\t<layer id="crowdit">\n'
    layer_crowdit_bottom = '\t</layer>\n'
    floor_bottom = '</floor>'
    wall_content = ''
    crowdit_content = ''

    for idx, line in enumerate(preprocessed_lines):
        wall = f'\t\t<wall closed="false" id="w{idx+2}">\n'
        for point in line:
            x = {round(point[0], 2)}
            y = {round(point[1], 2)}
            wall += f'\t\t\t<point x="{round(point[0], 2)}" y="{round(point[1], 2)}"/>\n'
        wall += '\t\t</wall>\n'
        wall_content += wall

    for obstacle in obstacles:
        p1 = (obstacle[0][0], obstacle[0][1])
        p2 = (obstacle[1][0], obstacle[0][1])
        p3 = (obstacle[1][0], obstacle[1][1])
        p4 = (obstacle[0][0], obstacle[1][1])
        obstacle_lines = [
            [p1, p2], [p2, p3], [p3, p4], [p4, p1]
            ]
        for idx, obs_line in enumerate(obstacle_lines):
            wall = f'\t\t<wall closed="false" id="w{len(preprocessed_lines)+idx+2}">\n'
            for point in obs_line:
                wall += f'\t\t\t<point x="{round(point[0], 2)}" y="{round(point[1], 2)}"/>\n'
            wall += '\t\t</wall>\n'
            wall_content += wall

    for id_oas, origins_areas in enumerate(origins):
        destination_areas = destinations[id_oas]
        crowdit_content = ''
        source_dict = {}
        dst_dict = {}
        for id_o, origin in enumerate(origins_areas):

            s1x = origin[0][0]
            s1y = origin[0][1]
            s2x = origin[1][0]
            s2y = origin[1][1]

            source_dict.update({f'Quelle-{id_o}': [f'simObj-{id_o}', origin[2]]})

            crowdit_content += f'\t\t<wunderZone id="simObj-{id_o}">\n'
            crowdit_content += f'\t\t\t<point x="{s1x}" y="{s1y}"/>\n'
            crowdit_content += f'\t\t\t<point x="{s2x}" y="{s1y}"/>\n'
            crowdit_content += f'\t\t\t<point x="{s2x}" y="{s2y}"/>\n'
            crowdit_content += f'\t\t\t<point x="{s1x}" y="{s2y}"/>\n'
            crowdit_content += '\t\t</wunderZone>\n'

        for id_d, destination in enumerate(destination_areas):
            d1x = destination[0][0]
            d1y = destination[0][1]
            d2x = destination[1][0]
            d2y = destination[1][1]

            dst_dict.update({f'Ziel-{id_d}': [f'simObj-{len(source_dict)+id_d}', destination[2]]})

            crowdit_content += f'\t\t<wunderZone id="simObj-{len(source_dict)+id_d}">\n'
            crowdit_content += f'\t\t\t<point x="{d1x}" y="{d1y}"/>\n'
            crowdit_content += f'\t\t\t<point x="{d2x}" y="{d1y}"/>\n'
            crowdit_content += f'\t\t\t<point x="{d2x}" y="{d2y}"/>\n'
            crowdit_content += f'\t\t\t<point x="{d1x}" y="{d2y}"/>\n'
            crowdit_content += '\t\t</wunderZone>\n'
        
        xml_text = header + floor_header + layer_0 + layer_A_WALL + wall_content + layer_A_WALL_bottom + layer_crowdit + crowdit_content + layer_crowdit_bottom + floor_bottom

        variation_folder = os.path.join(crowdit_folder, f'variation_{id_oas}')
        if not os.path.isdir(variation_folder): os.mkdir(variation_folder)

        # PARAMETERS FOR CROWDIT
        PATH_PROBABILITIES = 1/len(dst_dict)
        # TODO only one path combination is implemented for now, namely going to 
        # all destinations with equal probability
        
        path_variations = list(itertools.product(source_dict.keys(), dst_dict.keys()))

        for num_agents in num_agents_list:

            subfolder_name = os.path.join(variation_folder, f'AGENTS_PER_SRC_{num_agents}')
            if not os.path.isdir(subfolder_name): os.mkdir(subfolder_name)
           
            if '\\' in crowdit_descr: crowdit_descr = crowdit_descr.split('\\')[-1]
            project_folder = os.path.join(subfolder_name, f'project_{crowdit_descr.split("__")[0]}_{id_oas}_res')
            if not os.path.isdir(project_folder): os.mkdir(project_folder)

            geometry_folder = os.path.join(project_folder, 'geometry')
            if not os.path.isdir(geometry_folder): os.mkdir(geometry_folder)

            meta_folder = os.path.join(project_folder, 'meta')
            if not os.path.isdir(meta_folder): os.mkdir(meta_folder)

            spawing_agents_per_second = []
            for keys in source_dict:
                if source_dict[keys][1] < 5.:
                    spawing_agents_per_second.append(1.)
                elif 5. <= source_dict[keys][1] < 8.:
                    spawing_agents_per_second.append(2.)
                elif 8. <= source_dict[keys][1] < 15.:
                    spawing_agents_per_second.append(3.)
                else:
                    spawing_agents_per_second.append(4.)
            
            # spawing_agents_per_second = 5.0
            spawn_times = [ceil(num_agents/spawing_agents_per_area) for spawing_agents_per_area in spawing_agents_per_second]

            write_crowdit_meta_folder(meta_folder, source_dict, dst_dict, num_agents, spawn_times)

            floorname = os.path.join(geometry_folder, f'floorplan_variation_{id_oas}_agents_{num_agents}.floor')

            write_crowdit_project_file(
                project_filename = os.path.join(subfolder_name, f'project_{crowdit_descr.split("__")[0]}_{id_oas}.crowdit'), 
                project_name = f'project_{crowdit_descr.split("__")[0]}_{id_oas}',
                floor_filename = f'geometry/floorplan_variation_{id_oas}_agents_{num_agents}.floor',
                source_dict = source_dict, 
                dst_dict = dst_dict,
                path_combinations = path_variations,
                path_prob = PATH_PROBABILITIES
                )
            with open(floorname, 'w') as f:
                f.write(xml_text)
            f.close()

def export2crowdit_project_EGICE(preprocessed_lines, origins, destinations, obstacles, crowdit_descr, crowdit_folder_name):

    """
    /** * The repulsion between pedestrians is taken from * M. J. Seitz and G. Koester, Natural discretization of pedestrian movement in continuous space, * American Physical Society, PHYSICAL REVIEW E 2012, 86, 046108 * PHYSICAL REVIEW E 2012 * <p> * AND * M. J. Seitz, F. Dietrich and G. Köster "The effect of stepping on pedestrian trajectories", * Physica A: Statistical Mechanics and its Applications  03/2015; 421. */

    Bachelor thesis of Zoennchen (2013):// "Navigation around pedestrian groups and queueing using a dynamic adaption of traveling times// in the Fast Marching Algorithm."
    """

    crowdit_descr = crowdit_descr.replace('floorplan_', '') # necessary because of path lenght issues

    root_folder = 'C:\\Users\\ga78jem\\Documents\\Crowdit\\'+crowdit_folder_name
    if not os.path.isdir(root_folder): os.mkdir(root_folder)
    if not os.path.isdir(os.path.join(root_folder, crowdit_descr.split('\\')[0])): os.mkdir(os.path.join(root_folder, crowdit_descr.split('\\')[0]))

    crowdit_folder = os.path.join(root_folder, crowdit_descr)
    if not os.path.isdir(crowdit_folder): os.mkdir(crowdit_folder)

    crowdit_folder_obs = crowdit_folder+'_wObs'
    if not os.path.isdir(crowdit_folder_obs): os.mkdir(crowdit_folder_obs)

    header = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    floor_header = '<floor isoDate="2022-05-24T13:17:59.807407200Z" srcFile="INSERT_SRC_DXF" xmlFormat="0.10.2">\n'
    layer_0 = '\t<layer id="0"/>\n'
    layer_A_WALL = '\t<layer id="A-WALL-____-MCUT">\n'
    layer_A_WALL_bottom = '\t</layer>\n'
    layer_crowdit = '\t<layer id="crowdit">\n'
    layer_crowdit_bottom = '\t</layer>\n'
    floor_bottom = '</floor>'
    wall_content = ''
    crowdit_content = ''
    obstacle_content = ''

    o_d_distributions = ['shortest', 'uniform']
    velocities_mean =   [1.34, 1.0, 2.0]
    velocity_min =      [0.46, 0.46, 1.0]
    velocities_max =    [1.61, 1.61, 2.5]
    num_agents_list =   [30, 20, 10,]
    # TODO torso overlap?
    torso_overlaps = []


    for idx, line in enumerate(preprocessed_lines):
        wall = f'\t\t<wall closed="false" id="w{idx+2}">\n'
        for point in line:
            x = {round(point[0], 2)}
            y = {round(point[1], 2)}
            wall += f'\t\t\t<point x="{round(point[0], 2)}" y="{round(point[1], 2)}"/>\n'
        wall += '\t\t</wall>\n'
        wall_content += wall

    for obstacle in obstacles:
        p1 = (obstacle[0][0], obstacle[0][1])
        p2 = (obstacle[1][0], obstacle[0][1])
        p3 = (obstacle[1][0], obstacle[1][1])
        p4 = (obstacle[0][0], obstacle[1][1])
        obstacle_lines = [
            [p1, p2], [p2, p3], [p3, p4], [p4, p1]
            ]
        for idx, obs_line in enumerate(obstacle_lines):
            wall = f'\t\t<wall closed="false" id="w{len(preprocessed_lines)+idx+2}">\n'
            for point in obs_line:
                wall += f'\t\t\t<point x="{round(point[0], 2)}" y="{round(point[1], 2)}"/>\n'
            wall += '\t\t</wall>\n'
            obstacle_content += wall

    for id_oas, origins_areas in enumerate(origins):
        destination_areas = destinations[id_oas]
        crowdit_content = ''
        source_dict = {}
        dst_dict = {}
        for id_o, origin in enumerate(origins_areas):

            s1x = origin[0][0]
            s1y = origin[0][1]
            s2x = origin[1][0]
            s2y = origin[1][1]

            source_dict.update({f'Quelle-{id_o}': [f'simObj-{id_o}', origin[2]]})

            crowdit_content += f'\t\t<wunderZone id="simObj-{id_o}">\n'
            crowdit_content += f'\t\t\t<point x="{s1x}" y="{s1y}"/>\n'
            crowdit_content += f'\t\t\t<point x="{s2x}" y="{s1y}"/>\n'
            crowdit_content += f'\t\t\t<point x="{s2x}" y="{s2y}"/>\n'
            crowdit_content += f'\t\t\t<point x="{s1x}" y="{s2y}"/>\n'
            crowdit_content += '\t\t</wunderZone>\n'

        for id_d, destination in enumerate(destination_areas):
            d1x = destination[0][0]
            d1y = destination[0][1]
            d2x = destination[1][0]
            d2y = destination[1][1]

            dst_dict.update({f'Ziel-{id_d}': [f'simObj-{len(source_dict)+id_d}', destination[2]]})

            crowdit_content += f'\t\t<wunderZone id="simObj-{len(source_dict)+id_d}">\n'
            crowdit_content += f'\t\t\t<point x="{d1x}" y="{d1y}"/>\n'
            crowdit_content += f'\t\t\t<point x="{d2x}" y="{d1y}"/>\n'
            crowdit_content += f'\t\t\t<point x="{d2x}" y="{d2y}"/>\n'
            crowdit_content += f'\t\t\t<point x="{d1x}" y="{d2y}"/>\n'
            crowdit_content += '\t\t</wunderZone>\n'
        
        xml_text = header + floor_header + layer_0 + layer_A_WALL + wall_content + layer_A_WALL_bottom + layer_crowdit + crowdit_content + layer_crowdit_bottom + floor_bottom
        xml_text_obs = header + floor_header + layer_0 + layer_A_WALL + wall_content + obstacle_content + layer_A_WALL_bottom + layer_crowdit + crowdit_content + layer_crowdit_bottom + floor_bottom

        variation_folder = os.path.join(crowdit_folder, f'variation_{id_oas}')
        if not os.path.isdir(variation_folder): os.mkdir(variation_folder)

        variation_folder_obs = os.path.join(crowdit_folder_obs, f'variation_{id_oas}')
        if not os.path.isdir(variation_folder_obs): os.mkdir(variation_folder_obs)

        for num_agents in num_agents_list:

            for distr in o_d_distributions:

                for v_mean, v_min, v_max in zip(velocities_mean, velocity_min, velocities_max):

                    vel_str = str(v_mean).replace('.', '')

                    subfolder_name = os.path.join(variation_folder, f'AGENTS_PER_SRC_{num_agents}_DISTR_{distr}_VEL_{vel_str}')
                    if not os.path.isdir(subfolder_name): os.mkdir(subfolder_name)

                    subfolder_name_obs = os.path.join(variation_folder_obs, f'AGENTS_PER_SRC_{num_agents}_DISTR_{distr}_VEL_{vel_str}')
                    if not os.path.isdir(subfolder_name_obs): os.mkdir(subfolder_name_obs)

                    if '\\' in crowdit_descr: crowdit_descr = crowdit_descr.split('\\')[-1]
                    project_folder = os.path.join(subfolder_name, f'project_{crowdit_descr.split("__")[0]}_{id_oas}_res')
                    if not os.path.isdir(project_folder): os.mkdir(project_folder)

                    project_folder_obs = os.path.join(subfolder_name_obs, f'project_{crowdit_descr.split("__")[0]}_{id_oas}_res')
                    if not os.path.isdir(project_folder_obs): os.mkdir(project_folder_obs)

                    geometry_folder = os.path.join(project_folder, 'geometry')
                    if not os.path.isdir(geometry_folder): os.mkdir(geometry_folder)

                    geometry_folder_obs = os.path.join(project_folder_obs, 'geometry')
                    if not os.path.isdir(geometry_folder_obs): os.mkdir(geometry_folder_obs)

                    meta_folder = os.path.join(project_folder, 'meta')
                    if not os.path.isdir(meta_folder): os.mkdir(meta_folder)

                    meta_folder_obs = os.path.join(project_folder_obs, 'meta')
                    if not os.path.isdir(meta_folder_obs): os.mkdir(meta_folder_obs)

                    spawn_times = [1 for key in source_dict]

                    write_crowdit_meta_folder(
                        meta_folder, source_dict, dst_dict, num_agents, spawn_times, velocity=[v_mean, v_min, v_max]
                    )

                    write_crowdit_meta_folder(
                        meta_folder_obs, source_dict, dst_dict, num_agents, spawn_times, velocity=[v_mean, v_min, v_max]
                    )

                    floorname = os.path.join(geometry_folder, f'floorplan_variation_{id_oas}_agents_{num_agents}.floor')
                    with open(floorname, 'w') as f:
                        f.write(xml_text)
                    f.close()

                    floorname_obs = os.path.join(geometry_folder_obs, f'floorplan_variation_{id_oas}_agents_{num_agents}.floor')
                    with open(floorname_obs, 'w') as fobs:
                        fobs.write(xml_text_obs)
                    fobs.close()

                    if distr == 'uniform':
                        path_variations = list(itertools.product(source_dict.keys(), dst_dict.keys()))
                        path_prob = 1/len(dst_dict)
                        is_set = False
                    elif distr == 'shortest':
                        path_variations = [['Origin_set', 'Destination_set']]
                        path_prob = 1.0
                        is_set = True

                    for folder_name in [subfolder_name, subfolder_name_obs]:
                        write_crowdit_project_file(
                            project_filename = os.path.join(folder_name, f'project_{crowdit_descr.split("__")[0]}_{id_oas}.crowdit'), 
                            project_name = f'project_{crowdit_descr.split("__")[0]}_{id_oas}',
                            floor_filename = f'geometry/floorplan_variation_{id_oas}_agents_{num_agents}.floor',
                            source_dict = source_dict, 
                            dst_dict = dst_dict,
                            path_combinations = path_variations,
                            path_prob = path_prob,
                            is_set = is_set
                        )

