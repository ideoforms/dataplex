import os
import time
import argparse
import pandas as pd
import datetime

from .source import Source
from ..settings import timestamp_field_name

class SourceCSV (Source):
    def __init__(self,
                 path: str,
                 rate: float = 1.0,
                 property_names: list[str] = None):
        """
        Read a CSV file.

        Args:
            filename (str): The file path to read.
            rate (float, optional): The rate that data should be output, relative to the original
                                    time series. Defaults to 1.0.
        """
        super().__init__()

        self.filename = path
        self.rate = rate

        df = pd.read_csv(path, parse_dates=[timestamp_field_name])
        self.records = iter(df.to_dict(orient="records"))
        self.data = None

        if property_names:
            for property_name in property_names:
                if property_name not in df.columns:
                    raise ValueError("Specified property name not found in CSV: %s" % property_name)
            self.property_names = property_names
        else:
            self.property_names = list(df.columns)

        self.t0_log = None
        self.t0_time = None

        self.read()

    def __str__(self):
        return ("CSV (%s)" % os.path.basename(self.filename))

    def read(self):
        self.next_row = next(self.records)
        return self.next_row

    def collect(self, blocking: bool = False):
        """
        Block until the next reading is due, based on our CSV read rate.
        """

        if self.t0_log is None:
            #------------------------------------------------------------------------
            # If no rows have been read, process the first row to set our initial
            # time.
            #------------------------------------------------------------------------
            self.data = next(self.records)
            self.t0_log = self.data[timestamp_field_name]
            self.t0_time = datetime.datetime.now()
            self.next_row = next(self.records)

        log_delta = (self.next_row[timestamp_field_name] - self.t0_log).total_seconds() / float(self.rate)
        time_delta = (datetime.datetime.now() - self.t0_time).total_seconds()

        if blocking:
            while time_delta <= log_delta:
                #------------------------------------------------------------------------
                # wait until we've hit the required time
                #------------------------------------------------------------------------
                time.sleep(0.01)
                time_delta = (datetime.datetime.now() - self.t0_time).total_seconds()

        while time_delta >= log_delta:
            #------------------------------------------------------------------------
            # TODO
            # skip over multiple readings
            #------------------------------------------------------------------------
            self.data = self.next_row
            self.next_row = next(self.records)
            log_delta = (self.next_row[timestamp_field_name] - self.t0_log).total_seconds() / float(self.rate)

        return self.data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rate", type=float, default=1.0, help="Rate to output records relative to original CSV timestamps")
    parser.add_argument("input_path", help="CSV file to read")
    args = parser.parse_args()

    source = SourceCSV(args.input_path, rate=args.rate)

    while True:
        print(source.collect())
