import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument

def slab_geometry_by_level(x, y, level, delta_z , start_x , start_y):
    zz = level.Elevation + delta_z
    xx = x
    yy = y
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

def OverrideColorPattern(element, color, pattern, view):
    graphicSettings = OverrideGraphicSettings()
    graphicSettings.SetSurfaceForegroundPatternColor(color)
    graphicSettings.SetCutForegroundPatternColor(color)
    graphicSettings.SetSurfaceForegroundPatternId(UnwrapElement(pattern).Id)
    graphicSettings.SetCutForegroundPatternId(UnwrapElement(pattern).Id)
    graphicSettings.SetSurfaceBackgroundPatternId(UnwrapElement(pattern).Id)
    graphicSettings.SetCutBackgroundPatternId(UnwrapElement(pattern).Id)
    graphicSettings.SetProjectionLineColor(color)
    UnwrapElement(view).SetElementOverrides(element.Id, graphicSettings)

if 0 : 
    TransactionManager.Instance.EnsureInTransaction(doc)

    length = 100.
    width = 70.
    start_x = 20.
    start_y = 20.

    level = doc.ActiveView.GenLevel

    floor_geometry = slab_geometry_by_level(length, width, level, 1. , start_x , start_y)

    floor = doc.Create.NewFloor(floor_geometry, True)

    red = Color(255 , 0 , 0) 
    fillPatterns = FilteredElementCollector(doc).OfClass(FillPatternElement)
    solidPattern = None
    for pattern in fillPatterns:
        if UnwrapElement(pattern).GetFillPattern().IsSolidFill:
            solidPattern = pattern
            break

    view = doc.ActiveView

    if solidPattern : 
        OverrideColorPattern(floor, red, solidPattern, view)

        TransactionManager.Instance.TransactionTaskDone()
        OUT = 0
    else : 
        OUT = 1