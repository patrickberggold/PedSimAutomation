import torch
import numpy as np
from my_model_beit import MyModel
from collections import OrderedDict
from torchvision import transforms
import matplotlib.pyplot as plt
import PIL
from PIL import Image as PilImage
SEP = '\\'

def get_color(class_label):
    if class_label == 1: return np.array([143, 225,255], dtype=np.uint8)
    elif class_label == 2: return np.array([0, 0, 255], dtype=np.uint8)
    elif class_label == 3: return np.array([255, 0,255], dtype=np.uint8)
    return None


CUDA_DEVICE = 'cpu' # 0, 1 or 'cpu'
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

# image = np.array(PIL.Image.open('C:\\Users\\ga78jem\\Downloads\\test_image.png')) 
image = np.array(PIL.Image.open(r"C:\Users\mohab\Documents\TUM\HiWiPatrick\PedSimAutomation\PythonScripts/test_image.png")) 
image_t = image.transpose(2,0,1).astype(np.float32) / 255.
image_t = torch.tensor(image_t).unsqueeze(0)
image_t = transforms.Normalize(mean=[0.5,0.5,0.5], std=[0.5,0.5,0.5])(image_t)

# prediction_raw = model(image_t, add_info)

# load checkpoint
# ckpt = 'C:\\Users\\ga78jem\\Downloads\\model_epoch=45-step=230000.pth'
ckpt = r"C:\Users\mohab\Documents\TUM\HiWiPatrick\PedSimAutomation\PythonScripts/model_epoch=45-step=230000.pth"
# state_dict = OrderedDict([(key.replace('model.', ''), tensor.cpu()) if key.startswith('model.') else (key, tensor) for key, tensor in torch.load(ckpt).items()])
state_dict = OrderedDict([(key.replace('model.', ''), tensor.cpu()) if key.startswith('model.') else (key, tensor) for key, tensor in torch.load(ckpt , map_location=torch.device('cpu')).items()])
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

# evac time prediction is still missing
# FORWARD PASS & VISUALIZATION
if MODE == 'denseClass_wEvac':
    dense_pred, evac_time_pred = model(image_t, add_info)
    MODE = 'density_class'
else:
    dense_pred = model(image_t, add_info)

predicted_frames = []

dense_pred = dense_pred.squeeze().cpu().detach().numpy()
dense_pred = np.argmax(dense_pred, axis=0)
dense_pred = dense_pred.transpose(1,2,0)
num_frames = dense_pred.shape[-1]

cell_size = 4
add_vector_template = np.zeros((cell_size**2,2), dtype=np.int32)
for x in range(cell_size):
    for y in range(cell_size):
        add_vector_template[cell_size*x + y] = np.array([x, y], dtype=np.int32)

for frame_id in range(num_frames):

    frame_pred_np = dense_pred[:,:,frame_id]
    nnz_coords = np.argwhere(frame_pred_np > 0).squeeze()
    pred_counts = frame_pred_np[nnz_coords[:,0], nnz_coords[:,1]]
    # scale up
    nnz_coords = np.repeat(nnz_coords, cell_size**2, axis=0) * cell_size
    add_vector = np.tile(add_vector_template.transpose(1,0), np.argwhere(frame_pred_np > 0).squeeze().shape[0]).transpose(1,0)
    nnz_coords += add_vector
    pred_counts = np.repeat(pred_counts, cell_size**2, axis=0)
    pred_counts_colored = [get_color(count) for count in pred_counts]
    binned_pred_img = image.copy()
    if len(pred_counts_colored) > 0: binned_pred_img[nnz_coords[:,0], nnz_coords[:,1]] = pred_counts_colored

    plt.imshow(binned_pred_img)
    plt.close('all')

    predicted_frames.append(binned_pred_img)

last_frame = PilImage.fromarray(predicted_frames[-1])
last_frame.save("./x.png")
