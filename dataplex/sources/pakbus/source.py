from . import pakbus
from ..source import Source

#----------------------------------------------------------------------
# serial setup
#----------------------------------------------------------------------
PAKBUS_NODEID = 0x01
PAKBUS_MYNODEID = 0x802
PAKBUS_DEV = "/dev/cu.usbserial-FTGOJL30"

#----------------------------------------------------------------------
# translations from BWS names to shortnames
#----------------------------------------------------------------------
PAKBUS_property_names = {
    "Batt_Volt" : "battery",
    "AirTC"     : "temperature",
    "RH"        : "humidity",
    "WS_ms"     : "wind_speed",
    "WindDir"   : "wind_dir",
    "Rain_mm"   : "rain",
    "Solar_W"   : "sun",

    "TdC    "   : "dewpoint",
    "WindRun"   : "windrun",
    "Solar_kJ"  : "sunkj",
}

FIELDS = [ "temperature", "humidity", "wind_speed", "wind_dir", "rain", "sun" ]

class SourcePakbus(Source):
	def __init__(self):
		#--------------------------------------------------------------
		# if we're in serial mode, connect to pakbus port.
		#--------------------------------------------------------------
		try:
			self.serial = pakbus.open_serial(settings.PAKBUS_DEV)
		except Exception as e:
			print("Couldn't open serial device %s (%s)" % (settings.pakbus_dev, e))
			sys.exit(1)

		msg = pakbus.ping_node(self.serial, PAKBUS_NODEID, PAKBUS_MYNODEID)
		if not msg:
			raise Warning('no reply from PakBus node 0x%.3x' % PAKBUS_NODEID)

	def collect(self):
		data = {}

		data["time"] = int(time.time())

		for name in FIELDS:
			longname = ([n for n in list(PAKBUS_property_names.keys()) if PAKBUS_property_names[n] == name])[0]

			#--------------------------------------------------------------
			# get each of our parameters from the device.
			#--------------------------------------------------------------
			value = pakbus.getvalues(self.serial, PAKBUS_NODEID, PAKBUS_MYNODEID, "Public", 'IEEE4B', longname)
			value = value[0]

			data[name] = value

		return data

	def close(self):
		#--------------------------------------------------------------
		# say goodbye and close socket.
		#--------------------------------------------------------------
		pakbus.send(self.serial, pakbus.pkt_bye_cmd(PAKBUS_NODEID, PAKBUS_MYNODEID))
		self.serial.close()

	@property
	def fields(self):
		return FIELDS
