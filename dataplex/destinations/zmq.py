import jdp
import logging
from zeroconf import Zeroconf, ServiceInfo
import socket
import zeroconf
import zmq
import time

from .destination import Destination

logger = logging.getLogger(__name__)

SERVICE_TYPE = "_dataplex._tcp.local."
SERVICE_NAME = "Weather Station A._dataplex._tcp.local."
PUB_PORT = 5556

#--------------------------
# Robust LAN IP detection
#--------------------------
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()

    return ip


class DestinationZMQ (Destination):
    def __init__(self,
                 property_names: list[str] = None):
        self.property_names = property_names
        public_ip = get_local_ip()
        logger.info(f"Detected LAN IP: {public_ip}")

        #--------------------------------------------------------------------------------
        # ZeroMQ publisher
        #--------------------------------------------------------------------------------
        self.ctx = zmq.Context()
        self.pub = self.ctx.socket(zmq.PUB)
        self.pub.bind(f"tcp://*:{PUB_PORT}")

        #--------------------------------------------------------------------------------
        # Zeroconf advertisement
        #--------------------------------------------------------------------------------
        self.zeroconf = Zeroconf()
        self.service = ServiceInfo(type_=SERVICE_TYPE,
                                   name=SERVICE_NAME,
                                   addresses=[socket.inet_aton(public_ip)],
                                   port=PUB_PORT,
                                   properties={"topics": "temp,humidity,wind"},
                                   server=f"{socket.gethostname()}.local.")
        self.zeroconf.register_service(self.service)
        logger.info(f"Service advertised via Zeroconf at {public_ip}:{PUB_PORT}")

    def send(self, data):
        self.pub.send_json(data)

    def close(self):
        self.zeroconf.unregister_service(self.service)
        self.zeroconf.close()
        self.pub.close()
        self.ctx.term()

if __name__ == "__main__":
    destination = DestinationZMQ()
    try:
        while True:
            data = {"temp": 22.3, "humidity": 0.54, "wind": 3.5}
            destination.send(data)
            logger.info(f"DestinationZMQ: Sent: {data}")
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        destination.close()