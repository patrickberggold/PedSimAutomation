# IN[0] : bbox of geometry in image coordinate system, image width , image height
# IN[1] : origin and destination lists from origin and destination prepper script
# IN[2] : path of temp image created in script that runs before this one

import sys
sys.path.append(r'D:\Work\TUM_Research\HiWiPatrick\PedSimAutomation\DynamoDependencies\DynamoVEnv\lib\site-packages')

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

image_path = IN[2]
origins, destinations = IN[1]

image = cv2.imread(image_path)
image_copy = np.copy(image)

origin_color = (0, 0, 255) #bgr
destination_color = (0, 255, 0)

for origin in origins:
    reshaped_origin = [*origin[0], *origin[1]]
    pixel_coordinates = fix_open_cv_flipped_y(*reshaped_origin)
    image = change_bounding_box_color(image , *pixel_coordinates, origin_color)

for destination in destinations:
    reshaped_destination = [*destination[0], *destination[1]]
    pixel_coordinates = fix_open_cv_flipped_y(*reshaped_destination)
    image = change_bounding_box_color(image, *pixel_coordinates, destination_color)

overlayed_image_path = tempfile.mktemp(suffix=".png")
cv2.imwrite(overlayed_image_path, image)

result = Image.FromFile(overlayed_image_path)

OUT = result