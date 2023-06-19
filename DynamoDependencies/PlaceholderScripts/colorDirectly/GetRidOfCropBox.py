#IN[1]: view element id

import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

if UnwrapElement(IN[0]) : 
    doc = DocumentManager.Instance.CurrentDBDocument
    TransactionManager.Instance.EnsureInTransaction(doc)
    
    viewId = IN[1]
    elementId = ElementId(viewId)
    view = doc.GetElement(elementId)
    
    view.CropBoxActive = False
    view.CropBoxVisible = False
    
    TransactionManager.Instance.TransactionTaskDone()
    
    OUT = 1