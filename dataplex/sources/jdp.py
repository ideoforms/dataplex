from jdp import JDPServer
import argparse

from .source import Source

class SourceJDP (Source):
    def __init__(self,
                 property_names: list[str],
                 port: int = 48000):
        """
        Listen for JSON Datagram Protocol packets.

        Args:
            property_names (list[str]): The list of expected properties
            port (int): The port to listen on.
        """
        super().__init__()
        self.property_names = property_names
        self.server = JDPServer(port)
        self.server.start()
        self.server.add_callback(self.handle_data)
        self.data = {}

    def __str__(self):
        return ("JDP (%s)" % self.server)

    def handle_data(self, data: dict):
        for key, value in data.items():
            if key in self.property_names:
                # TODO: When receiving the output of ECDFNormaliser
                if isinstance(value, dict):
                    self.data[key] = value["value"]
                else:
                    self.data[key] = value

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
