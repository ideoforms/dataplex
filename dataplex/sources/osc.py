from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
import argparse
import threading
import logging


logger = logging.getLogger("dataplex")

from .source import Source

class SourceOSC (Source):
    def __init__(self,
                 port: int = 8000,
                 properties: dict = None):
        """
        Listen for OSC datagrams.

        Formats:
         - /<field_name> <value>        - assigns value to field_name
         - /data/<field_name> <value>   - assigns value to field_name
         - 

        Args:
            property_names (list[str]): The list of expected fields
            port (int): The port to listen on.
        """
        super().__init__()
        if properties:
            self.property_names = list(properties.keys())

        self.data = {}
        self.port = port

    def __str__(self):
        return ("OSC (port %d)" % self.port)
    
    def _osc_handler(self, address: str, *args):
        """
        Handle incoming OSC messages.
        """
        logger.debug("Received OSC message: %s %s" % (address, args))
        if address.startswith("/data/"):
            property_name = address[5:]
        else:
            property_name = address[0:]

        if len(args) == 1:
            value = args[0]
            self.data[property_name] = value
        elif len(args) > 1 and len(args) < 4:
            arg_suffixes = ["x", "y", "z"]
            for i, value in enumerate(args):
                property_subname = "%s_%s" % (property_name, arg_suffixes[i])
                self.data[property_subname] = value
        elif len(args) > 3:
            print("Too many arguments for field %s" % property_name)
        else:
            self.data[property_name] = None

    def start(self):
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
    
    def run(self):
        dispatcher = Dispatcher()
        dispatcher.set_default_handler(self._osc_handler)

        server = BlockingOSCUDPServer(("0.0.0.0", self.port), dispatcher)
        server.serve_forever()

    def collect(self, blocking: bool = False):
        if self.data:
            return self.data


if __name__ == "__main__":
    import time

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default=12000, help="Port to listen on")
    args = parser.parse_args()

    source = SourceOSC(args.port)
    print("Listening on port %d" % args.port)

    while True:
        print(source.collect())
        time.sleep(0.1)