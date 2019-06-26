import os
import csv
import sys
import math
import time
import getopt

from . import settings

from .constants import *
from .sources import *
from .destinations import *
from .ecdf import ECDFNormaliser


class Server:
    def __init__(self):
        #--------------------------------------------------------------
        # unbuffered stdout for launchctl logging
        #--------------------------------------------------------------
        # (not using right now)
        # sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
        #--------------------------------------------------------------
        self.parse_args()

        #--------------------------------------------------------------
        # init: SOURCE
        # create our collector object, adopting whatever mode is
        # selected in settings.sources
        #--------------------------------------------------------------
        self.sources = []
        for source in settings.sources:
            if source == SOURCE_PAKBUS:
                self.sources.append(SourcePakbus())
            elif source == SOURCE_ULTIMETER:
                self.sources.append(SourceUltimeter(settings.ultimeter_port))
            elif source == SOURCE_CSV:
                self.sources.append(SourceCSV(settings.csv_file))
            elif source == SOURCE_WEBCAM:
                self.sources.append(SourceWebcam())
            elif source == SOURCE_AUDIO:
                self.sources.append(SourceAudio())
            elif source == SOURCE_METOFFICE:
                self.sources.append(SourceMetOffice())

        #--------------------------------------------------------------
        # init: DATA
        #--------------------------------------------------------------
        settings.fields = []
        for source in self.sources:
            settings.fields += source.fields
        settings.fields = [n for n in settings.fields if n != "time"]

        self.data = {}

        for source in self.sources:
            for name in source.fields:
                item = ECDFNormaliser(settings.global_history, settings.recent_history)
                self.data[name] = item

        #--------------------------------------------------------------
        # init: DESTINATIONS
        # we always want to transmit over OSC. set this up now.
        # support specifying multiple OSC ports for multicast.
        #--------------------------------------------------------------
        self.destinations = []

        #--------------------------------------------------------------
        # by default, output to a logfile and stdout.
        #--------------------------------------------------------------
        if [source for source in self.sources if source.should_log]:
            self.destinations.append(DestinationLog())
        self.destinations.append(DestinationStdout())

        #--------------------------------------------------------------
        # we currently always want to transmit over OSC. set this up now.
        # support specifying multiple OSC ports for multicast.
        #--------------------------------------------------------------
        for destination_address in settings.osc_destinations:
            osc_host, osc_port = destination_address.split(":")
            destination = DestinationOSC(osc_host, int(osc_port))
            self.destinations.append(destination)

        for destination_address in settings.jdp_destinations:
            osc_host, osc_port = destination_address.split(":")
            destination = DestinationJDP(osc_host, int(osc_port))
            self.destinations.append(destination)

        print("Sources: ")
        for source in self.sources:
            print(" - %s" % source)
        print("Destinations: ")
        for destination in self.destinations:
            print(" - %s" % destination)

    def run(self):
        try:
            while True:
                #--------------------------------------------------------------
                # Infinite loop: pull new data and record. 
                #--------------------------------------------------------------
                try:
                    record = {}
                    for source in self.sources:
                        record.update(source.collect())

                except StopIteration:
                    #--------------------------------------------------------------
                    # TODO: we should throw this when a CSV file has finished
                    #--------------------------------------------------------------
                    print("Source %s ended stream." % self.source)
                    break

                #--------------------------------------------------------------
                # Set time value, and record any values that are present.
                #--------------------------------------------------------------
                if "time" in record:
                    self.data["time"] = record["time"]
                else:
                    self.data["time"] = time.time()

                #--------------------------------------------------------------
                # If we've not got any data except time, skip this iteration.
                #--------------------------------------------------------------
                if len(record) == 1:
                    continue

                #--------------------------------------------------------------
                # Register new data.
                #--------------------------------------------------------------
                for key in self.data:
                    if key == "time":
                        continue
                    if key in record and record[key] is not None:
                        self.data[key].register(record[key])

                #--------------------------------------------------------------
                # If any of our data sources are not yet set (returning None),
                # skip this iteration.
                #--------------------------------------------------------------
                missing_data = False
                for key in settings.fields:
                    if self.data[key].value is None:
                        print("Awaiting data for %s..." % key)
                        missing_data = True
                #--------------------------------------------------------------
                # Skip this iteration and retry.
                #--------------------------------------------------------------
                if missing_data:
                    time.sleep(0.1)
                    continue

                #--------------------------------------------------------------
                # send our current data to each destination
                #--------------------------------------------------------------
                for destination in self.destinations:
                    destination.send(self.data)

                #--------------------------------------------------------------
                # send our current data to each destination
                #--------------------------------------------------------------
                if settings.sources == [ "SOURCE_CSV" ]:
                    time.sleep(0.01)
                else:
                    time.sleep(settings.read_interval)

        except KeyboardInterrupt:
            #--------------------------------------------------------------
            # die silently.
            #--------------------------------------------------------------
            print("Killed by ctrl-c")
            pass

    def parse_args(self):
        def usage():
            print("Usage: %s [-f <csv_file>] [-s]" % sys.argv[0])
            print("  -p: input mode pakbus (Campbell Scientific)")
            print("  -u: input mode ultimeter (Peet Bros)")
            print("  -f: input mode .csv file")
            print("  -r: rate of CSV reading")
            print("  -d: debug output")
            print("  -n: disable smoothing")
            print("  -h: show this help")

            sys.exit(1)

        #--------------------------------------------------------------
        # pull commandline opts and update settings appropriately.
        #--------------------------------------------------------------
        try:
            flags, args = getopt.getopt(sys.argv[1:], "f:pudnr:h")
        except:
            usage()

        for key, value in flags:
            if key == "-f":
                settings.sources = [ SOURCE_CSV ]
                settings.csv_file = value
            elif key == "-p":
                settings.sources = [ SOURCE_PAKBUS ]
            elif key == "-u":
                settings.sources = [ SOURCE_ULTIMETER ]
            elif key == "-d":
                settings.debug = True
            elif key == "-r":
                settings.csv_rate = float(value)
            elif key == "-n":
                for key, value in list(settings.smoothing.items()):
                    settings.smoothing[key] = 0.0
            elif key == "-h":
                usage()
            

