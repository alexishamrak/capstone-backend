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
import bluetooth

class State:
    def __init__(self, device, location):
        self.location = location
        self.device = device
        self.device.on_disconnect = FnVoid_VoidP_DataP(self.disconnect_function)
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
        print("%s -> %s" % (self.location, json_data))
        # Write the json to the bluetooth client socket
        client_sock.send(json_data)
        
    def disconnect_function(self):
        while not(self.device.is_connected):
            print("Attempting to re-establish connection with " + self.locaiton)
            self.device.connect()
            sleep(5.0)
            
            
def disconnect_recovery(device):
    print(device.is_connected)
    while not(device.is_connected):
        print("Attempting reconnect for " + device.address)
        res = device.connect()
        print(res)
        if res == None:
            break
        sleep(5.0)

# Open a bluetooth server on the pi for the desktop app to pair with
server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
server_sock.bind(("",bluetooth.PORT_ANY))
server_sock.listen(1)
port = server_sock.getsockname()[1]
print(port)
uuid = "e63edc34-5ba6-4764-9c00-6c14249597f6"
bluetooth.advertise_service(server_sock, name="HubServer", service_id=uuid,
                            service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
                            #profiles=[bluetooth.SERIAL_PORT_PROFILE]#,
                            )
print("Waiting for connection with desktop app")
client_sock, client_info = server_sock.accept()
client_sock.send("Hello from the pi")
print("Established connection with desktop app")

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

    while True:
        sleep(10.0)

except (SystemExit, KeyboardInterrupt, OSError) as ex:
    # When the program is closed, close up all of the open resources and
    # exit
    client_sock.close()
    server_sock.close()
  
    
    for s in states:
        libmetawear.mbl_mw_acc_stop(s.device.board)
        libmetawear.mbl_mw_acc_disable_acceleration_sampling(s.device.board)

        signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
        libmetawear.mbl_mw_datasignal_unsubscribe(signal)
        libmetawear.mbl_mw_debug_disconnect(s.device.board)

    print("Total Samples Received")
    for s in states:
        print("%s -> %d" % (s.device.address, s.samples))
