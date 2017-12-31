#!/usr/bin/python
# Aurthor: sehattersley
# Purpose: Read data from the serial port on the RPi. Data is sent by the RPICT3V1 board which provide 3 currents and one voltage.
# Notes: Sometimes the serial port does not return all the data so I have added a loop to try a few times.
# If the Watts are -ve the CT is most likely connected the wrong way.

# --- Imports ---
import serial # Used for communicating with the RPICT3V1 Raspberry Pi board
import time # Used for the delay
import urllib # Used for web access
try:
	import httplib # Used for web access. Python 2
except ImportError:
	import http.client as httplib # Used for web access. Python 3
import numpy as np # Used for percentiles



# --- Classes ---
class CTVTSensor(object): # Class for the CT and VT sensors
	def __init__(self, sName, nTurnsRatio, bEnabled=0): # This is run when an onject is first created
		self.sName = sName
		self.bEnabled = bEnabled
		self.sNodeID = None
		self.dRealPower_W = None
		self.lsRealPower_W = [] # Create blank list
		self.dIrms_A = None
		self.lsIrms_A = []
		self.dVrms_V = None
		self.lsVrms_V = []
		self.nTurnsRatio = nTurnsRatio

	def PrintValues(self, sType): # Specify what type of data you want to print "Value" or "List"
		if self.bEnabled == 1: # Only print values if the sensors has been enabled
			if sType == "Value":
				if self.sNodeID is not None: # Only print if the value has been populated
					print(self.sName + " Node ID: " + self.sNodeID)
				if self.dRealPower_W is not None:
					print(self.sName + " Real Power: " + "%.2f" % self.dRealPower_W + " W")
				if self.dIrms_A is not None:
					print(self.sName + " Current: " + "%.2f" % self.dIrms_A + " A")
				if self.dVrms_V is not None:
					print( self.sName + " Voltage: " + "%.2f" % self.dVrms_V + " V")
			if sType == "List":
				if self.sNodeID is not None: # Only print if the value has been populated
					print(self.sName + " Node ID: " + self.sNodeID)
				if self.lsRealPower_W is not None:
					print(self.sName + " Real Power: " + str(self.lsRealPower_W) + " W")
				if self.lsIrms_A is not None:
					print(self.sName + " Current: " + str(self.lsIrms_A) + " A")
				if self.lsVrms_V is not None:
					print( self.sName + " Voltage: " + str(self.lsVrms_V) + " V")

	def ErrorCheck (self): # Check that the sensor reading are within the range of the sensor i.e. not bad data
		if not 0 <= self.dRealPower_W <= 4000: # Roughly 13A @ 253V
			self.dRealPower_W = None # Data is bad so set it to None so its not used later on in the code.
		if not 0 <= self.dIrms_A <= 15: # Circuits should not go above 13A standard UK socket
			self.dIrms_A = None
		if not 200 <= self.dVrms_V <= 270: # UK limits are 216.2V to 253V (-6% / +10%)
			self.dVrms_V = None



# --- Functions ---
def PostToEmoncms(sSensorName, sSensorValueType, dSensorValue, conn, sLocation, ApiKey, sNodeID, bDebugPrint): # Function to post data to an emoncms server
	MeasuredData = (sSensorName + "_" + sSensorValueType + ":%.2f" %(dSensorValue)) #Data name cannot have spaces.
	Request = sLocation + ApiKey + "&node=" + sNodeID + "&json=" + MeasuredData
	conn.request("GET", Request) # Make a GET request to the emoncms data. This basically sends the data.
	Response = conn.getresponse() # Get status and error message back from webpage. This must be done before a new GET command can be done.
	Response.read() # This line prevents the error response not ready. Its to do with the http socket being closed.
	if bDebugPrint == 1:
		print(sSensorName + ": data post status and reason - " + str(Response.status) + ", " + str(Response.reason))

