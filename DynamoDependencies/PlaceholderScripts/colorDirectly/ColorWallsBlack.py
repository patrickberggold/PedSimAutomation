#IN[0]: Create Floor plan or not (boolean)

import clr
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument

def OverrideColorPattern(element, color, pattern, view):
    graphicSettings = OverrideGraphicSettings()
    graphicSettings.SetSurfaceForegroundPatternColor(color)
    graphicSettings.SetCutForegroundPatternColor(color)
    graphicSettings.SetSurfaceForegroundPatternId(UnwrapElement(pattern).Id)
    graphicSettings.SetCutForegroundPatternId(UnwrapElement(pattern).Id)
    UnwrapElement(view).SetElementOverrides(element.Id, graphicSettings)

if UnwrapElement(IN[0]) : 
    viewId = IN[1]
    elementId = ElementId(viewId)
    view = doc.GetElement(elementId)

    black = Color(0, 0, 0)
    
    walls = FilteredElementCollector(doc).OfClass(Wall)
    TransactionManager.Instance.EnsureInTransaction(doc)
    
    fillPatterns = FilteredElementCollector(doc).OfClass(FillPatternElement)
    solidPattern = None
    for pattern in fillPatterns:
        if UnwrapElement(pattern).GetFillPattern().IsSolidFill:
            solidPattern = pattern
            break
    
    if solidPattern : 
        for wall in walls:
            OverrideColorPattern(wall, black, solidPattern, view)
    
        TransactionManager.Instance.TransactionTaskDone()
        OUT = 1
    else : 
        OUT = 0
