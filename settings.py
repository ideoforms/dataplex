import collector

debug = False

#----------------------------------------------------------------------
# I/O setup
#----------------------------------------------------------------------
mode = collector.MODE_ULTIMETER
logfile = "logs/weather-data.%Y%m%d.%H%M%S.csv"
time_format = "%Y/%m/%d-%H:%M:%S"

#----------------------------------------------------------------------
# data reading options
#----------------------------------------------------------------------
csv_rate = 100
csv_sleep = 0.1

#----------------------------------------------------------------------
# sleep between pulling data from serial
#----------------------------------------------------------------------
serial_sleep = 0.5
# smoothing = 0.00

#----------------------------------------------------------------------
# how many history values shall we use for normalized/change values?
#----------------------------------------------------------------------
histsize = 100

#----------------------------------------------------------------------
# do we wish to only output new values?
# can cause weirdness when reading from BWS due to reading latency.
#----------------------------------------------------------------------
uniq = False

#----------------------------------------------------------------------
# network config
#----------------------------------------------------------------------
osc_host = "localhost"
osc_port = 7400

#----------------------------------------------------------------------
# serial setup
#----------------------------------------------------------------------
pakbus_nodeid = 0x01
pakbus_mynodeid = 0x802
pakbus_dev = "/dev/cu.usbserial-FTELIIL0"

#----------------------------------------------------------------------
# translations from BWS names to shortnames
#----------------------------------------------------------------------
translations = {
	"Batt_Volt" : "battery",
	"AirTC" 	: "temperature",
	"RH" 		: "humidity",
	"WS_ms" 	: "windspeed",
	"WindDir"	: "winddir",
	"Rain_mm"	: "rain",
	"Solar_W"	: "sun",

	"TdC	" 	: "dewpoint",
	"WindRun" 	: "windrun",
	"Solar_kJ" 	: "sunkj",
}

#----------------------------------------------------------------------
# fields to read
#----------------------------------------------------------------------
fields = [ "temperature", "humidity", "windspeed", "winddir", "sun", "rain" ]

smoothing = {
	"battery"		: 0.0,
	"temperature"	: 0.0,
	"humidity"		: 0.0,
	"windspeed"		: 0.9,
	"winddir"		: 0.5,
	"rain"			: 0.0,
	"sun"			: 0.5
}

use_peak = {
	"battery"		: False,
	"temperature"	: False,
	"humidity"		: False,
	"windspeed"		: False,
	"winddir"		: False,
	# "rain"			: True,
	# switched off for summer school 
	"rain"			: False,
	"sun"			: False
	
}

# smoothing = 0.99
