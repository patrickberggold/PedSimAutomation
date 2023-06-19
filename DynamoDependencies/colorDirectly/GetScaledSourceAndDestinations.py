#IN[0]: room dict.
#IN[1]: bbox of geometry inside png
#IN[2]: site_x and site_y
#IN[3]: wall thickness in meters

import clr
from System.Drawing import *
from Autodesk.DesignScript.Geometry import *
from RevitServices.Persistence import DocumentManager 
from Autodesk.Revit.DB import *

def extract_lists_with_string(room_dict, type):
    extracted_lists = []
    for key in room_dict:
        if type in key:
            extracted_lists.append(room_dict[key])
    return extracted_lists

def flip_point_y_axis(point, height) :
    return height + 1 - point

def transform_to_image_coordinates(point , site_bbox_image , site_dims_revit , wall_thickness) : 
    transformed_point = []
    for c in range(len(point)) : 
        gradient = (site_bbox_image[c + 2] - site_bbox_image[c]) / site_dims_revit[c] # bbox: xmin,ymin,xmax,ymax
        if c == 0 :
            transformed_point.append(int(point[c] * gradient + site_bbox_image[c] + wall_thickness / 2 * gradient))
        else : 
            transformed_point.append(int(flip_point_y_axis(point[c] * gradient , site_bbox_image[c + 2] - site_bbox_image[c]) + site_bbox_image[c] - wall_thickness / 2 * gradient))

    return transformed_point

def transform_set_of_points(points , site_bbox_image , site_dims_revit , wall_thickness) : 
    transformed_points = []
    for point in points : 
        transformed_points.append(
            transform_to_image_coordinates(point , site_bbox_image , site_dims_revit , wall_thickness)
        )

    return transformed_points
    
if UnwrapElement(IN[4]) : 
    x = 1
        
    dict = IN[0]
    #site_bbox_in_image , image_width , image_height = IN[1]
    #site_dimensions_revit = IN[2][1][:2]
    #wall_thickness = IN[3]
    
    
    origins = extract_lists_with_string(dict , "ORIGIN")
    destinations = extract_lists_with_string(dict , "DESTINATION")
    
    # origins_in_image = [
    #     transform_set_of_points(origin , site_bbox_in_image , site_dimensions_revit , wall_thickness) for origin in origins
    # ]
    # destinations_in_image = [
    #     transform_set_of_points(destination , site_bbox_in_image , site_dimensions_revit , wall_thickness) for destination in destinations
    # ]
    
    #OUT = origins_in_image , destinations_in_image
    OUT = origins, destinations