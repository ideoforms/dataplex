import jdp
import logging

from .destination import Destination

logger = logging.getLogger(__name__)

class DestinationJDP (Destination):
    def __init__(self, host, port):
        self.client = jdp.Client((host, port))

    def send(self, data):
        structure = {}
        for name in list(data.items()):
            try:
                #------------------------------------------------------------------------
                # For ECDFNormaliser objects, pass their dictionary of properties.
                #------------------------------------------------------------------------
                structure[name] = {
                    "value" : record.value,
                    "normalised" : record.normalised,
                    "previous_value" : record.previous_value,
                    "previous_normalised" : record.previous_normalised,
                    "change" : record.change
                }
            except AttributeError:
                #------------------------------------------------------------------------
                # For scalar fields (eg time), simply pass their value.
                #------------------------------------------------------------------------
                structure[name] = record
        
        logger.debug("DestinationJDP: Send packet: %s" % structure)
        self.client.send(structure)
