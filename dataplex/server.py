import time
import logging
import argparse
import datetime

from . import settings

from .config import load_config
from .settings import global_history_length, recent_history_length
from .sources import SourceAudio, SourceCSV, SourcePakbus, SourceUltimeter, SourceWebcam, SourceJDP, SourceSerial
from .destinations import DestinationJDP, DestinationCSV, DestinationOSC, DestinationStdout
from .statistics.ecdf import ECDFNormaliser

logger = logging.getLogger(__name__)

class Server:
    def __init__(self,
                 config_path: str = "config/config.json",
                 quiet: bool = False,
                 sources: list[str] = []):
        """
        Server is the central class that loads a configuration, reads data from one or more
        Source objects, and relays the processed stream to one or more Destinations.

        Args:
            config_path (str, optional): Path to the JSON config file. Defaults to "config/config.json".
            quiet (bool, optional): If True, suppresses terminal output

        Raises:
            ValueError: If an invalid Source or Destination type is given.
        """
        config = load_config(config_path)

        #--------------------------------------------------------------
        # Init: Sources
        #--------------------------------------------------------------
        self.sources = []
        for source in config.sources:
            if not source.enabled:
                logger.info("Server: Skipping source %s due to enabled=False" % str(source.__class__.__name__))
                continue
            if sources and source.name not in sources:
                logger.info("Server: Skipping source %s as not in specified sources list" % str(source.__class__.__name__))
                continue

            if source.type == "pakbus":
                self.sources.append(SourcePakbus())
            elif source.type == "ultimeter":
                self.sources.append(SourceUltimeter(field_names=source.field_names,
                                                    port=source.port))
            elif source.type == "csv":
                self.sources.append(SourceCSV(path=source.path,
                                              rate=source.rate))
            elif source.type == "jdp":
                self.sources.append(SourceJDP(field_names=source.field_names,
                                              port=source.port))
            elif source.type == "video":
                self.sources.append(SourceWebcam(source.camera_index))
            elif source.type == "audio":
                self.sources.append(SourceAudio(source.block_size))
            elif source.type == "serial":
                self.sources.append(SourceSerial(field_names=source.field_names,
                                                 port_name=source.port_name))
            else:
                raise ValueError(f"Source type not known: {source.type}")
            
            # TODO: Refactor to instantiate a source via a type-to-class lookup dict,
            #       passing name and other params as part of kwargs
            self.sources[-1].name = source.name

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

        if not quiet:
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

    def next(self):
        #--------------------------------------------------------------
        # Infinite loop: pull new data and record.
        #--------------------------------------------------------------
        try:
            record = {}
            for source in self.sources:
                data = source.collect()
                if data:
                    record.update(data)

        except StopIteration:
            #--------------------------------------------------------------
            # TODO: we should throw this when a CSV file has finished
            #--------------------------------------------------------------
            logger.info("Source %s ended stream." % self.source)
            raise

        #--------------------------------------------------------------
        # Set time value, and record any values that are present.
        #--------------------------------------------------------------
        if "time" in record:
            self.data["time"] = record["time"]
        else:
            self.data["time"] = datetime.datetime.now()

        #--------------------------------------------------------------
        # If we've not got any data except time, skip this iteration.
        #--------------------------------------------------------------
        if len(record) == 1:
            return

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
            return

        #--------------------------------------------------------------
        # Send current data to each destination
        #--------------------------------------------------------------
        for destination in self.destinations:
            destination.send(self.data)

        return self.data
            
    def run(self):
        """
        Run the main server process, blocking indefinitely.
        """
        try:
            while True:
                self.next()
                #--------------------------------------------------------------
                # Wait until next cycle
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
    parser.add_argument("--sources", help="List of source names to select", type=str)
    parser.add_argument("-c", "--config", type=str, help="Path to JSON config file", default="config/config.json")
    args = parser.parse_args()

    log_level = "INFO"
    if args.quiet:
        log_level = "WARNING"
    elif args.verbose:
        log_level = "DEBUG"
    logging.basicConfig(level=log_level, format='%(asctime)s %(name)-24s %(levelname)-8s %(message)s')

    if args.sources:
        args.sources = args.sources.split(",")

    server = Server(config_path=args.config,
                    quiet=args.quiet,
                    sources=args.sources)
    server.run()
