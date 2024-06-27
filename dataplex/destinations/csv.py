import os
import csv
import time

from .destination import Destination
from .. import settings

DEFAULT_CSV_PATH = "logs/data.%Y%m%d.%H%M%S.csv"

class DestinationCSV (Destination):
    def __init__(self, path_template: str = DEFAULT_CSV_PATH):
        #--------------------------------------------------------------
        # start writing to output logfile.
        #--------------------------------------------------------------
        self.path = time.strftime(path_template)

        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.logfd = open(self.path, "w")
        self.logwriter = csv.writer(self.logfd)
        self.logwriter.writerow(["time"] + settings.fields)

    def __str__(self):
        return "Log (%s)" % (os.path.basename(self.path))

    def send(self, data):
        #--------------------------------------------------------------
        # write the latest set of data to logfile.
        #--------------------------------------------------------------
        now = time.strftime(settings.time_format, time.localtime(data["time"]))
        self.logwriter.writerow([now] + ["%.3f" % data[key].value for key in settings.fields])

    def close(self):
        self.logfd.close()
