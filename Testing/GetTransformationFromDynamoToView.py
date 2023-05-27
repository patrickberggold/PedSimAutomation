#IN[0]: view element id
#IN[1]: Output of Input prep. script

import sys
import clr
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

doc = DocumentManager.Instance.CurrentDBDocument

viewId = IN[0]
elementId = ElementId(viewId)
view = doc.GetElement(elementId)

walls = FilteredElementCollector(doc).OfClass(Wall).ToElements()

non_unique_vertices = []
for wall in walls:
    wall_location = wall.Location
    if isinstance(wall_location, LocationCurve):
        wall_location_curve = wall_location.Curve
        curve_start_point = wall_location_curve.GetEndPoint(0)
        curve_end_point = wall_location_curve.GetEndPoint(1)

        non_unique_vertices.append(curve_start_point)
        non_unique_vertices.append(curve_end_point)

geometry_vertices = list(set(non_unique_vertices))

total_x_in_dynamo = IN[1][1][0]
total_y_in_dynamo = IN[1][1][1]

if geometry_vertices:
    min_vertex = min(geometry_vertices, key=lambda vertex: (vertex.X, vertex.Y, vertex.Z)) #* bottom left of outer rectangle
    max_vertex = max(geometry_vertices, key=lambda vertex: (vertex.X, vertex.Y, vertex.Z)) #* top right of outer rectangle
    
    x_min , y_min = min_vertex.X , min_vertex.Y
    x_max , y_max = max_vertex.X , max_vertex.Y

    total_x_in_view = x_max - x_min
    total_y_in_view = y_max - y_min
    
    OUT = total_x_in_view / total_x_in_dynamo , total_y_in_view / total_y_in_dynamo
else : 
    OUT = None