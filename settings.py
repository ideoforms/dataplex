import collector

debug = False

#----------------------------------------------------------------------
# I/O setup
#----------------------------------------------------------------------
mode = collector.MODE_ULTIMETER
# mode = collector.MODE_PAKBUS
logfile = "logs/weather-data.%Y%m%d.%H%M%S.csv"
time_format = "%Y/%m/%d-%H:%M:%S"

#----------------------------------------------------------------------
# data reading options
#----------------------------------------------------------------------
csv_rate = 1
csv_sleep = 0.05

#----------------------------------------------------------------------
# sleep between pulling data from serial
#----------------------------------------------------------------------
serial_sleep = 0.5

#----------------------------------------------------------------------
# how many history values shall we use for normalized/change values?
#----------------------------------------------------------------------
histsize = 500

#----------------------------------------------------------------------
# do we wish to only output new values?
# can cause weirdness when reading from BWS due to reading latency.
#----------------------------------------------------------------------
uniq = False

#----------------------------------------------------------------------
# network config
#----------------------------------------------------------------------
osc_destinations = [ "localhost:7400", "localhost:6100", "localhost:8000", "localhost:58000" ]

#----------------------------------------------------------------------
# serial setup
#----------------------------------------------------------------------
pakbus_nodeid = 0x01
pakbus_mynodeid = 0x802
pakbus_dev = "/dev/cu.usbserial-FTGOJL30"

#----------------------------------------------------------------------
# translations from BWS names to shortnames
#----------------------------------------------------------------------
translations = {
	"Batt_Volt" : "battery",
	"AirTC" 	: "temperature",
	"RH" 		: "humidity",
	"WS_ms" 	: "wind_speed",
	"WindDir"	: "wind_dir",
	"Rain_mm"	: "rain",
	"Solar_W"	: "sun",

	"TdC	" 	: "dewpoint",
	"WindRun" 	: "windrun",
	"Solar_kJ" 	: "sunkj",
}

#----------------------------------------------------------------------
# fields to read
#----------------------------------------------------------------------
if mode == collector.MODE_ULTIMETER:
	fields = [ "temperature", "humidity", "wind_speed", "wind_dir", "rain" ]
else:
	fields = [ "temperature", "humidity", "wind_speed", "wind_dir", "rain", "sun" ]

smoothing = {
	"battery"		: 0.0,
	"temperature"	: 0.0,
	"humidity"		: 0.0,
	"wind_speed"	: 0.9,
	"wind_dir"		: 0.5,
	"rain"			: 0.0,
	"sun"			: 0.5
}

use_peak = {
	"battery"		: False,
	"temperature"	: False,
	"humidity"		: False,
	"wind_speed"	: False,
	"wind_dir"		: False,
	"rain"			: False,
	"sun"			: False
}

reverse_wind_dir = True
