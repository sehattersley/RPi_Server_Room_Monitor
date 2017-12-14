#!/usr/bin/python
# Aurthor: sehattersley
# Purpose: Read data from the serial port on the RPi. Data is sent by the RPICT3V1 board which provide 3 currents and one voltage.
# Notes: Sometimes the serial port does not return all the data so I have added a loop to try a few times.
# If the Watts are -ve the CT is most likely connected the wrong way.

# --- Imports ---
import serial # Used for communicating with the RPICT3V1 Raspberry Pi board
import time # Used for the delay
import httplib, urllib # Used for web access



# --- Classes ---
class CTVTSensor(object): # Class for the CT and VT sensors
	def __init__(self, sName, nTurnsRatio, bEnabled=0): # This is run when an onject is first created
		self.sName = sName
		self.bEnabled = bEnabled
		self.sNodeID = None
		self.dRealPower_W = None
		self.dIrms_A = None
		self.dVrms_V = None
		self.nTurnsRatio = nTurnsRatio

	def PrintValues(self):
		if self.bEnabled == 1: #Only print values if the sensors has been enabled
			#print(self.name + ': Temperature = {0:0.1f} *C  Humidity = {1:0.1f} %'.format(self.temperature, self.humidity))
			if self.sNodeID is not None: # Only print if the value has been populated
				print(self.sName + " Node ID: " + self.sNodeID)
			if self.dRealPower_W is not None:
				print(self.sName + " Real Power: " + "%.2f" % self.dRealPower_W + " W")
			if self.dIrms_A is not None:
				print(self.sName + " Current: " + "%.2f" % self.dIrms_A + " A")
			if self.dVrms_V is not None:
				print( self.sName + " Voltage: " + "%.2f" % self.dVrms_V + " V")

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



# --- Control Settings ---
bDebugPrint = 0
bDebugSendData = 1
bEmoncmsOrg = 0
bEmoncmsOther = 1

oCT1 = CTVTSensor("CT1", 8, 1) # Create an object and give it a name, turns ratio and enabled/disabled
oCT2 = CTVTSensor("CT2", 8, 1)
oCT3 = CTVTSensor("CT3", 8, 1)
oVT1 = CTVTSensor("VT1", 1, 1)



 # --- Read the sensors and save the data ---
for x in range(0,5): # Loop from 0 to 4 i.e. 5 iterations. This is becuase sometimes not all the data is successfully read first time.
	SerialConnection = serial.Serial('/dev/ttyAMA0', 38400) # Set up the serial connection
	SerialResponse = SerialConnection.readline() # Read from the serial port
	if bDebugPrint == 1:
		print("Loop No. " + str(x))
		print("Raw data: " + SerialResponse) # Print the raw serial port data (CSV format with space not comma)

	if SerialResponse is not None:
		lsData = SerialResponse.split(" ") # Split the data into a list using the space
		if bDebugPrint == 1:
			print("Raw data in list format: " + str(lsData))
		if len(lsData) == 8: # We expect 8 values even if some sensors are not used.
			#CT1.sNodeID = z[0] # Node ID is not used
			oCT1.dRealPower_W = float(lsData[1]) / oCT1.nTurnsRatio # CTs being used are 100/1A which means they dont measure small currents well. To compensate extra turns have been used on the primary side.
			oCT2.dRealPower_W = float(lsData[2]) / oCT2.nTurnsRatio # Due to this these extra turns need to be taken into account here by dividing by the turns ratio.
			oCT3.dRealPower_W = float(lsData[3]) / oCT3.nTurnsRatio
			oCT1.dIrms_A = float(lsData[4]) / 1000 / oCT1.nTurnsRatio # Readings come back in mA so they need dividing by 1000.
			oCT2.dIrms_A = float(lsData[5]) / 1000 /  oCT2.nTurnsRatio
			oCT3.dIrms_A = float(lsData[6]) / 1000 / oCT3.nTurnsRatio
			oVT1.dVrms_V = float(lsData[7][:-2]) # The last entry has a new line attached to it so this needs removing

			if bDebugPrint ==1 :
				print("FORMATTED DATA: Note error check is performed after this so some data may be cleared")
				oCT1.PrintValues()
				oCT2.PrintValues()
				oCT3.PrintValues()
				oVT1.PrintValues()

			oCT1.ErrorCheck() # Check the data is realistic
			oCT2.ErrorCheck()
			oCT3.ErrorCheck()
			oVT1.ErrorCheck()

			break # exit the for loop now we have all the data
	SerialConnection.close() # Close the serial connection
	time.sleep(5) # Wait 5 seconds before trying the serial connection again



