import threading
import argparse
import logging
import time
from zeroconf import Zeroconf, ServiceBrowser
import socket, zmq, time

SERVICE_TYPE = "_dataplex._tcp.local."

logger = logging.getLogger("dataplex")

from .source import Source

class SourceZMQ(Source):
    def __init__(self,
                 property_names: list[str] = None):
        """
        Listen for data from ZMQ publishers discovered via Zeroconf.

        Args:
            property_names (list[str]): The list of expected properties
        """
        super().__init__()
        self.property_names = property_names
        self.data = {}

        self.sockets = {}
        self.ctx = zmq.Context()
        self.zc = Zeroconf()
        self.browser = ServiceBrowser(self.zc, SERVICE_TYPE, self)

        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        self.new_data_event = threading.Event()

    def __str__(self):
        return ("SourceZMQ (%d sources)" % len(self.data))

    def collect(self, blocking: bool = False):
        """
        Block until the next reading is due, based on our CSV read rate.
        """
        if blocking:
            self.new_data_event.wait()
            self.new_data_event.clear()
        
        if self.data:
            return self.data

    def add_service(self, zeroconf, type, name):
        # Zeroconf callback: new service discovered
        info = zeroconf.get_service_info(type, name)
        if not info:
            return
        ip = socket.inet_ntoa(info.addresses[0])
        port = info.port
        endpoint = f"tcp://{ip}:{port}"
        logger.info(f"SourceZMQ: Discovered service: {name} at {endpoint}")

        sock = self.ctx.socket(zmq.SUB)
        sock.connect(endpoint)
        sock.subscribe("")  # receive all topics
        self.sockets[name] = sock

    def remove_service(self, zeroconf, type, name):
        # Zeroconf callback: service removed
        logger.info(f"SourceZMQ: Service removed: {name}")
        sock = self.sockets.pop(name, None)
        if sock:
            sock.close()

    def update_service(self, zeroconf, type, name):
        pass

    def close(self):
        self.zc.close()

    def run(self):
        while True:
            for name, sock in list(self.sockets.items()):
                try:
                    msg = sock.recv_json(flags=zmq.NOBLOCK)
                    self.new_data_event.set()

                    for key, value in msg.items():
                        if (not self.property_names) or (key in self.property_names):
                            self.data[key] = value
                except zmq.Again:
                    # No data to read
                    pass
            time.sleep(0.01)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    source = SourceZMQ()

    while True:
        print(source.collect(blocking=True))
