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

floor_list = IN[0][0]
all_levels = IN[0][1]
site_x = IN[1][1][0]
site_y = IN[1][1][1]
geometry_picker = IN[2]

create_edge_geometry = UnwrapElement(IN[3])
create_cross_geometry = UnwrapElement(IN[4])
create_e2e_geometry = UnwrapElement(IN[5])

convert_meter_to_unit = IN[6][0]

create_slab_geometry = IN[6][3]
create_staircase = IN[6][6]
create_one_stair = IN[6][4]

default_floor_type = UnwrapElement(IN[7])

if any(geometry_picker) : 
    room_dict = {}

    if geometry_picker[0] : 
        creation_function = create_cross_geometry

        start_x_even = convert_meter_to_unit(site_x * 0.97)
        end_x_even = convert_meter_to_unit(0.8 * site_x)

        start_x_odd = convert_meter_to_unit(0.03 * site_x)
        end_x_odd = convert_meter_to_unit(0.2 * site_x)

        start_y_even = convert_meter_to_unit(site_y / 2. - site_y / 40.)
        end_y_even = convert_meter_to_unit(site_y / 2. + site_y / 40.)

        start_y_odd = convert_meter_to_unit(site_y / 2. - site_y / 40.)
        end_y_odd = convert_meter_to_unit(site_y / 2. + site_y / 40.)

        in_x_even = True
        in_x_odd = True

    elif geometry_picker[1] : 
        creation_function = create_e2e_geometry

        start_x_even = convert_meter_to_unit(site_x * 0.97)
        end_x_even = convert_meter_to_unit(0.91 * site_x)

        start_x_odd = convert_meter_to_unit(0.03 * site_x)
        end_x_odd = convert_meter_to_unit(0.09 * site_x)

        start_y_even = convert_meter_to_unit(site_y * 0.96)
        end_y_even = convert_meter_to_unit(3. * site_y / 4.)

        start_y_odd = convert_meter_to_unit(site_y * 0.04)
        end_y_odd = convert_meter_to_unit(site_y / 4.)

        in_x_even = False
        in_x_odd = False

    else : 
        creation_function = create_edge_geometry

        start_x_even = convert_meter_to_unit(site_x * 0.8)
        end_x_even = convert_meter_to_unit(0.97 * site_x)

        start_x_odd = convert_meter_to_unit(0.046 * site_x)
        end_x_odd = convert_meter_to_unit(0.096 * site_x)

        start_y_even = convert_meter_to_unit(site_y * 0.88)
        end_y_even = convert_meter_to_unit(site_y * 0.94)

        start_y_odd = convert_meter_to_unit(0.03 * site_y)
        end_y_odd = convert_meter_to_unit(0.2 * site_y)

        in_x_even = True
        in_x_odd = False

    for i in range(len(all_levels) - 1) : 
        room_dict[f"level_{i}"] = creation_function(UnwrapElement(all_levels[i]) , UnwrapElement(all_levels[i + 1]))

        stair_thickness = (UnwrapElement(all_levels[i + 1]).Elevation - UnwrapElement(all_levels[i]).Elevation) / 15.
        
        if i < (len(all_levels) - 2) :
            doc = DocumentManager.Instance.CurrentDBDocument
            TransactionManager.Instance.EnsureInTransaction(doc)

            if i % 2 == 0 : 
                start_x = start_x_even
                end_x = end_x_even
                start_y = start_y_even
                end_y = end_y_even
                in_x = in_x_even
            else : 
                start_x = start_x_odd
                end_x = end_x_odd
                start_y = start_y_odd
                end_y = end_y_odd
                in_x = in_x_odd

            stairs = create_staircase(
                start_x = start_x , 
                start_y = start_y , 
                start_level = UnwrapElement(all_levels[i]) , 
                end_x = end_x , 
                end_y = end_y , 
                end_level = UnwrapElement(all_levels[i + 1]) , 
                thickness = stair_thickness , 
                floor_type = default_floor_type , 
                inXDirection = in_x
            )

            floor_cutting_curve = create_slab_geometry(start_x , end_x , start_y , end_y , 0.)
            floor_cutting = doc.Create.NewOpening(doc.GetElement(ElementId(floor_list[i + 1].Id)), floor_cutting_curve, False)

            TransactionManager.Instance.TransactionTaskDone() 

    OUT = room_dict