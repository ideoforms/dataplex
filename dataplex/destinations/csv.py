import os
import csv
import logging
import datetime

from .destination import Destination

logger = logging.getLogger(__name__)

DEFAULT_CSV_PATH = "logs/data.%Y%m%d.%H%M%S.csv"

class DestinationCSV (Destination):
    def __init__(self,
                 property_names: list[str],
                 path_template: str = DEFAULT_CSV_PATH):
        #--------------------------------------------------------------
        # Format the CSV path template according to the current time
        #--------------------------------------------------------------
        self.property_names = property_names
        now = datetime.datetime.now()
        self.path = now.strftime(path_template)

        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.logfd = open(self.path, "w")
        self.logwriter = csv.writer(self.logfd)
        self.logwriter.writerow(["time"] + property_names)

    def __str__(self):
        return "CSV (%s)" % (os.path.basename(self.path))

    def send(self, data: dict):
        #--------------------------------------------------------------
        # write the latest set of data to logfile.
        #--------------------------------------------------------------
        now = str(data["time"])
        row = [now] + ["%.3f" % data[key].value for key in self.property_names]
        self.logwriter.writerow(row)
        logger.debug("DestinationCSV: Log row: %s" % row)

    def close(self):
        self.logfd.close()
