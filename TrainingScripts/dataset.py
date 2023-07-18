from torch.utils.data import Dataset
import numpy as np
from helper import SEP
import albumentations as A
import torch
import sparse
import os
import re

class FloorplanDataset(Dataset):
    def __init__(
        self, 
        img_paths: list, 
        target_paths: list, 
        transform = None
    ):
        self.transform = transform
        self.img_paths = img_paths
        self.target_paths = target_paths
        self.max_floorplan_meters = 64
        self.final_resolution = 640

        self.vel2index = {'10': 0, '13': 1, '20': 2}
        self.num_agents2index = {'10': 0, '20': 1, '30': 2}
        self.data_dict = {}
        add_data_path = 'ExampleDataset'+SEP+'floorplan_info.txt'

        self.load_additional_info(add_data_path)

    def __len__(self):
        return(len(self.img_paths))

    def __getitem__(self, idx):
        img_path, target_path = self.img_paths[idx], self.target_paths[idx]
        
        img = sparse.load_npz(img_path).todense()
        img = img.astype(np.float32) / 255.

        with np.load(target_path) as fp:
            coords = fp["coords"]
            data = fp["data"]
            evac_time = float(data[-1])/2.
            data = np.delete(data, -1)
            shape = tuple(fp["shape"])
            fill_value = fp["fill_value"][()]
            count_frames = sparse.COO(
                coords=coords,
                data=data,
                shape=shape,
                sorted=True,
                has_duplicates=False,
                fill_value=fill_value,
            )

            # normalize counts to time frame duration
            time_frame = evac_time / 8.
            count_frames = count_frames.todense().transpose(1,2,0).astype(np.float32)
            class_frames = count_frames / time_frame

            # Use boolean indexing to assign class labels
            class_1_mask = (class_frames > 0.0) & (class_frames <= 0.4)
            class_2_mask = (class_frames > 0.4) & (class_frames <= 0.8)
            class_3_mask = (class_frames > 0.8)

            class_frames[class_1_mask] = 1
            class_frames[class_2_mask] = 2
            class_frames[class_3_mask] = 3

        img, class_frames = self.augmentations(img, class_frames)

        if self.transform:
            img = self.transform(img)

        # get additional information
        info_dict = self.data_dict['variation_'+img_path.split(SEP)[-1].split('_')[1][0]]

        num_origins = len(info_dict['origins'])
        num_destination = len(info_dict['destinations'])
        num_agents = target_path.split('AGENTS_PER_SRC_')[-1].split('_')[0]
        num_agents_id = self.num_agents2index[num_agents]
        
        velocity = target_path.split('VEL_')[-1][:2]
        velocity_id = self.vel2index[velocity]
        
        site_dimensions = np.array([info_dict['site_x'], info_dict['site_y']], dtype=np.float32) / 100.
        
        return img, (class_frames, evac_time), [num_origins, num_destination, num_agents_id, site_dimensions, velocity_id] 
           

    def augmentations(self, image, class_frames):
        # flipping, transposing, random 90 deg rotations
        transform = A.Compose([
            A.augmentations.geometric.transforms.HorizontalFlip(p=0.5),
            A.augmentations.geometric.transforms.VerticalFlip(p=0.5),
            A.augmentations.geometric.transforms.Transpose(p=0.5),
            A.augmentations.geometric.rotate.RandomRotate90(p=0.5),
        ])
        
        transformed = transform(image=image, mask=class_frames)
        
        image = torch.tensor(transformed['image']).permute(2, 0, 1).float()
        class_frames = torch.tensor(transformed['mask']).permute(2, 0, 1).long()

        return image, class_frames


    def load_additional_info(self, add_data_path):
        assert os.path.isfile(add_data_path)
        
        self.data_dict = {}

        lines = open(add_data_path, 'r').readlines()
        for idx, line in enumerate(lines):
            if line.startswith('variation'):
                site_x = float(lines[idx+1].strip().split(":")[1])
                site_y = float(lines[idx+2].strip().split(":")[1])
                data_line = lines[idx+3].strip()
                or_data_line = data_line.split(':')[1].split('#')[0].strip()
                dst_data_line = data_line.split(':')[2].strip()

                origins = re.findall(r'\[.*?\]', or_data_line)
                destinations = re.findall(r'\[.*?\]', dst_data_line)

                def extract_area_points(areas, a_type):
                    variation_dict = {}
                    for id_o, area in enumerate(areas):
                        xs = area.split('=(')[1]
                        x_start = float(xs.split(',')[0])
                        x_end = float(xs.split(',')[1].split(')')[0])
                        ys = area.split('=(')[2]
                        y_start = float(ys.split(',')[0])
                        y_end = float(ys.split(',')[1].split(')')[0])
                        
                        variation_dict.update({
                            f'{a_type}_{id_o}': {
                                'x_start': x_start,
                                'x_end': x_end,
                                'y_start': y_start,
                                'y_end': y_end 
                            }
                        })
                    return variation_dict
                
                extracted_origins = extract_area_points(origins, 'origin')
                extracted_destinations = extract_area_points(destinations, 'dst')

                self.data_dict.update({
                    line.split(':')[0]: {
                    'origins': extracted_origins,
                    'destinations': extracted_destinations,
                    'site_x': site_x,
                    'site_y': site_y
                }})