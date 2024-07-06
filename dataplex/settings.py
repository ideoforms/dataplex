#----------------------------------------------------------------------
# I/O setup
#----------------------------------------------------------------------
time_format = "%Y/%m/%d-%H:%M:%S"

#----------------------------------------------------------------------
# sleep between pulling data from inputs
#----------------------------------------------------------------------
read_interval = 0.25

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
global_history_length = 3600
recent_history_length = 360

use_peak = {
    "battery": False,
    "temperature": False,
    "humidity": False,
    "wind_speed": False,
    "wind_dir": False,
    "rain": False,
    "sun": False
}

