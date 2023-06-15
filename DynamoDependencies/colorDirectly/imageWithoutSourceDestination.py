# IN[0] : bbox of geometry in image coordinate system, image width , image height
# IN[1] : origin and destination lists from origin and destination prepper script
# IN[2] : path of temp image created in script that runs before this one
# IN[3] : create input image or not (boolean)
# IN[4] : output of prepper script
# IN[5] : padded image width (input param)
# IN[6] : padded image height (input param)

import sys
#sys.path.append(r'D:\Work\TUM_Research\HiWiPatrick\PedSimAutomation\DynamoDependencies\DynamoVEnv\lib\site-packages')

sys.path.append(r'C:\Users\mohab\Documents\TUM\HiWiPatrick\PedSimAutomation\DynamoDependencies\DynamoVEnv\lib\site-packages')

import clr
import System
from System.IO import *
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager 

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference('System.Drawing')
import System.Drawing
from System.Drawing import *
import os
import cv2
import numpy as np
import tempfile

def fix_open_cv_flipped_y(x_min_new, y_min_new, x_max_new, y_max_new):
    return x_min_new , y_max_new , x_max_new , y_min_new

def change_bounding_box_color(image, x_min, y_min, x_max, y_max, color):
    image[y_min:y_max, x_min:x_max] = tuple(color)

    return image

if IN[3] : 
    site_bbox_in_image = IN[0][0]
    origins, destinations = IN[1]
    image_path = IN[2]
    site_dimensions_meters = IN[4][1][:2]
    padded_image_width = int(IN[5])
    padded_image_height = int(IN[6])
    
    image = cv2.imread(image_path)

    origin_color = (0, 0, 255) #bgr
    destination_color = (0, 255, 0)
    
    # for origin in origins:
    #     reshaped_origin = [*origin[0], *origin[1]]
    #     pixel_coordinates = fix_open_cv_flipped_y(*reshaped_origin)
    #     image = change_bounding_box_color(image , *pixel_coordinates, origin_color)
    
    # for destination in destinations:
    #     reshaped_destination = [*destination[0], *destination[1]]
    #     pixel_coordinates = fix_open_cv_flipped_y(*reshaped_destination)
    #     image = change_bounding_box_color(image, *pixel_coordinates, destination_color)

    padded_image = np.zeros((padded_image_height, padded_image_width , 3), dtype=np.uint8)
    padded_image_centers = [
        int(dim / 2) for dim in [padded_image_width , padded_image_height]
    ]

    site_cutout = image[site_bbox_in_image[1] : site_bbox_in_image[3] , site_bbox_in_image[0] : site_bbox_in_image[2]]
    site_dims_in_padded_image = [
        dim * 10 for dim in site_dimensions_meters
    ]

    # using different interpolation order for upsizing and downsizing
    if site_dims_in_padded_image[0] > site_bbox_in_image[2] - site_bbox_in_image[0] and site_dims_in_padded_image[1] > site_bbox_in_image[3] - site_bbox_in_image[1] : 
        scaled_cutout = cv2.resize(site_cutout, tuple(site_dims_in_padded_image), interpolation=cv2.INTER_CUBIC)
    else : 
        scaled_cutout = cv2.resize(site_cutout, tuple(site_dims_in_padded_image), interpolation=cv2.INTER_AREA)

    origin_padded_image = [
        int(padded_image_centers[i] - site_dims_in_padded_image[i] / 2) for i in range(2)
    ]
    padded_image[origin_padded_image[1] : origin_padded_image[1] + site_dims_in_padded_image[1] , origin_padded_image[0] : origin_padded_image[0] + site_dims_in_padded_image[0]] = scaled_cutout
    
    overlayed_image_path = tempfile.mktemp(suffix=".png")
    cv2.imwrite(overlayed_image_path, padded_image)
    
    result = Image.FromFile(overlayed_image_path)
    
    OUT = result