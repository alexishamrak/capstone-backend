The main file containing the current sensor driver script is: driver_script_aws.py.

! The script gets the current mac addresses of the sensors in use from the file: sensor_macs.txt. To change the sensors in use, replace the macs in this file. It is important to ensure that this file is in the same directory as the driver script.                                                                      !

To run this script, you must have the MbientLab python API installed. Installation details may be found here: https://mbientlab.com/tutorials/PyWindows.html
You will also need to ensure that the graceful shutdown python module is installed.

Ensure that the pi has an internet conection, and that the bluetooth is manually turned on before running this script.

It is highly recommended to download the MbientLab MetaMotion mobile application onto your smart device for help in resetting the sensors and checking their
battery level. This application is available for free on both the google play store, and the app store.

If a sensor is not responding or connecting to the pi try these potential solutions:
  1) While the pi is attempting a conect to the sensors, wave them in circles around the pi (approximately 10cm away from the pi)
  2) Using the mobile app, connect and disconnect to the sensors.
  3) Using the mobile app, issue a soft reset (when connected to a sensor, the soft reset option is one of the options in the three dots in the top right corner of the app.)
  4) Issue a hard reset:
      a) Press and hold the button on the sensor
      b) While continuing to hold the button, plug the sensor into the micro-USB charger. (When it detects the power source, the light should begin to flash slowly)
      c) Continue to hold the button for 10s
      d) release the button
      e) unplug the sensor from the charger
  5) Recharge the sensors, or let them rest for several minutes.
