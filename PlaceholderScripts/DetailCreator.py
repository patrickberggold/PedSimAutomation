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

geometry_picker = IN[2]

if any(geometry_picker) : 
    floor_list = IN[0][0]
    all_levels = IN[0][1]
    site_x = IN[1][1][0]
    site_y = IN[1][1][1]
    
    create_edge_geometry = UnwrapElement(IN[3])
    create_cross_geometry = UnwrapElement(IN[4])
    create_e2e_geometry = UnwrapElement(IN[5])
    create_new_cross_geometry = UnwrapElement(IN[8])
    create_new_edge_geometry = UnwrapElement(IN[9])
    create_new_asym_edge_geometry = UnwrapElement(IN[10])
    
    convert_meter_to_unit = IN[6][0]
    
    create_slab_geometry = IN[6][3]
    create_staircase_variant_1 = IN[6][6]
    create_staircase_variant_2 = IN[6][7]
    create_staircase_variant_3 = IN[6][8]
    create_one_stair = IN[6][4]
    
    default_floor_type = UnwrapElement(IN[7])

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

        start_y_single = convert_meter_to_unit(site_y * 0.01)
        start_x_single = convert_meter_to_unit(site_x * 0.01)
        end_y_single = convert_meter_to_unit(site_y * 0.01)
        end_x_single = convert_meter_to_unit(site_x * 0.01)
        in_x_single = True

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

        start_y_single = convert_meter_to_unit(site_y * 0.01)
        start_x_single = convert_meter_to_unit(site_x * 0.01)
        end_y_single = convert_meter_to_unit(site_y * 0.01)
        end_x_single = convert_meter_to_unit(site_x * 0.01)
        in_x_single = True

    elif geometry_picker[2] : 
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

        start_y_single = convert_meter_to_unit(site_y * 0.01)
        start_x_single = convert_meter_to_unit(site_x * 0.01)
        end_y_single = convert_meter_to_unit(site_y * 0.01)
        end_x_single = convert_meter_to_unit(site_x * 0.01)
        in_x_single = True

    elif geometry_picker[3] : 
        creation_function = create_new_cross_geometry

        start_x_odd = convert_meter_to_unit(site_x * 0.98)
        end_x_odd = convert_meter_to_unit(0.92 * site_x)
        start_y_odd = convert_meter_to_unit(site_y * 0.275)
        end_y_odd = convert_meter_to_unit(site_y * 0.725)

        start_y_single = convert_meter_to_unit(site_y * 0.85)
        start_x_single = convert_meter_to_unit(site_x * 0.01)
        end_y_single = convert_meter_to_unit(site_y * 0.45)
        end_x_single = convert_meter_to_unit(site_x * 0.05)
        in_x_single = False


        in_x_even = True
        in_x_odd = False
    elif geometry_picker[4] : 
        creation_function = create_new_edge_geometry

        start_x_even = convert_meter_to_unit(site_x * 0.99)
        end_x_even = convert_meter_to_unit(0.9 * site_x)

        start_x_odd = convert_meter_to_unit(0.01 * site_x)
        end_x_odd = convert_meter_to_unit(0.19 * site_x)

        start_y_even = convert_meter_to_unit(site_y * 0.90)
        end_y_even = convert_meter_to_unit(site_y * 0.99)

        start_y_odd = convert_meter_to_unit(site_y * 0.01)
        end_y_odd = convert_meter_to_unit(site_y * 0.1)

        start_y_single = convert_meter_to_unit(site_y * 0.945)
        start_x_single = convert_meter_to_unit(site_x * 0.02)
        end_y_single = convert_meter_to_unit(site_y * 0.985)
        end_x_single = convert_meter_to_unit(site_x * 0.1)

        in_x_even = True
        in_x_odd = False
        in_x_single = True

    else : 
        creation_function = create_new_asym_edge_geometry

        start_x_even = convert_meter_to_unit(site_x * 0.99)
        end_x_even = convert_meter_to_unit(0.9 * site_x)

        start_x_odd = convert_meter_to_unit(0.01 * site_x)
        end_x_odd = convert_meter_to_unit(0.19 * site_x)

        start_y_even = convert_meter_to_unit(site_y * 0.90)
        end_y_even = convert_meter_to_unit(site_y * 0.99)

        start_y_odd = convert_meter_to_unit(site_y * 0.52)
        end_y_odd = convert_meter_to_unit(site_y * 0.61)

        start_y_single = convert_meter_to_unit(site_y * 0.945)
        start_x_single = convert_meter_to_unit(site_x * 0.02)
        end_y_single = convert_meter_to_unit(site_y * 0.985)
        end_x_single = convert_meter_to_unit(site_x * 0.1)

        in_x_even = True
        in_x_odd = False
        in_x_single = True

    for i in range(len(all_levels) - 1) : 
        room_dict[f"level_{i}"] = creation_function(UnwrapElement(all_levels[i]) , UnwrapElement(all_levels[i + 1]))

        stair_thickness = (UnwrapElement(all_levels[i + 1]).Elevation - UnwrapElement(all_levels[i]).Elevation) / 15.
        
        if i < (len(all_levels) - 2) :
            doc = DocumentManager.Instance.CurrentDBDocument
            TransactionManager.Instance.EnsureInTransaction(doc)

            if not geometry_picker[3] : 
                stairs_even = create_staircase_variant_2(
                    doc , end_x_even , end_y_even , UnwrapElement(all_levels[i]) , start_x_even , start_y_even , UnwrapElement(all_levels[i + 1]) , stair_thickness , default_floor_type , in_x_even
                )
                
            stairs_odd = create_staircase_variant_3(
                doc , end_x_odd , end_y_odd , UnwrapElement(all_levels[i]) , start_x_odd , start_y_odd , UnwrapElement(all_levels[i + 1]) , stair_thickness , default_floor_type , in_x_odd
            )

            stairs = create_staircase_variant_1(
                start_x = start_x_single , 
                start_y = start_y_single , 
                start_level = UnwrapElement(all_levels[i]) , 
                end_x = end_x_single , 
                end_y = end_y_single , 
                end_level = UnwrapElement(all_levels[i + 1]) , 
                thickness = stair_thickness , 
                floor_type = default_floor_type , 
                inXDirection = in_x_single
            )

            if not geometry_picker[3] : 
                floor_cutting_curve_even = create_slab_geometry(start_x_even , end_x_even , start_y_even , end_y_even , 0.)
                floor_cutting_even = doc.Create.NewOpening(doc.GetElement(ElementId(floor_list[i + 1].Id)), floor_cutting_curve_even, False)

            floor_cutting_curve_odd = create_slab_geometry(start_x_odd , end_x_odd , start_y_odd , end_y_odd , 0.)
            floor_cutting_odd = doc.Create.NewOpening(doc.GetElement(ElementId(floor_list[i + 1].Id)), floor_cutting_curve_odd, False)

            floor_cutting_curve_single = create_slab_geometry(start_x_single , end_x_single , start_y_single , end_y_single , 0.)
            floor_cutting_single = doc.Create.NewOpening(doc.GetElement(ElementId(floor_list[i + 1].Id)), floor_cutting_curve_single, False)

            TransactionManager.Instance.TransactionTaskDone() 

            if i == 0 :
                TransactionManager.Instance.EnsureInTransaction(doc)
                view = doc.ActiveView

                fillPatterns = FilteredElementCollector(doc).OfClass(FillPatternElement)
                solidPattern = None
                for pattern in fillPatterns:
                    if UnwrapElement(pattern).GetFillPattern().IsSolidFill:
                        solidPattern = pattern
                        break

                def slab_geometry_by_level(x, y, level, delta_z , start_x , start_y):
                    zz = level.Elevation + delta_z
                    xx = x + start_x
                    yy = y + start_y
                    line_1 = Line.CreateBound(XYZ(start_x, start_y, zz), XYZ(xx, start_y, zz))
                    line_2 = Line.CreateBound(XYZ(xx, start_y, zz), XYZ(xx, yy, zz))
                    line_3 = Line.CreateBound(XYZ(xx, yy, zz), XYZ(start_x, yy, zz))
                    line_4 = Line.CreateBound(XYZ(start_x, yy, zz), XYZ(start_x, start_y, zz))

                    slab_geometry = CurveArray()
                    slab_geometry.Append(line_1)
                    slab_geometry.Append(line_2)
                    slab_geometry.Append(line_3)
                    slab_geometry.Append(line_4)
                    return slab_geometry

                def override_color_pattern(element, color, pattern, view):
                    graphicSettings = OverrideGraphicSettings()
                    graphicSettings.SetSurfaceForegroundPatternColor(color)
                    graphicSettings.SetCutForegroundPatternColor(color)
                    graphicSettings.SetSurfaceForegroundPatternId(UnwrapElement(pattern).Id)
                    graphicSettings.SetCutForegroundPatternId(UnwrapElement(pattern).Id)
                    graphicSettings.SetSurfaceBackgroundPatternId(UnwrapElement(pattern).Id)
                    graphicSettings.SetCutBackgroundPatternId(UnwrapElement(pattern).Id)
                    graphicSettings.SetProjectionLineColor(color)
                    UnwrapElement(view).SetElementOverrides(element.Id, graphicSettings)

                def convert_meter_to_unit(pre_value):
                    tempo_list = []
                    tempo_value = 0
                    if isinstance(pre_value, list):
                        len_list = len(pre_value)
                        for ii in range(len_list):
                            tempo_list.append (float(UnitUtils.ConvertToInternalUnits(pre_value[ii], UnitTypeId.Meters)))
                        pre_value = tempo_list
                    else:
                        tempo_value = float(UnitUtils.ConvertToInternalUnits(pre_value, UnitTypeId.Meters))
                        pre_value = tempo_value
                    return pre_value

                def create_colored_floor(length , width , start_x , start_y , level , doc , color) : 
                    floor_geometry = slab_geometry_by_level(length, width, level, 1. , start_x , start_y)

                    floor = doc.Create.NewFloor(floor_geometry, True)

                    override_color_pattern(floor, color, solidPattern, view)
                origins = [
                    value for _ , value in room_dict[f"level_{i}"].items()
                ]

                x = 0
                y = 255

                for origin in origins : 
                    origin_bbox = convert_meter_to_unit([*origin[0], *origin[1]])

                    start_x , start_y = origin_bbox[0] , origin_bbox[1]

                    size_x = origin_bbox[2] - origin_bbox[0]
                    size_y = origin_bbox[3] - origin_bbox[1]

                    create_colored_floor(size_x , size_y , start_x , start_y , all_levels[i] , doc , Color(x , y , 0))
                    z = x
                    x = y
                    y = z

    OUT = origins