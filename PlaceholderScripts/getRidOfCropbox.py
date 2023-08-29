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
    
    viewIds = IN[1]
    results = []
    for elementId in viewIds : 
        view = doc.GetElement(elementId)
        
        view.CropBoxActive = False
        view.CropBoxVisible = False

        results.append(1)
    
    TransactionManager.Instance.TransactionTaskDone()
    
    OUT = 1 if all(results) == 1 else 0