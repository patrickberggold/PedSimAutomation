def transform_to_image_coordinates(point , site_bbox_image , site_dims_revit) : 
    transformed_point = []
    for c in range(len(point)) : 
        gradient = (site_bbox_image[c + 2] - site_bbox_image[c]) / site_dims_revit[c] /  # bbox: xmin,ymin,xmax,ymax
        transformed_point.append(point[c] * gradient + site_bbox_image[c])

    return transformed_point

def transform_set_of_points(points , site_bbox_image , site_dims_revit) : 
    transformed_points = []
    for point in points : 
        transformed_points.append(
            transform_to_image_coordinates(point , site_bbox_image , site_dims_revit)
        )

    return transformed_points