# IN[0] Element id of view

import clr
import System
import sys
from System.IO import *
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager 

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *
import tempfile

if UnwrapElement(IN[0]) and IN[1] : 
    package_path = fr"{IN[1]}\lib\site-packages"
    sys.path.append(package_path)
    import cv2
    import numpy as np

    image_path = UnwrapElement(IN[0])
    image = cv2.imread(image_path)
    image_height , image_width , _ = image.shape

    padded_image_width = int(IN[2])
    padded_image_height = int(IN[3])

    site_x = 25
    site_y = 20
    new_image_dimensions = [site_x * 10 , site_y * 10]
    
    padded_image = np.zeros((padded_image_height, padded_image_width , 3), dtype=np.uint8)
    padded_image_centers = [
        int(dim / 2) for dim in [padded_image_width , padded_image_height]
    ]

    # using different interpolation order for upsizing and downsizing
    if site_x * 10 > image_width and site_y * 10 > image_height : 
        scaled_image = cv2.resize(image, tuple(new_image_dimensions), interpolation=cv2.INTER_CUBIC)
    else : 
        scaled_image = cv2.resize(image, tuple(new_image_dimensions), interpolation=cv2.INTER_AREA)

    origin_in_padded_image = [
        int(padded_image_centers[i] - new_image_dimensions[i] / 2) for i in range(2)
    ]

    padded_image[
        origin_in_padded_image[1] : origin_in_padded_image[1] + new_image_dimensions[1] , origin_in_padded_image[0] : origin_in_padded_image[0] + new_image_dimensions[0]
    ] = scaled_image

    padded_image_path = tempfile.mktemp(suffix=".png")
    cv2.imwrite(padded_image_path , padded_image)

    OUT = padded_image_path
