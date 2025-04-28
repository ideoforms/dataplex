import time

from .destination import Destination
from .. import settings

class DestinationStdout (Destination):
    def __init__(self, property_names: list[str] = None):
        self.property_names = property_names
        self.phase = 0

    def __str__(self):
        return "Standard output"

    def send(self, data: dict):
        if self.property_names is None:
            self.property_names = list(data.keys())
            self.property_names = list(filter(lambda x: x not in ["time"], self.property_names))
            
        #--------------------------------------------------------------
        # add a heading every N lines for readability.
        #--------------------------------------------------------------
        if self.phase % settings.print_interval == 0:
            print(" ".join(["%-19s" % key for key in ["time"] + self.property_names]))

        self.phase = self.phase + 1

        #--------------------------------------------------------------
        # add a heading every N lines for readability.
        #--------------------------------------------------------------
        print("%-19s" % data["time"].strftime(settings.time_format), end=' ')

        for key in self.property_names:
            if data[key].value is not None:
                values = "[%.2f, %.2f]" % (data[key].value, data[key].normalised)
                print("%-19s" % values, end=' ')
            else:
                print("%-19s" % "", end=' ')
        print("")
