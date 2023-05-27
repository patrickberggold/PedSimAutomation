#IN[0]: view element id

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
cropBox = view.CropBox

minVertex = cropBox.Min
maxVertex = cropBox.Max

x_bottom_left = minVertex.X
y_bottom_left = minVertex.Y
x_top_right = maxVertex.X
y_top_right = maxVertex.Y

OUT = x_bottom_left, y_bottom_left, x_top_right, y_top_right, x_top_right - x_bottom_left, y_top_right - y_bottom_left