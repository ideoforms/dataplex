import glob
import time
import serial
import datetime
import threading

# from Queue import *

"""
Must be put into data logger mode by holding CLEAR + WINDSPEED for 3 seconds.
!!0000008002EF0000----0306--------0000004500000000
"""

DATA_HEADER = "!!"
DATA_FIELDS = [
	"wind_speed",
	"wind_dir",
	"temperature",
	"rain",
	"pressure",
	"indoor_temp",
	"humidity",
	"indoor_humidity",
	"date",
	"time",
	"rain_total",
	"wind_speed_mean"
]

class Ultimeter:
	def __init__(self, debug = False, port = None):
		self.port = None
		self.debug = debug
		self.buffer = ""
		self.handler = None

		#------------------------------------------------------------------------
		# dictionary of current values
		#------------------------------------------------------------------------
		self.values = {}

		self.port_name = port
		self.read_thread = None

		self.open()
	
	def start(self):
		#------------------------------------------------------------------------
		# start running, and connect when serial port available
		#------------------------------------------------------------------------
		if self.read_thread:
			print("*** already running background poll, refusing to start another thread")
			return
		else:
			self.read_thread = threading.Thread(target = self.read_serial)
			#------------------------------------------------------------------------
			# set daemon mode to True so this thread dies when the main thread
			# is killed.
			#------------------------------------------------------------------------
			self.read_thread.daemon = True
			self.read_thread.start()

	def trace(self, text):
		if self.debug:
			print(text)

	@property
	def is_open(self):
		""" Indicate whether this Ultimeter device is connected.
		"""
		return True if self.port else False

	def open(self, port_name = None):
		""" Open a connection to the named serial device (eg /dev/tty.*)
		"""
		if self.is_open:
			return

		if port_name is not None:
			self.port_name = port_name

		if self.port_name is None:
			#------------------------------------------------------------------------
			# see if we can find a default FTDI-style interface ID
			#------------------------------------------------------------------------
			interfaces = glob.glob("/dev/cu.usbserial-*")
			interfaces = sorted(interfaces)
			if interfaces:
				self.port_name = interfaces[0]
				print(("Using port %s" % self.port_name))

		if self.port_name is None:
			raise Exception("No serial port found, please specify.")

		self.port = serial.Serial(port = self.port_name, baudrate = 2400, timeout = 0.1)
		# self.port.setPort(self.port_name)
		# self.port.open()

		#------------------------------------------------------------------------
		# each time we connect, set the date of the unit and switch it to
		# datalogger mode, as both of these things are lost on reset.
		#------------------------------------------------------------------------
		self.set_date()
		self.set_data_logger()
		# self.set_pressure(1000)

		return self.port.getCTS()

	def close(self):
		if self.port:
			self.port.close()
		self.port = None


	def set_date(self):
		#------------------------------------------------------------------------
		# >Uyyyy
		# Set year
		#------------------------------------------------------------------------
		# >Addddmmmm
		# Set Date and Time (decimal digits dddd = day of year,
		# mmmm = minute of day; Jan 1 = 0000, Midnight = 0000)
		#------------------------------------------------------------------------
		now = datetime.datetime.now() 

		# calculate day of year (number from 0)
		day_of_year = datetime.datetime(now.year, now.month, now.day).toordinal() - 1

		# calculate minute of day
		minute_of_day = now.minute + 60 * now.hour
		self.port.write(">U%04d\r\n".encode() % now.year)
		self.port.write(">A%04d%04d\r\n".encode() % (day_of_year, minute_of_day))
		# print " - written time settings(day of year = %d, minute of day = %d)" % (day_of_year, minute_of_day)

	def set_data_logger(self):
		# >I
		# Set output mode to Data Logger Mode (continuous output)
		time.sleep(0.5)
		self.port.write(">I\n".encode())
	
	def set_pressure(self, pressure):
		time.sleep(0.5)
		self.port.write(">E%05d".encode() % (pressure * 10))

	def read_serial(self):
		""" Read loop that continuously reads CR-delimited serial data.
		If the connection is closed, it will be reopened automatically. 
		"""
		while True:
			self.open()

			try:
				empty_tries = 0
				while self.port and self.port.isOpen():
					n = self.port.inWaiting()
					if n > 0:
						empty_tries = 0
					else:
						empty_tries = empty_tries + 1
						if empty_tries > 50:
							raise Exception("No data read, bailing")
					while n:
						try:
							text = self.port.read(size = n)
							if len(text) == 0: continue
							text = text.decode()
							for char in text:
								if char == "\n" or char == "\n":
									if self.buffer:
										self.handle(self.buffer)
									self.buffer = ""
								else:
									self.buffer += char
							self.trace("[POLL] read: %s" % text)
						except serial.SerialException as e:
							print(("*** error reading serial: %s" % e))
							break
						n = self.port.inWaiting()
					time.sleep(0.04)
			except Exception as e:
				print(("Exception: %s" % e))
				pass

			# reset data if we've lost connection so we don't keep sending
			self.values = {}
			self.close()
			print("Trying to open port...")
			time.sleep(1)

	def handle(self, message):
		""" Execute a complete message. """

		if not message.startswith(DATA_HEADER):
			#------------------------------------------------------------------------
			# invalid message (no header.)
			#------------------------------------------------------------------------
			return

		message = message[len(DATA_HEADER):]
		self.values = {}
		for field in DATA_FIELDS:
			value = message[:4]

			#------------------------------------------------------------------------
			# Interpret our message as a hex value.
			#------------------------------------------------------------------------
			try:
				value = int("0x" + value, 0)
			except:
				value = 0
			message = message[4:]

			#------------------------------------------------------------------------
			# Now convert between native serial values and our desired metric
			# measure.
			#------------------------------------------------------------------------
			if field == "temperature":
				#------------------------------------------------------------------------
				# temperature: unit = 0.1 degrees fahrenheit
				# convert to degrees celsius
				#------------------------------------------------------------------------
				value = value * 0.1
				value = (value - 32) / 1.8

			elif field == "humidity":
				#------------------------------------------------------------------------
				# humidity: unit = 0.1% RH
				#------------------------------------------------------------------------
				value = value * 0.1

			elif field == "wind_dir":
				#------------------------------------------------------------------------
				# wind direction: unit = degrees (0..255)
				# convert to (0..360)
				#------------------------------------------------------------------------
				value = 360.0 * value / 255.0

			elif field == "wind_speed" or field == "wind_speed_mean":
				#------------------------------------------------------------------------
				# wind speed: unit = 1.1kph
				# convert to m/s
				#------------------------------------------------------------------------
				value = 100.0 * value / 3600.0
			
			elif field == "rain":
				#------------------------------------------------------------------------
				# unit = 0.01 in
				# convert to inches
				#------------------------------------------------------------------------
				value = value / 100.0

			elif field == "pressure":
				#------------------------------------------------------------------------
				# unit = 0.1 hPa
				# convert to hPa
				#------------------------------------------------------------------------
				value = value / 10.0
				
			self.values[field] = value

		#------------------------------------------------------------------------
		# if we have a callback set, call it now with our updated values.
		#------------------------------------------------------------------------
		if self.handler:
			self.handler(self.values)

def main():
	def handler(values):
		for key, value in list(values.items()):
			print(("%s - %f" % (key, value)))

	ultimeter = Ultimeter()
	ultimeter.handler = handler
	ultimeter.start()

	while True:
		time.sleep(0.1)

if __name__ == "__main__":
	main()
