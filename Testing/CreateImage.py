# IN[0] : path of temp image created in script that runs before this one
# IN[1] : min and max in both x and y in view coordinate system in revit units
# IN[2] : origin and destination lists from origin and destination prepper script

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
import tempfile
from PIL import Image as im

def transform_coordinates(image, x0_original, y0_original, x1_original, y1_original, x_min_new, y_min_new, x_max_new, y_max_new):
    width, height = image.size

    scale_x = width / (x1_original - x0_original)
    scale_y = height / (y1_original - y0_original)

    pixel_xmin = int((x_min_new - x0_original) * scale_x)
    pixel_ymin = int(height - (y_max_new - y0_original) * scale_y)
    pixel_xmax = int((x_max_new - x0_original) * scale_x)
    pixel_ymax = int(height - (y_min_new - y0_original) * scale_y)

    return pixel_xmin, pixel_ymin, pixel_xmax, pixel_ymax

def change_bounding_box_color(image, pixels, x_min, y_min, x_max, y_max, color):
    width, height = image.size

    rgb_color = tuple(color)

    x_min = max(0, min(x_min, width - 1))
    y_min = max(0, min(y_min, height - 1))
    x_max = max(0, min(x_max, width - 1))
    y_max = max(0, min(y_max, height - 1))

    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            pixels[x, y] = rgb_color

    return image, pixels

image_path = IN[0]
view_dims = IN[1][:4]
origins , destinations = IN[2]

image = im.open(image_path)
pixels = image.load()

origin_color = (255, 0, 0)
destination_color = (0, 255, 0)

for origin in origins : 
    reshaped_origin = [*origin[0] , *origin[1]]
    pixel_coordinates = transform_coordinates(image , *view_dims , *reshaped_origin)
    image , pixels = change_bounding_box_color(image , pixels , *pixel_coordinates , origin_color)

for destination in destinations : 
    reshaped_destination = [*destination[0] , *destination[1]]
    pixel_coordinates = transform_coordinates(image , *view_dims , *reshaped_destination)
    image , pixels = change_bounding_box_color(image , pixels , *pixel_coordinates , destination_color)

overlayed_image_path = tempfile.mktemp(suffix=".png")
image.save(overlayed_image_path)

OUT = overlayed_image_path

result = Image.FromFile(overlayed_image_path)

OUT = result