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


doc = DocumentManager.Instance.CurrentDBDocument

floor_list = IN[0][0]
all_levels = IN[0][1]
site_x = IN[1][1][0]
site_y = IN[1][1][1]
geometry_picker = IN[2]

create_edge_geometry = UnwrapElement(IN[3])
create_cross_geometry = UnwrapElement(IN[4])
create_e2e_geometry = UnwrapElement(IN[5])
creation_functions = [
    create_cross_geometry , create_e2e_geometry , create_edge_geometry
]

create_slab_geometry = IN[6][3]
create_staircase = IN[6][6]
create_one_stair = IN[6][4]

default_floor_type = UnwrapElement(IN[7])

if any(geometry_picker) : 
    room_dict = {}
    for i in range(len(all_levels) - 1) : 
        room_dict[f"level_{i}"] = creation_functions[geometry_picker.index(True)](UnwrapElement(all_levels[i]) , UnwrapElement(all_levels[i + 1]))

        stair_thickness = (UnwrapElement(all_levels[i + 1]).Elevation - UnwrapElement(all_levels[i]).Elevation) / 10.
        start_x = site_x / 8.
        end_x = site_x / 2.
        start_y = site_y / 4.
        end_y = site_y / 2.

        stairs = create_staircase(
            start_x = site_x / 8. , 
            start_y = site_y / 4. , 
            start_level = all_levels[i] , 
            end_x = site_x / 2. , 
            end_y = site_y / 2. , 
            end_level = all_levels[i + 1] , 
            thickness = stair_thickness , 
            floor_type = default_floor_type , 
            inXDirection = False
        )

        floor_cutting_curve = create_slab_geometry(start_x , end_x , start_y , end_y , 0.)
        floor_cutting = doc.Create.NewOpening(doc.GetElement(ElementId(floor_list[2].Id)), floor_cutting_curve, False)

    OUT = room_dict

# if 1:
    
    
#     # floor_cutting_curve = create_slab_geometry(site_x / 8. , site_x / 2. , site_y / 4. , site_y / 2. , 0.)
#     # floor_cutting = doc.Create.NewOpening(doc.GetElement(ElementId(floor_list[2].Id)), floor_cutting_curve, False)
#     # floor_cutting_2 = doc.Create.NewOpening(doc.GetElement(ElementId(floor_list[1].Id)), floor_cutting_curve, False)

#     room_dict = {}

#     for i in range(len(all_levels) - 1) : 
#         #room_dict[f"level_{i}"] = create_edge_geometry(UnwrapElement(all_levels[i]) , UnwrapElement(all_levels[i + 1]))
#         # room_dict[f"level_{i}"] = create_cross_geometry(UnwrapElement(all_levels[i]) , UnwrapElement(all_levels[i + 1]))
#         room_dict[f"level_{i}"] = create_e2e_geometry(UnwrapElement(all_levels[i]) , UnwrapElement(all_levels[i + 1]))
    

#     # TransactionManager.Instance.TransactionTaskDone()

#     OUT = room_dict
