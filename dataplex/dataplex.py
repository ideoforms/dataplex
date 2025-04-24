import time
import logging
import argparse
import datetime
from collections import OrderedDict

from . import settings

from .config import load_config
from .settings import global_history_length, recent_history_length
from .sources import Source, SourceAudio, SourceCSV, SourcePakbus, SourceUltimeter, SourceWebcam, SourceJDP, SourceSerial
from .destinations import DestinationJDP, DestinationCSV, DestinationOSC, DestinationStdout
from .statistics.ecdf import ECDFNormaliser

logger = logging.getLogger(__name__)

class Dataplex:
    def __init__(self,
                 config_file: str = "config.json",
                 quiet: bool = False,
                 sources: list[str] = []):
        """
        Server is the central class that loads a configuration, reads data from one or more
        Source objects, and relays the processed stream to one or more Destinations.

        Args:
            config_file (str, optional): Path to the JSON config file. Defaults to "config.json".
                                         The 'config' subdirectory is automatically searched.
            quiet (bool, optional): If True, suppresses terminal output

        Raises:
            ValueError: If an invalid Source or Destination type is given.
        """
        self.on_record_callback = None

        config = load_config(config_file)
        self.config = config.config
        source_configs = config.sources
        destination_configs = config.destinations
        
        #--------------------------------------------------------------
        # Init: Sources
        #--------------------------------------------------------------
        self.sources = OrderedDict()
        for source_config in source_configs:
            if not source_config.enabled:
                logger.info("Server: Skipping source %s due to enabled=False" % str(source_config.name))
                continue
            if sources and source_config.name not in sources:
                logger.info("Server: Skipping source %s as not in specified sources list" %
                            str(source_config.name))
                continue

            if source_config.type == "pakbus":
                source = SourcePakbus()
            elif source_config.type == "ultimeter":
                source = SourceUltimeter(property_names=source_config.properties,
                                         port=source_config.port)
            elif source_config.type == "csv":
                source = SourceCSV(path=source_config.path,
                                   rate=source_config.rate)
            elif source_config.type == "jdp":
                source = SourceJDP(property_names=source.properties,
                                   port=source.port)
            elif source_config.type == "video":
                source = SourceWebcam(source.camera_index)
            elif source_config.type == "audio":
                source = SourceAudio(properties=source_config.properties)
            elif source_config.type == "serial":
                source = SourceSerial(property_names=source.properties,
                                      port_name=source.port_name)
            else:
                raise ValueError(f"Source type not known: {source_config.type}")

            # TODO: Refactor to instantiate a source via a type-to-class lookup dict,
            #       passing name and other params as part of kwargs
            self.sources[source_config.name] = source

        #--------------------------------------------------------------
        # Init: Fields
        #--------------------------------------------------------------
        self.property_names = []
        for source in self.sources.values():
            if source.property_names:
                self.property_names += source.property_names
        self.property_names = [n for n in self.property_names if n != "time"]

        self.data = {}

        for source in self.sources.values():
            if source.property_names:
                for name in source.property_names:
                    item = ECDFNormaliser(global_history_length,
                                          recent_history_length)
                    self.data[name] = item

        #--------------------------------------------------------------
        # Init: Destinations
        #--------------------------------------------------------------
        self.destinations = []

        
        #--------------------------------------------------------------
        # Iterate over configured destinations
        #--------------------------------------------------------------
        for destination_config in destination_configs:
            if destination_config.type == "csv":
                destination = DestinationCSV(property_names=self.property_names,
                                              path_template=destination_config.path)
            elif destination_config.type == "osc":
                destination = DestinationOSC(destination_config.host,
                                             destination_config.port)
            elif destination_config.type == "jdp":
                destination = DestinationJDP(destination_config.host,
                                             destination_config.port)
            elif destination_config.type == "stdout":
                destination = DestinationStdout(property_names=self.property_names)
            else:
                raise ValueError(f"Destination type not known: f{destination_config.type}")
        
            self.destinations.append(destination)

        #--------------------------------------------------------------
        # Print output
        #--------------------------------------------------------------
        logger.info("Sources: ")
        for source_name, source in self.sources.items():
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
            for source_name, source in self.sources.items():
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
        # if len(record) == 1:
        #     return

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
        for key in self.property_names:
            if self.data[key].value is None:
                logger.warning("Awaiting data for %s..." % key)
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
        
        #--------------------------------------------------------------
        # If present, trigger the on_record callback.
        #--------------------------------------------------------------
        if self.on_record_callback:
            self.on_record_callback(self.data)

        return self.data

    def run(self):
        """
        Run the main server process, blocking indefinitely.
        """

        #------------------------------------------------------------------------------
        # Run any initialisation code for sources whose properties may have been
        # set during setup.
        #------------------------------------------------------------------------------
        for source in self.sources.values():
            source.start()

        try:
            while True:
                self.next()

                #--------------------------------------------------------------
                # Wait until next cycle
                #--------------------------------------------------------------
                if isinstance(list(self.sources.keys())[0], SourceCSV):
                    time.sleep(0.01)
                else:
                    time.sleep(self.config.read_interval)

        except KeyboardInterrupt:
            logger.info("Killed by ctrl-c")
            pass

    def get_source(self, name) -> Source:
        """
        Get a source by name.

        Args:
            name (str): The name of the source to retrieve.

        Returns:
            Source: The source object.
        """
        if name in self.sources:
            return self.sources[name]
        else:
            raise ValueError(f"Source {name} not found")