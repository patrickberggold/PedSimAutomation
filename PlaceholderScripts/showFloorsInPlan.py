import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

if UnwrapElement(IN[0]):
    doc = DocumentManager.Instance.CurrentDBDocument
    
    floorCategoryId = BuiltInCategory.OST_Floors
    floorCategory = Category.GetCategory(doc, floorCategoryId)

    viewIds = IN[1]
    
    TransactionManager.Instance.EnsureInTransaction(doc)

    for elementId in viewIds : 
        view = doc.GetElement(elementId)    
        view.SetCategoryHidden(floorCategory.Id, False)

    TransactionManager.Instance.TransactionTaskDone()
    
    OUT = 1