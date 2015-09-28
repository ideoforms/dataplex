from meteolog.constants import *

fields = [ "wind_speed", "wind_dir", "temperature", "humidity", "pressure", "rain", "sun" ]

debug = False

#----------------------------------------------------------------------
# I/O setup
#----------------------------------------------------------------------
sources = [ SOURCE_ULTIMETER, SOURCE_WEBCAM ]
sources = [ SOURCE_WEBCAM ]
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
# lines between printing output
#----------------------------------------------------------------------
print_interval = 40

#----------------------------------------------------------------------
# how many history values shall we use for normalized/change values?
#----------------------------------------------------------------------
global_history = 500
recent_history = 20

#----------------------------------------------------------------------
# do we wish to only output new values?
# can cause weirdness when reading from BWS due to reading latency.
#----------------------------------------------------------------------
uniq = False

#----------------------------------------------------------------------
# network config
#----------------------------------------------------------------------
osc_destinations = [ "localhost:7400", "localhost:6100", "localhost:58000", "localhost:58001" ]
# osc_destinations = [ "localhost:58001", "localhost:58000" ]

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

