import clr

from System.Collections.Generic import *

clr.AddReference("RevitNodes")
import Revit

clr.ImportExtensions(Revit.Elements)
clr.ImportExtensions(Revit.GeometryConversion)

clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager 
from RevitServices.Transactions import TransactionManager 

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

clr.AddReference('ProtoGeometry')
import Autodesk 
from Autodesk.DesignScript.Geometry import *
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import *


def create_slab_geometry(x_min , x_max , y_min , y_max , z) : 

    bottom_left_point = XYZ(x_min , y_min , z)
    bottom_right_point = XYZ(x_max , y_min , z)
    top_right_point = XYZ(x_max , y_max , z)
    top_left_point = XYZ(x_min , y_max , z)

    bottom_line = Autodesk.Revit.DB.Line.CreateBound(bottom_left_point , bottom_right_point)
    right_vertical_line = Autodesk.Revit.DB.Line.CreateBound(bottom_right_point , top_right_point)
    top_line = Autodesk.Revit.DB.Line.CreateBound(top_right_point , top_left_point)
    left_vertical_line = Autodesk.Revit.DB.Line.CreateBound(top_left_point , bottom_left_point)

    slab_geometry = CurveArray()
    slab_geometry.Append(bottom_line)
    slab_geometry.Append(right_vertical_line)
    slab_geometry.Append(top_line)
    slab_geometry.Append(left_vertical_line)

    return slab_geometry

doc = DocumentManager.Instance.CurrentDBDocument
# TransactionManager.Instance.EnsureInTransaction(doc)

# room_dict = IN[0][0]
floor_list = IN[0][1]
allLevels = IN[0][2]
site_x , site_y = IN[0][3:]

create_edge_geometry = UnwrapElement(IN[1])

if 1:
    
    
    # floor_cutting_curve = create_slab_geometry(site_x / 8. , site_x / 2. , site_y / 4. , site_y / 2. , 0.)
    # floor_cutting = doc.Create.NewOpening(doc.GetElement(ElementId(floor_list[2].Id)), floor_cutting_curve, False)
    # floor_cutting_2 = doc.Create.NewOpening(doc.GetElement(ElementId(floor_list[1].Id)), floor_cutting_curve, False)

    room_dict = {}

    for i in range(len(allLevels) - 1) : 
        room_dict[f"level_{i}"] = create_edge_geometry(UnwrapElement(allLevels[i]) , UnwrapElement(allLevels[i + 1]))
    

    # TransactionManager.Instance.TransactionTaskDone()

    OUT = room_dict
