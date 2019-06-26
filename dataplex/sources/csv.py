#------------------------------------------------------------------------
# needed to import a package whose name clashes with my own:
# http://stackoverflow.com/questions/4816595/how-do-i-import-a-module-whose-name-clashes-with-a-module-in-my-package
#------------------------------------------------------------------------
 

import os
import csv
import time

from .. import settings
from .source import Source

class SourceCSV (Source):
    def __init__(self, filename, rate = 1.0):
        #--------------------------------------------------------------
        # set up our file reader.
        #--------------------------------------------------------------
        self.filename = filename
        self.fd = open(filename, "r")
        self.rate = rate
        self.reader = csv.reader(self.fd)
        self.fields = next(self.reader)

        self.t0_log = None
        self.t0_time = None

        self.read()

    def __str__(self):
        return("CSV (%s)" % os.path.basename(self.filename))

    def read(self):
        row = next(self.reader)
        row[0] = time.mktime(time.strptime(row[0], settings.time_format))
        row = dict([ (self.fields[n], float(value)) for n, value in enumerate(row) ])

        self.next_row = row

        return row

    def collect(self):
        """ Block until the next reading is due, based on our CSV read rate. """

        if self.t0_log is None:
            #--------------------------------------------------------------
            # first field is always timestamp.
            #--------------------------------------------------------------
            self.t0_log  = self.next_row["time"]
            self.t0_time = time.time()
            data = self.next_row
            self.read()
            return data

        log_delta = (self.next_row["time"] - self.t0_log) / float(settings.csv_rate)
        time_delta = time.time() - self.t0_time

        while time_delta <= log_delta:
            #------------------------------------------------------------------------
            # wait until we've hit the required time
            #------------------------------------------------------------------------
            time.sleep(0.1)
            time_delta = time.time() - self.t0_time

        while time_delta >= log_delta:
            #------------------------------------------------------------------------
            # TODO
            # skip over multiple readings
            #------------------------------------------------------------------------
            data = self.next_row
            self.read()
            log_delta = (self.next_row["time"] - self.t0_log) / float(settings.csv_rate)

        return data


    @property
    def should_log(self):
        return False
