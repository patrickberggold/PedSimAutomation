import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

if UnwrapElement(IN[0]):
    doc = DocumentManager.Instance.CurrentDBDocument
    
    
    floorCategoryId = BuiltInCategory.OST_Floors
    
    
    activeView = doc.ActiveView
    
    
    floorCategory = Category.GetCategory(doc, floorCategoryId)
    
    
    TransactionManager.Instance.EnsureInTransaction(doc)
    activeView.SetCategoryHidden(floorCategory.Id, False)
    TransactionManager.Instance.TransactionTaskDone()
    
    OUT = 1