import os
import csv
import time
import argparse

from .. import settings
# from .source import Source

class SourceCSV:
    def __init__(self,
                 path: str,
                 rate: float = 1.0):
        """
        Read a CSV file.

        Args:
            filename (str): The file path to read.
            rate (float, optional): The rate that data should be output, relative to the original
                                    time series. Defaults to 1.0.
        """
        self.filename = path
        self.fd = open(path, "r")
        self.rate = rate
        self.reader = csv.reader(self.fd)
        self.fields = next(self.reader)

        self.t0_log = None
        self.t0_time = None

        self.read()

    def __str__(self):
        return ("CSV (%s)" % os.path.basename(self.filename))

    def read(self):
        row = next(self.reader)
        row[0] = time.mktime(time.strptime(row[0], settings.time_format))
        row = dict([(self.fields[n], float(value)) for n, value in enumerate(row)])

        self.next_row = row

        return row

    def collect(self):
        """
        Block until the next reading is due, based on our CSV read rate.
        """

        if self.t0_log is None:
            #--------------------------------------------------------------
            # first field is always timestamp.
            #--------------------------------------------------------------
            self.t0_log = self.next_row["time"]
            self.t0_time = time.time()
            data = self.next_row
            self.read()
            return data

        log_delta = (self.next_row["time"] - self.t0_log) / float(self.rate)
        time_delta = time.time() - self.t0_time

        while time_delta <= log_delta:
            #------------------------------------------------------------------------
            # wait until we've hit the required time
            #------------------------------------------------------------------------
            time.sleep(0.01)
            time_delta = time.time() - self.t0_time

        while time_delta >= log_delta:
            #------------------------------------------------------------------------
            # TODO
            # skip over multiple readings
            #------------------------------------------------------------------------
            data = self.next_row
            self.read()
            log_delta = (self.next_row["time"] - self.t0_log) / float(self.rate)

        return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rate", type=float, default=1.0, help="Rate to output records relative to original CSV timestamps")
    parser.add_argument("input_path", help="CSV file to read")
    args = parser.parse_args()

    source = SourceCSV(args.input_path, rate=args.rate)

    while True:
        print(source.collect())
