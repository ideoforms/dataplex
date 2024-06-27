import time
import argparse

from . import settings

from .sources import SourceAudio, SourceCSV, SourcePakbus, SourceUltimeter, SourceWebcam
from .destinations import DestinationJDP, DestinationCSV, DestinationOSC, DestinationStdout
from .statistics.ecdf import ECDFNormaliser


class Server:
    def __init__(self):
        #--------------------------------------------------------------
        # init: SOURCE
        # create our collector object, adopting whatever mode is
        # selected in settings.sources
        #--------------------------------------------------------------
        self.sources = []
        for source in settings.sources:
            if source == "pakbus":
                self.sources.append(SourcePakbus())
            elif source == "ultimeter":
                self.sources.append(SourceUltimeter(settings.ultimeter_port))
            elif source == "csv":
                self.sources.append(SourceCSV(settings.csv_file))
            elif source == "webcam":
                self.sources.append(SourceWebcam())
            elif source == "audio":
                self.sources.append(SourceAudio())
            else:
                raise ValueError(f"Source ID not known: f{source}")

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
                item = ECDFNormaliser(settings.global_history,
                                      settings.recent_history)
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
            self.destinations.append(DestinationCSV())
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
                if settings.sources == ["csv"]:
                    time.sleep(0.01)
                else:
                    time.sleep(settings.read_interval)

        except KeyboardInterrupt:
            print("Killed by ctrl-c")
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Run the dataplex I/O server")
    parser.add_argument("--csv-rate", type=float, help="Rate of reading CSV records versus realtime", default=1.0)
    parser.add_argument("--verbose", "-v", help="Verbose output", action="store_true")
    parser.add_argument("-c", "--config", type=str, help="Path to config file", default="config.json")
    args = parser.parse_args()

    server = Server()
    server.run()