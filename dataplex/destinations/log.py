import os
import csv
import time

from .destination import Destination
from .. import settings

class DestinationLog (Destination):
    def __init__(self, path_template=settings.logfile):
        #--------------------------------------------------------------
        # start writing to output logfile.
        #--------------------------------------------------------------
        self.path = time.strftime(path_template)
        self.logfd = open(self.path, "w")
        self.logwriter = csv.writer(self.logfd)
        self.logwriter.writerow([ "time" ] + settings.fields)

    def __str__(self):
        return "Log (%s)" % (os.path.basename(self.path))

    def send(self, data):
        #--------------------------------------------------------------
        # write the latest set of data to logfile.
        #--------------------------------------------------------------
        # for key in settings.fields:
        #    print "%s - %s" % (key, data[key].value)
        now = time.strftime(settings.time_format, time.localtime(data["time"]))
        self.logwriter.writerow([ now ] + [ "%.3f" % data[key].value for key in settings.fields ])

    def close(self):
        self.logfd.close()
