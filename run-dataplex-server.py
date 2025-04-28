#!/usr/bin/env python3

import dataplex
import argparse
import logging
import time
import mido

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Run the dataplex I/O server")
    parser.add_argument("--verbose", "-v", help="Verbose output", action="store_true")
    parser.add_argument("--quiet", "-q", help="Quiet output", action="store_true")
    parser.add_argument("--sources", help="List of source names to select", type=str)
    parser.add_argument("-c", "--config", type=str, help="Path to JSON config file", default="config/config.json")
    args = parser.parse_args()

    log_level = "INFO"
    if args.quiet:
        log_level = "WARNING"
    elif args.verbose:
        log_level = "DEBUG"
    logging.basicConfig(level=log_level, format='%(asctime)s %(name)-24s %(levelname)-8s %(message)s')

    server = dataplex.Dataplex(config_path=args.config,
                               quiet=args.quiet,
                               sources=args.sources)
    output = mido.open_output("IAC Driver Bus 1")

    while True:
        server.next()
        value = server.data["lux"].normalised
        if value:
            msg = mido.Message("control_change", channel=0, control=0, value=int(value * 127))
            output.send(msg)
        time.sleep(0.1)
