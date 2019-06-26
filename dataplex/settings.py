from dataplex.constants import *

debug = False

#----------------------------------------------------------------------
# I/O setup
#----------------------------------------------------------------------
sources = [ SOURCE_ULTIMETER ]
logfile = "logs/weather-data.%Y%m%d.%H%M%S.csv"
time_format = "%Y/%m/%d-%H:%M:%S"

#----------------------------------------------------------------------
# data reading options
#----------------------------------------------------------------------
csv_rate = 2
csv_sleep = 0.01

#----------------------------------------------------------------------
# sleep between pulling data from inputs
#----------------------------------------------------------------------
read_interval = 0.5

#----------------------------------------------------------------------
# lines between printing output
#----------------------------------------------------------------------
print_interval = 40

#----------------------------------------------------------------------
# how many history values shall we use for normalized/change values?
#----------------------------------------------------------------------
global_history = 5000
recent_history = 500

#----------------------------------------------------------------------
# do we wish to only output new values?
# can cause weirdness when reading from BWS due to reading latency.
#----------------------------------------------------------------------
uniq = False

#----------------------------------------------------------------------
# network config
#----------------------------------------------------------------------
jdp_destinations = [ ]
osc_destinations = [ "localhost:7400" ]

use_peak = {
    "battery"       : False,
    "temperature"   : False,
    "humidity"      : False,
    "wind_speed"    : False,
    "wind_dir"      : False,
    "rain"          : False,
    "sun"           : False
}

reverse_wind_dir = True

ultimeter_port = "/dev/cu.usbserial-FTELIIL0"
