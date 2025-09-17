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
    for dim in ["x", "y", "z"]:
        dataplex.add_processor("/imu/gyro_%s" % dim, "normalise", type="linear")
        dataplex.add_processor("/imu/accel_%s" % dim, "normalise", type="linear")
    dataplex.add_destination("stdout")

    # TODO: Have property_names inferred automatically
    dataplex.add_destination("csv", property_names=dataplex.property_names)
    dataplex.add_destination("scope", property_names=dataplex.property_names)

    midi_mapper = dataplex.add_destination("midi", port_name="IAC Driver Bus 1")
    midi_mapper.add_mapping("/imu/gyro_x", cc=0)
    midi_mapper.add_mapping("/imu/gyro_y", cc=1)
    midi_mapper.add_mapping("/imu/gyro_z", cc=2)

    midi_mapper.add_event("/imu/gyro_x", when="value_crossed", value=0.75, note=60)
    midi_mapper.add_event("/imu/gyro_x", when="value_crossed", value=0.6, note=55)
    midi_mapper.add_event("/imu/gyro_x", when="value_crossed", value=0.9, note=48)
    
    dataplex.run()
