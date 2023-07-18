import torch
import pytorch_lightning as pl
from torchvision.transforms import Compose, Normalize, Resize
from torch.utils.data import DataLoader
import os, random
from dataset import FloorplanDataset
from helper import SEP
from transformers import BeitFeatureExtractor

class FloorplanDatamodule(pl.LightningDataModule):
    def __init__(self, config: dict, num_workers: int = 0):
        super().__init__()
        self.batch_size = config['batch_size']
        self.cuda_device = config['cuda_device']
        self.num_workers = num_workers

        feature_extractor = BeitFeatureExtractor.from_pretrained('microsoft/beit-base-finetuned-ade-640-640')
        self.train_transforms = Compose([
            Normalize(mean=feature_extractor.image_mean, std=feature_extractor.image_std),
        ])
        self.val_transforms = Compose([
            Normalize(mean=feature_extractor.image_mean, std=feature_extractor.image_std),
            ])
        self.set_data_paths()

    def setup(self, stage):
        self.train_dataset = FloorplanDataset(self.train_imgs_list, self.train_tars_list, transform=self.train_transforms)
        self.val_dataset = FloorplanDataset(self.val_imgs_list, self.val_tars_list, transform=self.val_transforms)
        self.test_dataset = FloorplanDataset(self.test_imgs_list, self.test_tars_list, transform=self.val_transforms)

    def train_dataloader(self):
        return DataLoader(self.train_dataset, batch_size=self.batch_size, num_workers=self.num_workers)

    def val_dataloader(self):
        return DataLoader(self.val_dataset, batch_size=self.batch_size, num_workers=self.num_workers)

    def test_dataloader(self):
        return DataLoader(self.test_dataset, batch_size=self.batch_size)

    # def predict_dataloader(self):
    #     return DataLoader(self.mnist_predict, batch_size=self.batch_size)

    def set_batch_size(self, new_batch_size):
        self.batch_size = new_batch_size

    def transfer_batch_to_device(self, batch, device, dataloader_idx):
        if self.cuda_device != 'cpu':
            device = torch.device('cuda', self.cuda_device)
            batch = super().transfer_batch_to_device(batch, device, dataloader_idx)
            return batch

    def set_data_paths(self):
        
        self.splits = [0.7, 0.15, 0.15]

        self.image_path = SEP.join(['ExampleDataset', 'inputs'])
        self.target_path = SEP.join(['ExampleDataset', 'targets'])
        
        self.set_filepaths()

        assert len(self.image_list) == len(self.target_list), 'Images list and target list do not have same length!'
    	
        val_split_factor = self.splits[1]
        test_split_factor = self.splits[2]
        
        self.indices = list(range(len(self.image_list)))
        
        val_split_index = round(len(self.indices) * val_split_factor)
        test_split_index = round(len(self.indices) * test_split_factor)
        
        random.seed(42)
        random.shuffle(self.indices)

        self.train_imgs_list = [self.image_list[idx] for idx in self.indices[(test_split_index + val_split_index):]]
        self.train_tars_list = [self.target_list[idx] for idx in self.indices[(test_split_index + val_split_index):]]
        
        self.val_imgs_list = [self.image_list[idx] for idx in self.indices[test_split_index:(test_split_index + val_split_index)]]
        self.val_tars_list = [self.target_list[idx] for idx in self.indices[test_split_index:(test_split_index + val_split_index)]]

        self.test_imgs_list = [self.image_list[idx] for idx in self.indices[:test_split_index]]
        self.test_tars_list = [self.target_list[idx] for idx in self.indices[:test_split_index]]


    def set_filepaths(self):

        self.image_list = []
        self.target_list = []

        self.target_list = [os.path.join(self.target_path, t) for t in os.listdir(self.target_path)]

        for t in os.listdir(self.target_path):
            gt_image = 'variation_'+t.split('_')[1]
            suffix = '.npz' if 'wObs' not in t else '_wObs.npz'
            gt_image += suffix
            self.image_list.append(os.path.join(self.image_path, gt_image))
        