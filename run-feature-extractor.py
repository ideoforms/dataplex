#!/usr/bin/env python3

import json
import argparse
import numpy as np
from jdp import JDPClient
from signalflow import *
from isobar import frequency_to_midi_note
from dataplex import Dataplex
from dataplex.utils import serialise_data

def segment_contiguous(array, min_length=10):
    segmented_values = []
    if len(array) > 0:
        current_value = array[0]
        count = 1
        for value in array[1:]:
            if value == current_value:
                count += 1
            else:
                if count >= min_length:
                    segmented_values.append((float(current_value), count))
                current_value = value
                count = 1
        if count >= min_length:
            segmented_values.append((float(current_value), count))
    return segmented_values


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

        if np.all(feature_buffer[-20:].rms < 0.01):
            buffer_length = len(feature_buffer)
            if buffer_length > 10:
                notes = frequency_to_midi_note(feature_buffer.f0)
                notes = notes[notes != None]
                notes = np.round(notes)
                notes_segmented = segment_contiguous(notes, min_length=10)
                print(notes_segmented)

            feature_buffer.reset()

    dataplex = Dataplex("config/audio-features.yaml")
    dataplex.on_record_callback = on_record

    feature_buffer = dataplex.create_rolling_buffer()

    datascope_config = json.load(open("config/datascope-config.json"))
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
