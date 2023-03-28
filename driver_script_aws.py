# the aws related code comes from here: https://aws.amazon.com/premiumsupport/knowledge-center/iot-core-publish-mqtt-messages-python/

from __future__ import print_function
from mbientlab.metawear import *
from time import sleep
import time
from threading import Event
import json
import platform
import sys
from graceful_shutdown import ShutdownProtection
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT

class State:
    def __init__(self, device, location):
        self.location = location
        self.device = device
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
        global TOPIC
        json_data = json.dumps(json_intermediary)
        print("%s -> %s" % (self.location, json_data))
        # Write json to aws
        aws_client.publish(TOPIC, json_data, 1)
        

# *These need to be checked by someone who knows what they are doing.* -josh
ENDPOINT = "a2yj29llu7rbln-ats.iot.ca-central-1.amazonaws.com"
CLIENT_ID = "testDevice"
PATH_TO_CERTIFICATE = "aws_files/d9704a03ad1d01fa48eb96456b0333ca9525da8252c308d0ba8a08b703e07578-certificate.pem.crt"
PATH_TO_PRIVATE_KEY = "aws_files/d9704a03ad1d01fa48eb96456b0333ca9525da8252c308d0ba8a08b703e07578-private.pem.key"
PATH_TO_AMAZON_ROOT_CA_1 = "aws_files/root-CA.crt"
TOPIC = "sensor-data"

aws_client = AWSIoTPyMQTT.AWSIoTMQTTClient(CLIENT_ID)
aws_client.configureEndpoint(ENDPOINT, 8883)
aws_client.configureCredentials(PATH_TO_AMAZON_ROOT_CA_1, PATH_TO_PRIVATE_KEY, PATH_TO_CERTIFICATE)


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
    aws_client.connect()
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
        # The sleep is not a multiple of 1.0s because this way it is less likely to interrupt a data publish.
        sleep(9.5)
        # The following loop has to do with a test that I want to run soon. It should not make it to production. -josh
        for s in states:
            if not s.device.is_connected:
                sys.exit("lost sensor connection")

except (SystemExit, KeyboardInterrupt, OSError) as ex:
    # When the program is closed, close up all of the open resources and
    # exit
    aws_client.publish(TOPIC, json.dumps("Stream terminating"), 1)
    sleep(1.0)
    aws_client.publish(TOPIC, json.dumps("Stream terminating"), 1)
    print(json.dumps("Stream terminating"))
    aws_client.disconnect()
    
    for s in states:
        s.device.disconnect()

    print("Stream terminated")
