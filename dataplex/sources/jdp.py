import os
import jdp
import time
import argparse

from .. import settings
from .source import Source

class SourceJDP (Source):
    def __init__(self,
                 port: int = 48000):
        """
        Listen for JSON Datagram Protocol packets.

        Args:
            port (int): The port to listen on.
        """
        self.server = jdp.Server(port)
        self.server.start()
        self.server.add_callback(self.handle_data)
        self.data = None

    def __str__(self):
        return ("JDP (%s)" % self.server)

    def handle_data(self, data: dict):
        print("Received JDP: %s" % data)
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
