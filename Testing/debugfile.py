def transform_coordinates(x0_original, y0_original, x1_original, y1_original, x_min_new, y_min_new, x_max_new, y_max_new):
    width, height = 984 , 713

    scale_x = width / (x1_original - x0_original)
    scale_y = height / (y1_original - y0_original)

    pixel_xmin = int((x_min_new) * scale_x)
    pixel_ymin = int(height - (y_max_new) * scale_y)
    pixel_xmax = int((x_max_new) * scale_x)
    pixel_ymax = int(height - (y_min_new) * scale_y)

    return pixel_xmin, pixel_ymin, pixel_xmax, pixel_ymax

x_min , x_max , y_min , y_max = transform_coordinates(-100, -100 , 100 , 100, 105, 220, 171, 303)

x = 0