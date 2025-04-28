#!/usr/bin/env python3

from dataplex import Dataplex
import argparse
import logging

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Run the dataplex I/O server")
    parser.add_argument("--verbose", "-v", help="Verbose output", action="store_true")
    args = parser.parse_args()

    log_level = "DEBUG" if args.verbose else "INFO"
    logging.basicConfig(level=log_level, format='%(asctime)s %(levelname)-8s %(message)s')

    print("Creating Dataplex server...")

    dataplex = Dataplex()
    
    # TODO: Have the default behaviour be to read as soon as a new frame arrives (if a "push" style source is present)
    dataplex.config.read_interval = 0.01
    dataplex.add_source(type="osc", port=8000, properties={"/imu/gyro": "vec3"})
    dataplex.add_destination(type="stdout")

    # TODO: Have property_names inferred automatically
    dataplex.add_destination(type="csv", property_names=["/imu/gyro_x", "/imu/gyro_y", "/imu/gyro_z"])
    dataplex.add_destination(type="scope", property_names=["/imu/gyro_x", "/imu/gyro_y", "/imu/gyro_z"])

    midi_mapper = dataplex.add_destination(type="midi", port_name="IAC Driver Bus 1")
    midi_mapper.add_mapping(property="/imu/gyro_x", cc=0)
    midi_mapper.add_mapping(property="/imu/gyro_y", cc=1)
    midi_mapper.add_mapping(property="/imu/gyro_z", cc=2)

    # midi_mapper.add_event(property="/imu/gyro_x",
    #                       when="value_crossed",
    #                       value=0.25,
    #                       debounce_time=0.1)

    # would be nice to be able to just do subplots(1, 3)
    
    dataplex.run()
