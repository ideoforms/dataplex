import os
import csv
import time
import datetime

from .destination import Destination
from .. import settings

DEFAULT_CSV_PATH = "logs/data.%Y%m%d.%H%M%S.csv"

class DestinationCSV (Destination):
    def __init__(self,
                 field_names: list[str],
                 path_template: str = DEFAULT_CSV_PATH):
        #--------------------------------------------------------------
        # Format the CSV path template according to the current time
        #--------------------------------------------------------------
        self.field_names = field_names
        now = datetime.datetime.now()
        self.path = now.strftime(path_template)

        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.logfd = open(self.path, "w")
        self.logwriter = csv.writer(self.logfd)
        self.logwriter.writerow(["time"] + field_names)

    def __str__(self):
        return "Log (%s)" % (os.path.basename(self.path))

    def send(self, data: dict):
        #--------------------------------------------------------------
        # write the latest set of data to logfile.
        #--------------------------------------------------------------
        now = time.strftime(settings.time_format, time.localtime(data["time"]))
        self.logwriter.writerow([now] + ["%.3f" % data[key].value for key in self.field_names])

    def close(self):
        self.logfd.close()
