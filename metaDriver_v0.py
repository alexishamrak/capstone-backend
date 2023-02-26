# For now, this is probably not safe. I have not put in 
# mutexes yet.

from __future__ import print_function
from mbientlab.metawear import *
from time import sleep
from threading import Event
import platform
import sys
import json

class mw_data:
    def __init__(self,x_value,y_value,z_value,location,validity):
        self.x_value = x_value
        self.y_value = y_value
        self.z_value = z_value
        self.location = location
        self.is_valid = validity

data_MAC_pairs = dict()

class mw_device:
    def __init__(self,device,mac):
        self.device = device
        self.callback = FnVoid_VoidP_DataP(self.data_handler)
        self.mac = mac

    def data_handler(self,ctx,data):
        data_MAC_pairs[self.mac].is_valid = True
        data_MAC_pairs[self.mac].x_value = 