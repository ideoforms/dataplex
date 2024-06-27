import time
import argparse

from . import settings

from .config import load_config
from .sources import SourceAudio, SourceCSV, SourcePakbus, SourceUltimeter, SourceWebcam
from .destinations import DestinationJDP, DestinationCSV, DestinationOSC, DestinationStdout
from .statistics.ecdf import ECDFNormaliser


class Server:
    def __init__(self, config_path: str = "config/config.json"):
        config = load_config(config_path)

        #--------------------------------------------------------------
        # Init: Sources
        #--------------------------------------------------------------
        self.sources = []
        for source in config.sources:
            if source.type == "pakbus":
                self.sources.append(SourcePakbus())
            elif source.type == "ultimeter":
                self.sources.append(SourceUltimeter(source.port))
            elif source.type == "csv":
                self.sources.append(SourceCSV(settings.csv_file))
            elif source.type == "webcam":
                self.sources.append(SourceWebcam())
            elif source.type == "audio":
                self.sources.append(SourceAudio())
            else:
                raise ValueError(f"Source type not known: f{source.type}")

        #--------------------------------------------------------------
        # Init: Fields
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
        # Init: Destinations
        #--------------------------------------------------------------
        self.destinations = []
        self.destinations.append(DestinationStdout())

        #--------------------------------------------------------------
        # Iterate over configured destinations
        #--------------------------------------------------------------
        for destination in config.destinations:
            if destination.type == "csv":
                self.destinations.append(DestinationCSV(path_template=destination.path))
            elif destination.type == "osc":
                self.destinations.append(DestinationOSC(destination.host,
                                                        destination.port))
            elif destination.type == "jdp":
                self.destinations.append(DestinationJDP(destination.host,
                                                        destination.port))
            else:
                raise ValueError(f"Destination type not known: f{destination.type}")


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
    parser.add_argument("-c", "--config", type=str, help="Path to JSON config file", default="config/config.json")
    args = parser.parse_args()

    server = Server(config_path=args.config)
    server.run()