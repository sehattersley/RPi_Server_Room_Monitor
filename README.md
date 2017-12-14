# RPi_Server_Room_Monitor
Scripts used by RPi to read sensors and post to emoncms

read_board_v1.py = Reading the CT and VT board
read_sensors_v1.py = Reading the DHT22 sensors

Sensors connected:
	- 4 x DHT22 temperature and humidity sensors
	- 1 x RPICT3V1 Raspberrypi board from (http://lechacalshop.com) with 3 currents and one voltage
		(Firmware version 1.2 Burden resistor = 24 ohms which is suitable for 100 A CT type SCT-013-000)


Reading from DHT22:
cd ~
git clone https://github.com/adafruit/Adafruit_Python_DHT
sudo apt-get update
sudo apt-get install build-essential python-dev python-openssl
cd Adafruit_Python_DHT
sudo python setup.py install
sudo reboot

To test the DHT22:
cd Adafruit_Python_DHT/examples
sudo ./AdafruitDHT.py 2302 7


Note that 2302 is the sensor type as the example script can use different sensors. 7 is the number of the GPIO pin you are
using. The DHT22 sensor has 4 pins however one is not used: power, ground and data. There should be a 10k ohm resistor between
data and power. Connect DHT22 sensors while the RPi is turned off.

You could run the script using a cron job every minute:
sudo crontab -e
add the following line:
* * * * * /home/pi/Adafruit_Python_DHT/examples/AdafruitDHT.py


Reading from RPICT3V1 Raspberrypi board:

sudo apt-get install python-serial

Note that the board requires the use of CTs that output current not voltage. Some of the STC CT's are voltage output types. One
way to get around this is to stick with the standard 5 to 100A STC-013-000 CT but wrap more turns on the primary side and then
divide the currentand wattage reading by that figure.
