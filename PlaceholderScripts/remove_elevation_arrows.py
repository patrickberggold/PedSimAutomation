import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

from System.Collections.Generic import List

doc = DocumentManager.Instance.CurrentDBDocument
TransactionManager.Instance.EnsureInTransaction(doc)

if UnwrapElement(IN[0]) : 
    results = []

    for viewId in viewIds:
        elementId = ElementId(viewId)
        view = doc.GetElement(elementId)

        elevationArrows = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Elev).ToElementIds()
        viewers = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Viewers).ToElementIds()

        if elevationArrows and viewers:
            view.HideElements(List[ElementId](elevationArrows))
            view.HideElements(List[ElementId](viewers))

            TransactionManager.Instance.TransactionTaskDone()

            results.append(1)  
        else:
            results.append(0) 

    OUT = 1 if all(results) == 1 else 0
