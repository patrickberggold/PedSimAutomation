import time
import os
import torch
import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint, LearningRateMonitor
from pytorch_lightning.callbacks.early_stopping import EarlyStopping
from image_module import ImageModule
from datamodule import FloorplanDatamodule
from helper import SEP, dir_maker, class_visualization

CUDA_DEVICE = 1 # 0, 1 or 'cpu'
BATCH_SIZE = 2

test_run = True # limit_batches -> 2 
save_model = False # create folder and save the model

do_training = True

CONFIG = {
    'cuda_device': CUDA_DEVICE,
    'batch_size': BATCH_SIZE,
    'from_ckpt_path': None,
    'load_to_ckpt_path': None,
    'run_test_epoch': test_run,
    'save_model': save_model
}

TRAIN_DICT = {
    'learning_rate': 0.0005, 
    'lr_sch_factor': 0.75,
    'lr_sch_patience': 3,
    'init': 'xavier',
    'loss_dict': {'alpha': 0.1, 'beta': 0.9},
    'early_stopping_patience': 7,
}


if __name__ == '__main__':

    datamodule = FloorplanDatamodule(config = CONFIG)

    module = ImageModule(config=CONFIG, train_config=TRAIN_DICT)

    # Load from checkpoint
    if CONFIG['from_ckpt_path']:
        ckpt_folder = os.path.join('checkpoints', CONFIG['from_ckpt_path'])
        ckpt_file = [file for file in os.listdir(ckpt_folder) if file.endswith('.ckpt')][0]
        ckpt_path = os.path.join(ckpt_folder, ckpt_file)

        module.load_state_dict(torch.load(ckpt_path)['state_dict'])

    if do_training:
        description_log = ''
        if save_model and not test_run:
            if not os.path.isdir('checkpoints'): os.mkdir('checkpoints')
            store_folder_path = SEP.join(['checkpoints', CONFIG['load_to_ckpt_path']])
            dir_maker(store_folder_path, description_log, CONFIG, TRAIN_DICT)

        callbacks = [EarlyStopping(monitor="val_loss", mode="min", patience=TRAIN_DICT['early_stopping_patience']), LearningRateMonitor(logging_interval='epoch')]
        
        if save_model and not test_run:
            model_checkpoint = ModelCheckpoint(
                dirpath = store_folder_path,
                filename = 'model_{epoch}-{step}',
                save_top_k = 1,
                verbose = True, 
                monitor = 'val_loss',
                mode = 'min'
            )
            callbacks.append(model_checkpoint)

        limit_batches = 2 if test_run else None
        trainer = pl.Trainer(
            gpus = [CUDA_DEVICE], 
            devices=f'cuda:{str(CUDA_DEVICE)}', 
            max_epochs = 500, 
            callbacks=callbacks,
            limit_train_batches=limit_batches,
            limit_val_batches=limit_batches,
            )

        start_training_time = time.time()
        trainer.fit(module, datamodule=datamodule)
        print(f'Training took {(time.time() - start_training_time)/60./(module.current_epoch+1):.3f} minutes per epoch...')

    else:
        # visualize classes within the ground truth floorplan image (or potentially evaluate checkpoint on the test set)
        datamodule.setup(stage='test')
        
        for idx, batch in enumerate(datamodule.test_dataloader()):
            floorplan_images = batch[0]
            class_frames, evac_times = batch[1]
            for img, cls_fr in zip(floorplan_images, class_frames):
                class_visualization(img, cls_fr)