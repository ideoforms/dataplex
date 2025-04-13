import jdp
import logging
import datetime

from .destination import Destination

logger = logging.getLogger(__name__)

class DestinationJDP (Destination):
    def __init__(self, host, port):
        self.client = jdp.Client((host, port))

    def serialise(self, value):
        """
        Serialise the value to encode as JSON.

        Args:
            value: The value to serialise.

        Returns:
            The JSON-encoded value. For ints, floats, and strings, this is the value itself.
            For datetime objects, this is a string in the format "YYYY-MM-DD HH:MM:SS.ssssss".
        """
        if isinstance(value, datetime.datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S.%f")
        else:
            return value

    def send(self, data):
        structure = {}
        for name, record in data.items():
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
                structure[name] = self.serialise(record)
        
        logger.debug("DestinationJDP: Send packet: %s" % structure)
        self.client.send(structure)