def GetReadings():
	SerialConnection = serial.Serial('/dev/ttyAMA0', 38400) # Set up the serial connection
	for x in range(0,5): # Loop from 0 to 4 i.e. 5 iterations. This is becuase sometimes not all the data is successfully read first time.
		SerialResponse = SerialConnection.readline() # Read from the serial port
		if bDebugPrint == 1:
			print("Loop No. " + str(x))
			print("Raw data: " + SerialResponse) # Print the raw serial port data (CSV format with space not comma)

		if SerialResponse is not None:
			lsData = SerialResponse.split(" ") # Split the data into a list using the space
			if bDebugPrint == 1:
				print("Raw data in list format: " + str(lsData))
			if len(lsData) == 8: # We expect 8 values even if some sensors are not used.
				#oCT1.sNodeID = z[0] # Node ID is not used
				oCT1.dRealPower_W = round((float(lsData[1]) / oCT1.nTurnsRatio),2) # CTs being used are 100/1A which means they dont measure small currents well. To compensate extra turns have been used on the primary side.
				oCT2.dRealPower_W = round((float(lsData[2]) / oCT2.nTurnsRatio),2) # Due to this these extra turns need to be taken into account here by dividing by the turns ratio.
				oCT3.dRealPower_W = round((float(lsData[3]) / oCT3.nTurnsRatio),2)
				oCT1.dIrms_A = round((float(lsData[4]) / 1000 / oCT1.nTurnsRatio),2) # Readings come back in mA so they need dividing by 1000.
				oCT2.dIrms_A = round((float(lsData[5]) / 1000 /  oCT2.nTurnsRatio),2)
				oCT3.dIrms_A = round((float(lsData[6]) / 1000 / oCT3.nTurnsRatio),2)
				oVT1.dVrms_V = round((float(lsData[7][:-2])),2) # The last entry has a new line attached to it so this needs removing

				oCT1.ErrorCheck() # Check the data is realistic i.e. within the raneg of the sensor. If not set to None.
				oCT2.ErrorCheck()
				oCT3.ErrorCheck()
				oVT1.ErrorCheck()

				oCT1.lsRealPower_W.append(oCT1.dRealPower_W) # Add data to lists which are later used to get percentiles.
				oCT2.lsRealPower_W.append(oCT2.dRealPower_W)
				oCT3.lsRealPower_W.append(oCT3.dRealPower_W)
				oCT1.lsIrms_A.append(oCT1.dIrms_A)
				oCT2.lsIrms_A.append(oCT2.dIrms_A)
				oCT3.lsIrms_A.append(oCT3.dIrms_A)
				oVT1.lsVrms_V.append(oVT1.dVrms_V)

				if bDebugPrint ==1 :
					print("FORMATTED DATA: Note error check has been perfomed to extreme values have been removed")
					oCT1.PrintValues("List")
					oCT2.PrintValues("List")
					oCT3.PrintValues("List")
					oVT1.PrintValues("List")

				SerialConnection.close() # Function is about to break to close the serial connection
				time.sleep(5) # Delay to allow serial connect to reset
				break # exit the for loop now we have all the data
	SerialConnection.close() # Function has finished so close the serial connection
	time.sleep(5)



# --- Control Settings ---
bDebugPrint = 0
bDebugSendData = 1
bEmoncmsOrg = 1
bEmoncmsOther = 1



# --- Main Code ---
oCT1 = CTVTSensor("CT1", 8, 1) # Create an object and give it a name, turns ratio and enabled/disabled
oCT2 = CTVTSensor("CT2", 8, 1)
oCT3 = CTVTSensor("CT3", 8, 1)
oVT1 = CTVTSensor("VT1", 1, 1)

for x in range(0,6): # Get 6 lots of readings
	GetReadings()

try: oCT1.dRealPower_W = np.percentile((np.array(sorted(oCT1.lsRealPower_W))),80) # Take the 80th percentile. This removes any values that are within the limits of the sensor but are clearly false.
except TypeError: oCT1.dRealPower_W = None # If there are any error such as None data then set value to None

try: oCT2.dRealPower_W = np.percentile((np.array(sorted(oCT2.lsRealPower_W))),80) # The list must be sorted to take the percentile.
except TypeError: oCT2.dRealPower_W = None

try: oCT3.dRealPower_W = np.percentile((np.array(sorted(oCT3.lsRealPower_W))),80)
except TypeError: oCT3.dRealPower_W = None

try: oCT1.dIrms_A = np.percentile((np.array(sorted(oCT1.lsIrms_A))),80)
except TypeError: oCT1.dIrms_A = None

try: oCT2.dIrms_A = np.percentile((np.array(sorted(oCT2.lsIrms_A))),80)
except TypeError: oCT2.dIrms_A = None

