import os
import platform
import numpy as np
import matplotlib.pyplot as plt

OPSYS = platform.system()
SEP = '\\' if OPSYS == 'Windows' else '/'
 
def dir_maker(store_folder_path, description_log, config, train_config):
    if os.path.isdir(store_folder_path):
        print('Path already exists!')
        quit()
    
    os.mkdir(store_folder_path)
    with open(os.path.join(store_folder_path, 'description.txt'), 'w') as f:
        f.write(description_log)
        f.write("\n\nCONFIG: {\n")
        for k in config.keys():
            f.write("'{}':'{}'\n".format(k, str(config[k])))
        f.write("}")
        f.write("\n\nTRAIN_CONFIG: {\n")
        for k in config.keys():
            f.write("'{}':'{}'\n".format(k, str(config[k])))
        f.write("}\n\n")
    f.close()


def class_colorization(classes):
    color_map = {
        1: np.array([143, 225, 255]),
        2: np.array([0, 0, 255]),
        3: np.array([255, 0, 255]),
    }
    encoded_colors = np.array([color_map[val] for val in classes], dtype=np.float32) / 255.
    return encoded_colors


def class_visualization(floorplan_image, class_frames):
    """
    assuming all inputs are in torch tensor format
    
    floorplan_image shape: channels x height x width
    class_frames shape: num_frames x height/4 x width/4
    
    with cell size = 4
    """

    floorplan_image = floorplan_image.permute(1, 2, 0).detach().cpu().numpy()
    floorplan_image = (floorplan_image+1)/2. # undo color encoding of the BeitFeatureExtractor
    class_frames = class_frames.permute(1, 2, 0).detach().cpu().numpy()

    cell_size = 4
    cell_template = np.zeros((cell_size**2,2), dtype=np.int32)
    for x in range(cell_size):
        for y in range(cell_size):
            cell_template[cell_size*x + y] = np.array([x, y], dtype=np.int32)
    
    for frame_id in range(class_frames.shape[-1]):
        frame_np = class_frames[:,:,frame_id]
        nnz_coords = np.argwhere(frame_np > 0).squeeze()
        gt_classes = frame_np[nnz_coords[:,0], nnz_coords[:,1]]
        # scale up
        nnz_coords = np.repeat(nnz_coords, cell_size**2, axis=0) * cell_size
        add_vector = np.tile(cell_template.transpose(1,0), np.argwhere(frame_np > 0).squeeze().shape[0]).transpose(1,0)
        nnz_coords += add_vector
        gt_classes = np.repeat(gt_classes, cell_size**2, axis=0)
        gt_classes_colored = class_colorization(gt_classes)
        binned_img = floorplan_image.copy()
        if len(gt_classes_colored) > 0: binned_img[nnz_coords[:,0], nnz_coords[:,1]] = gt_classes_colored
      
        plt.imshow(binned_img)
        plt.close('all')
