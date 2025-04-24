import jdp
import logging
from ..utils import serialise_data

from .destination import Destination

logger = logging.getLogger(__name__)


class DestinationJDP (Destination):
    def __init__(self, host, port):
        self.client = jdp.JDPClient(host, port)

    def send(self, data):
        structure = serialise_data(data)
        logger.debug("DestinationJDP: Send packet: %s" % structure)
        self.client.send(structure)
