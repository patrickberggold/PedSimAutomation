import clr
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *

site_x = int(IN[0])
site_y = int(IN[1]) 
CORR_WIDTH = int(IN[2]) 
NUM_ROOMS_SHORT_SIDE = int(IN[3])
NUM_ROOMS_LONG_SIDE = int(IN[4])
INCLUDE_BOTTLENECK = bool(IN[5])
# site_z = int(IN[6])
room_width = IN[6]
door_width = IN[7]
obstacle_width = IN[8]

txt_filename = \
    'floorplan_siteX_'+str(int(site_x))+'_siteY_'+str(int(site_y))+'_CORRWIDTH_'+str(CORR_WIDTH)+ '_NUMROOMS_'+str(NUM_ROOMS_SHORT_SIDE)+'_'+str(NUM_ROOMS_LONG_SIDE)+'_INCBNECK_'+str(INCLUDE_BOTTLENECK)+'.txt'

OUT = txt_filename, [site_x, site_y, CORR_WIDTH, NUM_ROOMS_SHORT_SIDE, NUM_ROOMS_LONG_SIDE, INCLUDE_BOTTLENECK , door_width , obstacle_width , room_width]