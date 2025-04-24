#!/usr/bin/env python3

from jdp import JDPClient
import argparse
import json
from signalflow import *
from dataplex import Dataplex
from dataplex.utils import serialise_data


def main(args):
    graph = AudioGraph()
    client = JDPClient("localhost", 48000)
 
    def on_record(record):
        data = serialise_data(record)
        client.send({"data": {
            "rms": data["rms"]["value"],
            "f0": data["f0"]["value"],
            "spectral-flatness": data["spectral-flatness"]["value"],
            "spectral-flux": data["spectral-flux"]["value"],
            "spectral-centroid": data["spectral-centroid"]["value"],
            "levels": [
                data["rms"]["normalised"],
                data["f0"]["normalised"],
                data["spectral-flux"]["normalised"]
            ]
        }})

    dataplex = Dataplex(config_file="config/audio-features.yaml")
    dataplex.on_record_callback = on_record

    datascope_config = json.load(open("datascope-config.json"))
    client.send({"config": datascope_config})

    if not args.live:
        buffer = Buffer("audio/swam-sax-melody.aif")
        input_node = BufferPlayer(buffer, loop=True)
        dataplex.get_source("audio").set_input_node(input_node)
        if args.playthrough:
            input_node.play()
            
    dataplex.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--playthrough", action="store_true")
    args = parser.parse_args()
    main(args)
