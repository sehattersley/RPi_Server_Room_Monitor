#!/usr/bin/python
# Author: sehattersley
# Purpose: Read CT and VT sensor data and post it to an emoncms server.
# Notes: 



# --- Imports ---
import Adafruit_DHT # Python library for accessing the oDHT22 temperature and humidity sensor
import urllib # Used for web access
try:
	import httplib # Used for web access. Python 2
except ImportError:
	import http.client as httplib # Used for web access. Python 3
import numpy as np # Used for percentiles



# --- Classes ---
class DHTSensor(object): # Class for the oDHT22 sensors
	_registry = [] # Keep a list of class objects

	def __init__(self, sName, bEnabled=0): # This is run when an onject is first created
		self._registry.append(self)
		self.sName = sName
		self.bEnabled = bEnabled
		self.dTemperature_C = None
		self.lsTemperature_C = [] # Create blank list
		self.dHumidity_P = None
		self.lsHumidity_P = []

	def PrintValues(self):
		if self.bEnabled == 1: # Only print values if the sensors has been enabled
			print(self.sName + ': Temperature = {0:0.1f} *C  Humidity = {1:0.1f} %'.format(self.dTemperature_C, self.dHumidity_P))

	def ErrorCheck (self): # Check that the sensor reading are within the range of the sensor i.e. not bad data
		if not -40 <= self.dTemperature_C <= 80:
			self.dTemperature_C = None # Data is bad so set it to None so its not used later on in the code.
		if not 0 <= self.dHumidity_P <= 100:
			self.dHumidity_P = None



# --- Functions ---
def PostToEmoncms(sSensorName, sSensorValueType, dSensorValue, conn, sLocation, ApiKey, sNodeID, bDebugPrint): # Function to post data to an emoncms server
	MeasuredData = (sSensorName + "_" + sSensorValueType + ":%.1f" %(dSensorValue)) #Data name cannot have spaces. oDHT22 sensor can only give 1 decimal place
	Request = sLocation + ApiKey + "&node=" + sNodeID + "&json=" + MeasuredData
	conn.request("GET", Request) # Make a GET request to the emoncms data. This basically sends the data.
	Response = conn.getresponse() # Get status and error message back from webpage. This must be done before a new GET command can be done.
	Response.read() # This line prevents the error response not ready. Its to do with the http socket being closed.
	if bDebugPrint == 1:
		print(sSensorName + ": data post status and reason - " + str(Response.status) + ", " + str(Response.reason))

def GetReadings():
	# oDHT22: The read_retry method will try 15 reads waiting 2 seconds between each retry
	# Sometimes reading the sensors can fail becuase the linux kernal takes priority
	if oDHT1.bEnabled == 1: # Only read the sensor if it has been anabled
		oDHT1.dHumidity_P, oDHT1.dTemperature_C = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 4) # The function needs to know the type of sensor and the RPi GPIO pin number
		oDHT1.ErrorCheck() # Check the data is realistic
		oDHT1.lsHumidity_P.append(oDHT1.dHumidity_P) # Add to list which is used later for percentiles.
		oDHT1.lsTemperature_C.append(oDHT1.dTemperature_C)

	if oDHT2.bEnabled == 1:
		oDHT2.dHumidity_P, oDHT2.dTemperature_C = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 17)
		oDHT2.ErrorCheck()
		oDHT2.lsHumidity_P.append(oDHT2.dHumidity_P)
		oDHT2.lsTemperature_C.append(oDHT2.dTemperature_C)

	if oDHT3.bEnabled == 1:
		oDHT3.dHumidity_P, oDHT3.dTemperature_C = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 23)
		oDHT3.ErrorCheck()
		oDHT3.lsHumidity_P.append(oDHT3.dHumidity_P)
		oDHT3.lsTemperature_C.append(oDHT3.dTemperature_C)

	if oDHT4.bEnabled == 1:
		oDHT4.dHumidity_P, oDHT4.dTemperature_C = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 10)
		oDHT4.ErrorCheck()	
		oDHT4.lsHumidity_P.append(oDHT4.dHumidity_P)
		oDHT4.lsTemperature_C.append(oDHT4.dTemperature_C)



# --- Control Settings ---
bDebugPrint = 0 # 0/1 will disable/enable debug print statements
bDebugSendData = 1 # Enable sending data to emoncms servers
bEmoncmsOrg = 1 # Send data to emoncms.org
bEmoncmsOther = 1 # Send data to another emoncms server eg. local emonpi or a linux server



# --- Main Code ---
oDHT1 = DHTSensor("DHT1", 1) #Create an oDHT22 sensor object, give it a name and enable/disable it
oDHT2 = DHTSensor("DHT2", 1)
oDHT3 = DHTSensor("DHT3", 1)
oDHT4 = DHTSensor("DHT4", 1)

for x in range(0,6): # Get 6 lots of readings so a percentile can be taken
	GetReadings()

for item in DHTSensor._registry:
	if item.bEnabled == 1: # Only run if the sensor is enabled
		try: item.dTemperature_C = np.percentile((np.array(sorted(item.lsTemperature_C))),80) # Take the 80th percentile. This removes any values that are within the limits of the sensor but are clearly false. The list must be sorted to take the percentile.
		except TypeError: oDHT1.dTemperature_C = None # If there are any error such as None data then set value to None so the data is not sent to EMONCMS
		try: item.dHumidity_P = np.percentile((np.array(sorted(item.lsHumidity_P))),80) # Take the 80th percentile. This removes any values that are within the limits of the sensor but are clearly false. The list must be sorted to take the percentile.
		except TypeError: item.dHumidity_P = None
	
	if bDebugPrint == 1: # Debug statements
		if item.bEnabled == 0:
			print(item.sName + ": Disabled")
		elif item.dTemperature_C is not None and item.dHumidity_P is not None:
			item.PrintValues()
		else:
			print(item.sName + ": Error Reading Sensor")



# --- Send data to emoncms.org ---
if bDebugSendData == 1 and bEmoncmsOrg == 1:
	sMyApiKey = "enter API kay here" # emoncms.org read & write api key
	Connection = httplib.HTTPConnection("emoncms.org:80") # Address of emoncms server with port number
	sLocation = "/input/post?apikey=" # Subfolder for the given emoncms server
	sNodeID = "Server_Room" # Node IDs cant have spaces in them

	for item in DHTSensor._registry:
		if item.bEnabled == 1:
			if item.dTemperature_C is not None: #Only post to emoncms if there is data
				PostToEmoncms(item.sName, "Temperature_C", item.dTemperature_C, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
			if item.dHumidity_P is not None:
				PostToEmoncms(item.sName, "Humidity_P", item.dHumidity_P, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)



# --- Send data to local emoncms server ---
if bDebugSendData == 1 and bEmoncmsOther == 1:
	sMyApiKey = "enter API key here" # Local emoncms read & write api key
	Connection = httplib.HTTPConnection("enter IP address here:80") # Address of Linux emoncms server with port number
	#Connection = httplib.HTTPConnection("localhost:80") # Address of local emoncms server with port number
	sLocation = "/emoncms/input/post?apikey=" # Subfolder for the given emoncms server
	sNodeID = "Server_Room" # Node IDs cant have spaces in them

	for item in DHTSensor._registry:
		if item.bEnabled == 1:
			if item.dTemperature_C is not None: #Only post to emoncms if there is data
				PostToEmoncms(item.sName, "Temperature_C", item.dTemperature_C, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
			if item.dHumidity_P is not None:
				PostToEmoncms(item.sName, "Humidity_P", item.dHumidity_P, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)



if bDebugPrint == 1:
	print("Script Finished")
#End of script