import cv2

def find_corners(image_path):
    floor_plan_no_colors = cv2.imread(image_path)
    image_height , image_width , _ = floor_plan_no_colors.shape

    gray = cv2.cvtColor(floor_plan_no_colors, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = list(contours)
    contours.sort(key=cv2.contourArea , reverse=True)

    if not contours : 
        return None

    # second largest contour is geometry (full image is largest)
    x, y, w, h = cv2.boundingRect(contours[1])
    bbox = [x , y , x + w , y + h]

    return bbox , image_width , image_height

image_path = IN[0]

geometry_corners , image_width , image_height = find_corners(image_path)
OUT = geometry_corners , image_width , image_height
