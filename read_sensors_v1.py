#!/usr/bin/python
# Author: sehattersley
# Purpose: Read CT and VT sensor data and post it to an emoncms server.



# --- Imports ---
import Adafruit_DHT # Python library for accessing the oDHT22 temperature and humidity sensor
import httplib, urllib # Used for web access



# --- Classes ---
class DHTSensor(object): # Class for the oDHT22 sensors
	def __init__(self, sName, bEnabled=0): # This is run when an onject is first created
		self.sName = sName
		self.bEnabled = bEnabled
		self.dTemperature_C = None
		self.dHumidity_P = None

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



# --- Control Settings ---
bDebugPrint = 0 # 0/1 will disable/enable debug print statements
bDebugSendData = 1 # Enable sending data to emoncms servers
bEmoncmsOrg = 0 # Send data to emoncms.org
bEmoncmsOther = 1 # Send data to another emoncms server eg. local emonpi or a linux server

oDHT1 = DHTSensor("DHT1", 1) #Create an oDHT22 sensor object, give it a name and enable/disable it
oDHT2 = DHTSensor("DHT2", 1)
oDHT3 = DHTSensor("DHT3", 1)
oDHT4 = DHTSensor("DHT4", 1)



# --- Read the sensor values ---
# oDHT22: The read_retry method will try 15 reads waiting 2 seconds between each retry
# Sometimes reading the sensors can fail becuase the linux kernal takes priority
if oDHT1.bEnabled == 1: # Only read the sensor if it has been anabled
	oDHT1.dHumidity_P, oDHT1.dTemperature_C = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 4) # The function needs to know the type of sensor and the RPi GPIO pin number
	oDHT1.ErrorCheck() # Check the data is realistic

if oDHT2.bEnabled == 1:
	oDHT2.dHumidity_P, oDHT2.dTemperature_C = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 17)
	oDHT2.ErrorCheck()

if oDHT3.bEnabled == 1:
	oDHT3.dHumidity_P, oDHT3.dTemperature_C = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 23)
	oDHT3.ErrorCheck()

if oDHT4.bEnabled == 1:
	oDHT4.dHumidity_P, oDHT4.dTemperature_C = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 10)
	oDHT4.ErrorCheck()

#Debug statements
if bDebugPrint == 1:
	if oDHT1.bEnabled == 0:
		print(oDHT1.sName + ": Disabled")
	elif oDHT1.dTemperature_C is not None and oDHT1.dHumidity_P is not None:
		oDHT1.PrintValues()
	else:
		print(oDHT1.sName + ": Error Reading Sensor")
	
	if oDHT2.bEnabled == 0:
		print(oDHT2.sName + ": Disabled")
	elif oDHT2.dTemperature_C is not None and oDHT2.dHumidity_P is not None:
		oDHT2.PrintValues()
	else:
		print(oDHT2.sName + ": Error Reading Sensor")

	if oDHT3.bEnabled == 0:
		print(oDHT3.sName + ": Disabled")
	elif oDHT3.dTemperature_C is not None and oDHT3.dHumidity_P is not None:
		oDHT3.PrintValues()
	else:
		print(oDHT3.sName + ": Error Reading Sensor")

	if oDHT4.bEnabled == 0:
		print(oDHT4.sName + ": Disabled")
	elif oDHT4.dTemperature_C is not None and oDHT4.dHumidity_P is not None:
		oDHT4.PrintValues()
	else:
		print(oDHT4.sName + ": Error Reading Sensor")



# --- Send data to emoncms.org ---
if bDebugSendData == 1 and bEmoncmsOrg == 1:
	sMyApiKey = "enter API key here" # emoncms.org read & write api key
	Connection = httplib.HTTPConnection("emoncms.org:80") # Address of emoncms server with port number
	sLocation = "/input/post?apikey=" # Subfolder for the given emoncms server
	sNodeID = "Server_Room" # Node IDs cant have spaces in them

	# Sensor 1
	if oDHT1.dTemperature_C is not None: #Only post to emoncms if there is data
		PostToEmoncms(oDHT1.sName, "Temperature_C", oDHT1.dTemperature_C, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
	if oDHT1.dHumidity_P is not None:
		PostToEmoncms(oDHT1.sName, "Humidity_P", oDHT1.dHumidity_P, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)

	# Sensor 2
	if oDHT2.dTemperature_C is not None:
		PostToEmoncms(oDHT2.sName, "Temperature_C", oDHT2.dTemperature_C, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
	if oDHT2.dHumidity_P is not None:
		PostToEmoncms(oDHT2.sName, "Humidity_P", oDHT2.dHumidity_P, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)

	# Sensor 3
	if oDHT3.dTemperature_C is not None:
		PostToEmoncms(oDHT3.sName, "Temperature_P", oDHT3.dTemperature_C, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
	if oDHT3.dHumidity_P is not None:
		PostToEmoncms(oDHT3.sName, "Humidity_P", oDHT3.dHumidity_P, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)

	# Sensor 4
	if oDHT4.dTemperature_C is not None:
		PostToEmoncms(oDHT4.sName, "Temperature_C", oDHT4.dTemperature_C, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
	if oDHT4.dHumidity_P is not None:
		PostToEmoncms(oDHT4.sName, "Humidity_P", oDHT4.dHumidity_P, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)



# --- Send data to local emoncms server ---
if bDebugSendData == 1 and bEmoncmsOther == 1:
	sMyApiKey = "enter API key here" # My Linux server emoncms read & write api key
	Connection = httplib.HTTPConnection("localhost:80") # Address of local emoncms server with port number
	sLocation = "/emoncms/input/post?apikey=" # Subfolder for the given emoncms server
	sNodeID = "Server_Room" # Node IDs cant have spaces in them

	# Sensor 1
	if oDHT1.dTemperature_C is not None: #Only post to emoncms if there is data
		PostToEmoncms(oDHT1.sName, "Temperature_C", oDHT1.dTemperature_C, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
	if oDHT1.dHumidity_P is not None:
		PostToEmoncms(oDHT1.sName, "Humidity_P", oDHT1.dHumidity_P, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)

	# Sensor 2
	if oDHT2.dTemperature_C is not None:
		PostToEmoncms(oDHT2.sName, "Temperature_C", oDHT2.dTemperature_C, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
	if oDHT2.dHumidity_P is not None:
		PostToEmoncms(oDHT2.sName, "Humidity_P", oDHT2.dHumidity_P, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)

	# Sensor 3
	if oDHT3.dTemperature_C is not None:
		PostToEmoncms(oDHT3.sName, "Temperature_C", oDHT3.dTemperature_C, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
	if oDHT3.dHumidity_P is not None:
		PostToEmoncms(oDHT3.sName, "Humidity_P", oDHT3.dHumidity_P, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)

	# Sensor 4
	if oDHT4.dTemperature_C is not None:
		PostToEmoncms(oDHT4.sName, "Temperature_C", oDHT4.dTemperature_C, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
	if oDHT4.dHumidity_P is not None:
		PostToEmoncms(oDHT4.sName, "Humidity_P", oDHT4.dHumidity_P, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)



if bDebugPrint == 1:
	print("Script Finished")
#End of script