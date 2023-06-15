import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument

def slab_geometry_by_level(x, y, level, delta_z):
    zz = level.Elevation + delta_z
    xx = x
    yy = y
    line_1 = Line.CreateBound(XYZ(0, 0, zz), XYZ(xx, 0, zz))
    line_2 = Line.CreateBound(XYZ(xx, 0, zz), XYZ(xx, yy, zz))
    line_3 = Line.CreateBound(XYZ(xx, yy, zz), XYZ(0, yy, zz))
    line_4 = Line.CreateBound(XYZ(0, yy, zz), XYZ(0, 0, zz))

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
    UnwrapElement(view).SetElementOverrides(element.Id, graphicSettings)

# Start a transaction
TransactionManager.Instance.EnsureInTransaction(doc)

# Define floor dimensions
length = 5.0
width = 5.0

# Get the level to place the floor on
level = doc.ActiveView.GenLevel

# Create floor geometry
floor_geometry = slab_geometry_by_level(length, width, level, 1.)

# Create a floor
floor = doc.Create.NewFloor(floor_geometry, True)

# Set the floor color
red = Color(255, 0, 0)  # Solid red color
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