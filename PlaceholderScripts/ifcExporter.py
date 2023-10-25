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

import os


should_export_ifc = IN[1]
ifc_file_export_dir = IN[3]
ifc_mapping_file_path = IN[2]

if IN[0] != None and should_export_ifc : 
    file_name = "geometry_as_ifc"
    doc = DocumentManager.Instance.CurrentDBDocument
    # TransactionManager.Instance.EnsureInTransaction(doc)

    options=IFCExportOptions()
    options.FileVersion = IFCVersion.IFC2x3CV2
    options.AddOption("ExportUserDefinedPsets","true")
    options.AddOption("ExportInternalRevitPropertySets","false")
    options.AddOption("ExportBaseQuantitiesPsets","false")
    options.AddOption("ExportExportIFCCommonPropertySets","false")

    if os.path.exists(ifc_mapping_file_path) : 
        options.AddOption("ExportUserDefinedPsetsFileName",str(ifc_mapping_file_path))

    try : 
        export_return = doc.Export(ifc_file_export_dir , file_name , options)

        OUT = "Exported IFC file successfully."
    except Exception as e :
        OUT = f"Unexpected error: {str(e)}"

    



