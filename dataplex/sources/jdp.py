import os
import jdp
import time
import argparse

from .. import settings
from .source import Source

class SourceJDP:
    def __init__(self,
                 field_names: list[str],
                 port: int = 48000):
        """
        Listen for JSON Datagram Protocol packets.

        Args:
            field_names (list[str]): The list of expected fields
            port (int): The port to listen on.
        """
        self.fields = field_names
        self.server = jdp.Server(port)
        self.server.start()
        self.server.add_callback(self.handle_data)
        self.data = None

    def __str__(self):
        return ("JDP (%s)" % self.server)

    def handle_data(self, data: dict):
        self.data = data

    def collect(self, blocking: bool = False):
        """
        Block until the next reading is due, based on our CSV read rate.
        """
        if self.data:
            return self.data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default=48000, help="Port to listen on")
    args = parser.parse_args()

    source = SourceJDP(args.port)

    while True:
        print(source.collect())
