import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument

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


if IN[0] : 
    view_id = IN[1]
    element_id = ElementId(view_id)
    view = doc.GetElement(element_id)

    origins, destinations = IN[0]

    level = view.GenLevel

    TransactionManager.Instance.EnsureInTransaction(doc)

    fillPatterns = FilteredElementCollector(doc).OfClass(FillPatternElement)
    solidPattern = None
    for pattern in fillPatterns:
        if UnwrapElement(pattern).GetFillPattern().IsSolidFill:
            solidPattern = pattern
            break

    if solidPattern : 
        red = Color(255 , 0 , 0)
        green = Color(0 , 255 , 0)

        for origin in origins : 
            origin_bbox = convert_meter_to_unit([*origin[0], *origin[1]])

            start_x , start_y = origin_bbox[0] , origin_bbox[1]

            size_x = origin_bbox[2] - origin_bbox[0]
            size_y = origin_bbox[3] - origin_bbox[1]

            create_colored_floor(size_x , size_y , start_x , start_y , level , doc , red)
        for destination in destinations : 
            destination_bbox = convert_meter_to_unit([*destination[0], *destination[1]])

            start_x , start_y = destination_bbox[0] , destination_bbox[1]

            size_x = destination_bbox[2] - destination_bbox[0]
            size_y = destination_bbox[3] - destination_bbox[1]

            create_colored_floor(size_x , size_y , start_x , start_y , level , doc , green)

        TransactionManager.Instance.TransactionTaskDone()
        OUT = 1
    else : 
        OUT = 0
