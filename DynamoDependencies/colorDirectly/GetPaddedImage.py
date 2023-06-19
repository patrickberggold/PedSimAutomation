# IN[0] Element id of view

import clr
import System
from System.IO import *
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager 

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *
import tempfile

if UnwrapElement(IN[1]) : 
    doc = DocumentManager.Instance.CurrentDBDocument
    
    viewId = IN[0]
    elementId = ElementId(viewId)
    view = doc.GetElement(elementId)
    
    screenshot_of_view_path = tempfile.mktemp(suffix=".png")
    
    options = ImageExportOptions()
    options.ExportRange = ExportRange.CurrentView
    options.ViewName = view.Name
    options.FilePath = screenshot_of_view_path
    options.ZoomType = ZoomFitType.Zoom
    options.PixelSize = 2048
    
    doc.ExportImage(options)
    
    saved_image_path = f"{screenshot_of_view_path[:-3]}jpg" # Saving as JPG format (unusual behavior)
    
    OUT = saved_image_path