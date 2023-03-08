# run "sudo hcitool dev" to find which hci is in use (x)
# You must execute this command in terminal first: "sudo hciconfig hcix piscan"

from __future__ import print_function
from mbientlab.metawear import *
from time import sleep
from threading import Event
import json
import time
import platform
import sys
from graceful_shutdown import ShutdownProtection
#import bluetooth

total_samples = 0
start_time = end_time = 0

class State:
    def __init__(self, device, location):
        self.location = location
        self.device = device
        #self.device.on_disconnect = lambda end_program: end_time = time.time()
        self.samples = 0
        self.callback = FnVoid_VoidP_DataP(self.data_handler)

    def data_handler(self, ctx, data):
        # generate the json object with the data collected
        json_intermediary = {
            "sensor_id" : self.location,
            "timestamp_s" : time.time(),
            "x" : parse_value(data).x,
            "y" : parse_value(data).y,
            "z" : parse_value(data).z
        }
        json_data = json.dumps(json_intermediary)
        #print("%s -> %s" % (self.location, json_data))
        # Write the json to the bluetooth client socket
        global total_samples
        total_samples += 1
        
    def disconnect_function(self):
        while not(self.device.is_connected):
            print("Lost connection")
            global end_time
            end_time = time.time()
            print(end_time)
            exit()
            
            
def disconnect_recovery(device):
    print(device.is_connected)
    while not(device.is_connected):
        print("Attempting reconnect for " + device.address)
        res = device.connect()
        print(res)
        if res == None:
            break
        sleep(5.0)

# Open and read the sensor identifier info from the config file
# line: "loctation MAC"
f = open("sensor_macs.txt","r")

# Generate an array of sensors and populate with the info from the file
# Establish a connection with each
states = []
for line in f:
    words = line.split()
    print(words)
    d = MetaWear(words[1])
    d.connect()
    print("Connected to " + words[0] +" "+ d.address)
    states.append(State(d,words[0]))

f.close()

try:

    for s in states: #Configure the devices to record data
        print("Configuring device")
        libmetawear.mbl_mw_settings_set_connection_parameters(s.device.board, 7.5, 7.5, 0, 6000)
        sleep(1.5)

        libmetawear.mbl_mw_acc_set_odr(s.device.board, 1.0)
        libmetawear.mbl_mw_acc_set_range(s.device.board, 16.0)
        libmetawear.mbl_mw_acc_write_acceleration_config(s.device.board)

        signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
        libmetawear.mbl_mw_datasignal_subscribe(signal, None, s.callback)

        libmetawear.mbl_mw_acc_enable_acceleration_sampling(s.device.board)
        libmetawear.mbl_mw_acc_start(s.device.board)
    print("Starting")
    start_time = time.time()
    print(start_time)
    while True:
        sleep(10.0)
        print("Total samples: ", total_samples)
        for s in states:
            if s.device.is_connected == False:
                exit(1)
            print(s.location, ": ", s.device.is_connected)

except (SystemExit, KeyboardInterrupt, OSError) as ex:
    # When the program is closed, close up all of the open resources and
    # exit
    end_time = time.time()
    print("seconds ran: ", (end_time - start_time))
    for s in states:
        libmetawear.mbl_mw_acc_stop(s.device.board)
        libmetawear.mbl_mw_acc_disable_acceleration_sampling(s.device.board)

        signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
        libmetawear.mbl_mw_datasignal_unsubscribe(signal)
        libmetawear.mbl_mw_debug_disconnect(s.device.board)

    
