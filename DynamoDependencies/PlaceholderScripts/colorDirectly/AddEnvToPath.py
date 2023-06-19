import sys
import os
import clr
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

if IN[0] and IN[1] : 
    # sys.path.append(r'D:\Work\TUM_Research\HiWiPatrick\PedSimAutomation\DynamoDependencies\DynamoVEnv\lib\site-packages')
    # sys.path.
    package_path = fr"{IN[1]}\lib\site-packages"

    if os.path.isdir(package_path):
        sys.path.append(package_path)
        OUT = 1
    else : 
        OUT = 0