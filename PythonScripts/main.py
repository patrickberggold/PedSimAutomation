import torch
import numpy as np
from my_model_beit import MyModel
from collections import OrderedDict
from PIL import Image
from torchvision import transforms
import matplotlib.pyplot as plt
SEP = '\\'

CUDA_DEVICE = 0 # 0, 1 or 'cpu'
MODE = 'density_class'# implemented: grayscale, evac, evac_only, class_movie, density_reg, density_class, denseClass_wEvac
BATCH_SIZE = 2
ARCH = 'MyModel' # MyModel, DeepLab, BeIT, SegFormer
ADD_INFO = True

test_run = True # limit_batches -> 2 
save_model = False # create folder and save the model

# example input coming from the outside
num_origins = torch.LongTensor([4])
num_destinations = torch.LongTensor([1])
num_agents_id = torch.LongTensor([2])
site_dimensions = torch.FloatTensor([0.55, 0.3])
velocity_id = torch.LongTensor([2])

add_info = [num_origins, num_destinations, num_agents_id, site_dimensions, velocity_id]

config = {
    'decoder_mode': 'fpn',
    'settings': {'final_conv_batch': True, 'marriage_mode': 2, 'hidden_size': 768, 'num_hidden_ca_layers': 3, 'use_pe': False, 'attn_pooling': False},
    'num_hidden_img_layers': 6
}
model = MyModel('density_class', output_channels=4, num_heads=8, additional_info=True, config=config)

model.eval()

image_batch = np.array(Image.open('C:\\Users\\ga78jem\\Downloads\\test_image.png'))
image_batch = image_batch.transpose(2,0,1).astype(np.float32) / 255. 
image_batch = torch.tensor(image_batch).unsqueeze(0)
image_batch = transforms.Normalize(mean=[0.5,0.5,0.5], std=[0.5,0.5,0.5])(image_batch)

prediction_raw = model(image_batch, add_info)

# load checkpoint
ckpt = 'C:\\Users\\ga78jem\\Downloads\\model_epoch=45-step=230000.pth'
state_dict = OrderedDict([(key.replace('model.', ''), tensor.cpu()) if key.startswith('model.') else (key, tensor) for key, tensor in torch.load(ckpt).items()])
module_state_dict = model.state_dict()

mkeys_missing_in_loaded = [module_key for module_key in list(module_state_dict.keys()) if module_key not in list(state_dict.keys())]
lkeys_missing_in_module = [loaded_key for loaded_key in list(state_dict.keys()) if loaded_key not in list(module_state_dict.keys())]

load_dict = OrderedDict()
for key, tensor in module_state_dict.items():
    if key in state_dict.keys():
        load_dict[key] = state_dict[key]
    else:
        load_dict[key] = tensor

model.load_state_dict(load_dict)

prediction_trained = model(image_batch, add_info)

# visualization is still missing
# evac time prediction is still missing