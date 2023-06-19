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

clr.AddReference('System.Drawing')
import System.Drawing
from System.Drawing import *

if IN[0] : 
    result = Image.FromFile(IN[0][0])
    
    OUT = result
    