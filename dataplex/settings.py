debug = False

#----------------------------------------------------------------------
# I/O setup
#----------------------------------------------------------------------
sources = ["ultimeter"]
logfile = "logs/weather-data.%Y%m%d.%H%M%S.csv"
time_format = "%Y/%m/%d-%H:%M:%S"

#----------------------------------------------------------------------
# data reading options
#----------------------------------------------------------------------
csv_file = "logs/weather-data.melbourne-cup-day-1.20151029.061205.csv"
csv_rate = 1
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
# 3600 values at ~1200bpm is half an hour's worth of readings,
# so if rain is registered at one tick, the normalised value will
# remain at 1.0 for half an hour.
#----------------------------------------------------------------------
global_history = 3600
recent_history = 360

#----------------------------------------------------------------------
# do we wish to only output new values?
# can cause weirdness when reading from BWS due to reading latency.
#----------------------------------------------------------------------
uniq = False

#----------------------------------------------------------------------
# network config
#----------------------------------------------------------------------
jdp_destinations = []
osc_destinations = ["127.0.0.1:7400"]

use_peak = {
    "battery": False,
    "temperature": False,
    "humidity": False,
    "wind_speed": False,
    "wind_dir": False,
    "rain": False,
    "sun": False
}

reverse_wind_dir = True

ultimeter_port = "/dev/cu.usbserial-FTELIIL0"