try: oCT3.dIrms_A = np.percentile((np.array(sorted(oCT3.lsIrms_A))),80)
except TypeError: oCT3.dIrms_A = None

try: oVT1.dVrms_V = np.percentile((np.array(sorted(oVT1.lsVrms_V))),80)
except TypeError: oVT1.dVrms_V = None

if bDebugPrint == 1:
	print("FINAL DATA TO BE SENT TO EMONCMS:")
	print(oCT1.sName + ": " + str(oCT1.dRealPower_W) + "W")
	print(oCT2.sName + ": " + str(oCT2.dRealPower_W) + "W")
	print(oCT3.sName + ": " + str(oCT3.dRealPower_W) + "W")
	print(oCT1.sName + ": " + str(oCT1.dIrms_A) + "A")
	print(oCT2.sName + ": " + str(oCT2.dIrms_A) + "A")
	print(oCT3.sName + ": " + str(oCT3.dIrms_A) + "A")
	print(oVT1.sName + ": " + str(oVT1.dVrms_V) + "V")


# --- Send data to emoncms.org ---
if bDebugSendData == 1 and bEmoncmsOrg == 1:
	sMyApiKey = "enter API key here" # My emoncms.org read & write api key
	Connection = httplib.HTTPConnection("emoncms.org:80") # Address of emoncms server with port number
	sLocation = "/input/post?apikey=" # Subfolder for the given emoncms server
	sNodeID = "Server_Room" # Node IDs cant have spaces in them

	# CT1
	if oCT1.dIrms_A is not None: PostToEmoncms(oCT1.sName, "Irms_A", oCT1.dIrms_A, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint) # Only post to emoncms if there is data
	if oCT1.dRealPower_W is not None: PostToEmoncms(oCT1.sName, "RealPower_W", oCT1.dRealPower_W, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
	
	# CT2
	if oCT2.dIrms_A is not None: PostToEmoncms(oCT2.sName, "Irms_A", oCT2.dIrms_A, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
	if oCT2.dRealPower_W is not None: PostToEmoncms(oCT2.sName, "RealPower_W", oCT2.dRealPower_W, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
	
	# CT3
	if oCT3.dIrms_A is not None: PostToEmoncms(oCT3.sName, "Irms_A", oCT3.dIrms_A, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
	if oCT3.dRealPower_W is not None: PostToEmoncms(oCT3.sName, "RealPower_W", oCT3.dRealPower_W, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
	
	# VT1
	if oVT1.dVrms_V is not None: PostToEmoncms(oVT1.sName, "Vrms_V", oVT1.dVrms_V, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)



# --- Send data to local emoncms server ---
if bDebugSendData == 1 and bEmoncmsOther == 1:
	sMyApiKey = "enter API key here" # My Linux server emoncms read & write api key
	Connection = httplib.HTTPConnection("enter IP address here:80") # Address of local emoncms server with port number
	#Connection = httplib.HTTPConnection("localhost:80") # Address of local emoncms server with port number
	sLocation = "/emoncms/input/post?apikey=" # Subfolder for the given emoncms server
	sNodeID = "Server_Room" # Node IDs cant have any spaces

	# CT1
	if oCT1.dIrms_A is not None: PostToEmoncms(oCT1.sName, "Irms_A", oCT1.dIrms_A, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint) # Only post to emoncms if there is data
	if oCT1.dRealPower_W is not None: PostToEmoncms(oCT1.sName, "RealPower_W", oCT1.dRealPower_W, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
	
	# CT2
	if oCT2.dIrms_A is not None: PostToEmoncms(oCT2.sName, "Irms_A", oCT2.dIrms_A, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
	if oCT2.dRealPower_W is not None: PostToEmoncms(oCT2.sName, "RealPower_W", oCT2.dRealPower_W, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
	
	# CT3
	if oCT3.dIrms_A is not None: PostToEmoncms(oCT3.sName, "Irms_A", oCT3.dIrms_A, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
	if oCT3.dRealPower_W is not None: PostToEmoncms(oCT3.sName, "RealPower_W", oCT3.dRealPower_W, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
	
	# VT1
	if oVT1.dVrms_V is not None: PostToEmoncms(oVT1.sName, "Vrms_V", oVT1.dVrms_V, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)



if bDebugPrint ==1:
	print("End of script")