# --- Send data to emoncms.org ---
if bDebugSendData == 1 and bEmoncmsOrg == 1:
	sMyApiKey = "enter API key here" # emoncms.org read & write api key
	Connection = httplib.HTTPConnection("emoncms.org:80") # Address of emoncms server with port number
	sLocation = "/input/post?apikey=" # Subfolder for the given emoncms server
	sNodeID = "Server_Room" # Node IDs cant have spaces in them

	# CT1
	if oCT1.dIrms_A is not None and oCT1.dRealPower_W is not None: #Only post to emoncms if there is data
		PostToEmoncms(oCT1.sName, "Irms_A", oCT1.dIrms_A, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
		PostToEmoncms(oCT1.sName, "RealPower_W", oCT1.dRealPower_W, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)

	# CT2
	if oCT2.dIrms_A is not None and oCT2.dRealPower_W is not None:
		PostToEmoncms(oCT2.sName, "Irms_A", oCT2.dIrms_A, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
		PostToEmoncms(oCT2.sName, "RealPower_W", oCT2.dRealPower_W, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)

	# CT3
	if oCT3.dIrms_A is not None and oCT3.dRealPower_W is not None:
		PostToEmoncms(oCT3.sName, "Irms_A", oCT3.dIrms_A, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
		PostToEmoncms(oCT3.sName, "RealPower_W", oCT3.dRealPower_W, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)

	# VT1
	if oVT1.dVrms_V is not None:
		PostToEmoncms(oVT1.sName, "Vrms_V", oVT1.dVrms_V, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)



# --- Send data to local emoncms server ---
if bDebugSendData == 1 and bEmoncmsOther == 1:
	sMyApiKey = "enter API key here" # My Linux server emoncms read & write api key
	Connection = httplib.HTTPConnection("localhost:80") # Address of local emoncms server with port number
	sLocation = "/emoncms/input/post?apikey=" # Subfolder for the given emoncms server
	sNodeID = "Server_Room" # Node IDs cant have any spaces

	# CT1
	if oCT1.dIrms_A is not None and oCT1.dRealPower_W is not None: #Only post to emoncms if there is data
		PostToEmoncms(oCT1.sName, "Irms_A", oCT1.dIrms_A, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
		PostToEmoncms(oCT1.sName, "RealPower_W", oCT1.dRealPower_W, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)

	# CT2
	if oCT2.dIrms_A is not None and oCT2.dRealPower_W is not None:
		PostToEmoncms(oCT2.sName, "Irms_A", oCT2.dIrms_A, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
		PostToEmoncms(oCT2.sName, "RealPower_W", oCT2.dRealPower_W, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)

	# CT3
	if oCT3.dIrms_A is not None and oCT3.dRealPower_W is not None:
		PostToEmoncms(oCT3.sName, "Irms_A", oCT3.dIrms_A, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)
		PostToEmoncms(oCT3.sName, "RealPower_W", oCT3.dRealPower_W, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)

	# VT1
	if oVT1.dVrms_V is not None:
		PostToEmoncms(oVT1.sName, "Vrms_V", oVT1.dVrms_V, Connection, sLocation, sMyApiKey, sNodeID, bDebugPrint)



if bDebugPrint ==1:
	print("End of script")