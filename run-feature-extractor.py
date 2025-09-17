#!/usr/bin/env python3

import json
import argparse
from jdp import JDPClient
from signalflow import *
from dataplex import Dataplex, DestinationStdout
from dataplex.utils import serialise_data

def main(args):
    import os
    os.environ["SIGNALFLOW_INPUT_DEVICE_NAME"] = "Loopback 2ch"
    os.environ["SIGNALFLOW_INPUT_DEVICE_NAME"] = "MacBook Pro Microphone"
    graph = AudioGraph()

    dataplex = Dataplex("config/audio-features.yaml")
    if args.verbose:
        dataplex.add_destination(DestinationStdout())

    if args.live:
        input_node = AudioIn(1)
    else:
        input_node = BufferPlayer(Buffer("audio/swam-sax-melody.aif"), loop=True)

    dataplex.get_source("audio").set_input_node(input_node)
    if args.playthrough:
        input_node.play()
            
    dataplex.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", help="Verbose output", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--playthrough", action="store_true")
    args = parser.parse_args()
    main(args)
