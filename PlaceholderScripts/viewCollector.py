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

collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Views).OfClass(ViewPlan)

floor_plan_view_ids = []
floor_plan_view_names = []

for view in collector:
    if "Story Level" in view.Name:
        floor_plan_view_ids.append(view.Id)
        floor_plan_view_names.append(view.Name)

OUT = floor_plan_view_ids