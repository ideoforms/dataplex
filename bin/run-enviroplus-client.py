#!/usr/bin/env python3

import dataplex
import logging
import pprint
import time

from bme280 import BME280 # Temperature, pressure, humidity
from smbus2 import SMBus
from ltr559 import LTR559 # Light
from enviroplus import gas # Gas
from pms5003 import PMS5003, ReadTimeoutError  # Particulate matter

ltr559 = LTR559()
bus = SMBus(1)
bme280 = BME280(i2c_dev=bus)
pms5003 = PMS5003()

def get_all_data():
    data = {}
    data["temperature"] = bme280.get_temperature()
    data["pressure"] = bme280.get_pressure()
    data["humidity"] = bme280.get_humidity()
    data["lux"] = ltr559.get_lux()
    gas_readings = gas.read_all()
    data["gas_nh3"] = gas_readings.nh3
    data["gas_oxidising"] = gas_readings.oxidising
    data["gas_reducing"] = gas_readings.reducing
    pm_readings = pms5003.read()
    # data["pm_1"] = float(pm_readings.pm_ug_per_m3(1))
    # data["pm_25"] = float(pm_readings.pm_ug_per_m3(2.5))
    # data["pm_10"] = float(pm_readings.pm_ug_per_m3(10))
    data["pm_1l_03"] = float(pm_readings.pm_per_1l_air(0.3))
    data["pm_1l_05"] = float(pm_readings.pm_per_1l_air(0.5))
    data["pm_1l_1"] = float(pm_readings.pm_per_1l_air(1.0))
    data["pm_1l_2"] = float(pm_readings.pm_per_1l_air(2.5))
    data["pm_1l_5"] = float(pm_readings.pm_per_1l_air(5))
    data["pm_1l_10"] = float(pm_readings.pm_per_1l_air(10))
    return data

def main():
    client = dataplex.Client(server_host="192.168.2.1",
                             server_port=48000)
    while True:
        data = get_all_data()
        pprint.pprint(data)
        client.send(data)
        time.sleep(0.1)

if __name__ == "__main__":
    main()
