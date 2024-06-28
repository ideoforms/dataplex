import time
import logging
import argparse

from . import settings

from .config import load_config
from .settings import global_history_length, recent_history_length
from .sources import SourceAudio, SourceCSV, SourcePakbus, SourceUltimeter, SourceWebcam
from .destinations import DestinationJDP, DestinationCSV, DestinationOSC, DestinationStdout
from .statistics.ecdf import ECDFNormaliser

logger = logging.getLogger(__name__)

class Server:
    def __init__(self, config_path: str = "config/config.json"):
        """
        Server is the central class that loads a configuration, reads data from one or more
        Source objects, and relays the processed stream to one or more Destinations.

        Args:
            config_path (str, optional): Path to the JSON config file. Defaults to "config/config.json".

        Raises:
            ValueError: If an invalid Source or Destination type is given.
        """
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
                self.sources.append(SourceCSV(path=source.path,
                                              rate=source.rate))
            elif source.type == "webcam":
                self.sources.append(SourceWebcam())
            elif source.type == "audio":
                self.sources.append(SourceAudio())
            else:
                raise ValueError(f"Source type not known: f{source.type}")

        #--------------------------------------------------------------
        # Init: Fields
        #--------------------------------------------------------------
        self.field_names = []
        for source in self.sources:
            self.field_names += source.fields
        self.field_names = [n for n in self.field_names if n != "time"]

        self.data = {}

        for source in self.sources:
            for name in source.fields:
                item = ECDFNormaliser(global_history_length,
                                      recent_history_length)
                self.data[name] = item

        #--------------------------------------------------------------
        # Init: Destinations
        #--------------------------------------------------------------
        self.destinations = []
        self.destinations.append(DestinationStdout(field_names=self.field_names))

        #--------------------------------------------------------------
        # Iterate over configured destinations
        #--------------------------------------------------------------
        for destination in config.destinations:
            if destination.type == "csv":
                self.destinations.append(DestinationCSV(field_names=self.field_names,
                                                        path_template=destination.path))
            elif destination.type == "osc":
                self.destinations.append(DestinationOSC(destination.host,
                                                        destination.port))
            elif destination.type == "jdp":
                self.destinations.append(DestinationJDP(destination.host,
                                                        destination.port))
            else:
                raise ValueError(f"Destination type not known: f{destination.type}")

        #--------------------------------------------------------------
        # Print output
        #--------------------------------------------------------------
        logger.info("Sources: ")
        for source in self.sources:
            logger.info(" - %s" % source)
        logger.info("Destinations: ")
        for destination in self.destinations:
            logger.info(" - %s" % destination)

    def run(self):
        """
        Run the main server process, blocking indefinitely.
        """
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
                    logger.info("Source %s ended stream." % self.source)
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
                for key in self.field_names:
                    if self.data[key].value is None:
                        logger.info("Awaiting data for %s..." % key)
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
                if isinstance(self.sources[0], SourceCSV):
                    time.sleep(0.01)
                else:
                    time.sleep(settings.read_interval)

        except KeyboardInterrupt:
            logger.info("Killed by ctrl-c")
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Run the dataplex I/O server")
    parser.add_argument("--verbose", "-v", help="Verbose output", action="store_true")
    parser.add_argument("--quiet", "-q", help="Quiet output", action="store_true")
    parser.add_argument("-c", "--config", type=str, help="Path to JSON config file", default="config/config.json")
    args = parser.parse_args()

    log_level = "INFO"
    if args.quiet:
        log_level = "WARNING"
    elif args.verbose:
        log_level = "DEBUG"
    logging.basicConfig(level=log_level, format='%(asctime)s %(name)-24s %(levelname)-8s %(message)s')

    server = Server(config_path=args.config)
    server.run()