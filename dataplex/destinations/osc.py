import time
from pythonosc.udp_client import SimpleUDPClient

from .destination import Destination

class DestinationOSC (Destination):
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.osc_client = SimpleUDPClient(host, port)

    def __str__(self):
        return "OSC (%s:%d)" % (self.host, self.port)

    def send_message(self, address, *args):
        self.osc_client.send_message(address, args)

    def send(self, data):
        #--------------------------------------------------------------
        # first, send current time in hours and minutes 
        #--------------------------------------------------------------
        self.send_message("/data/time", int(data["time"].timestamp()))

        for name, record in list(data.items()):
            if name == "time":
                continue

            #--------------------------------------------------------------
            # send OSC message.
            # for some variables, we might want to always send out our
            # peak value (eg, rain).
            #--------------------------------------------------------------
            # if settings.use_peak[name]:
            #    value = self.data_max[name]

            try:
                value = float(record)

                if value is not None:
                    self.send_message("/data/%s" % name, value)
            except IndexError:
                #------------------------------------------------------------------------
                # haven't yet got any data for this field (might not have read
                # anything yet)
                #------------------------------------------------------------------------
                pass

