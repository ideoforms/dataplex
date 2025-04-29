import sys
import time
import logging
import datetime
from typing import Optional, Union
from collections import OrderedDict

from .config import load_config, GeneralConfig
from .settings import global_history_length, recent_history_length
from .sources import Source, SourceAudio, SourceCSV, SourceOSC, SourcePakbus, SourceUltimeter, SourceWebcam, SourceJDP, SourceSerial
from .destinations import Destination, DestinationJDP, DestinationCSV, DestinationOSC, DestinationStdout, DestinationMidi, DestinationScope
from .statistics.ecdf import ECDFNormaliser
from .buffer import RollingFeatureBuffer

logger = logging.getLogger(__name__)

class Dataplex:
    SOURCE_CLASS_MAP = {
        "pakbus": SourcePakbus,
        "ultimeter": SourceUltimeter,
        "csv": SourceCSV,
        "osc": SourceOSC,
        "jdp": SourceJDP,
        "video": SourceWebcam,
        "audio": SourceAudio,
        "serial": SourceSerial
    }

    DESTINATION_CLASS_MAP = {
        "csv": DestinationCSV,
        "osc": DestinationOSC,
        "jdp": DestinationJDP,
        "stdout": DestinationStdout,
        "midi": DestinationMidi,
        "scope": DestinationScope
    }

    def __init__(self,
                 config_file: str = None):
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
        self.rolling_buffers = []
        self.data = {}
        self.property_names = []
        self.sources = OrderedDict()
        self.destinations = []

        #--------------------------------------------------------------
        # Load config
        #--------------------------------------------------------------
        if config_file:
            self.read_config_file(config_file)
        else:
            self.config = GeneralConfig()

    def read_config_file(self, config_file: str):
        config = load_config(config_file)
        self.config = config.config
        source_configs = config.sources
        destination_configs = config.destinations

        #--------------------------------------------------------------
        # Init: Sources
        #--------------------------------------------------------------
        for source_config in source_configs:
            if not source_config.enabled:
                logger.info("Server: Skipping source %s due to enabled=False" % str(source_config.name))
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
                source = SourceJDP(property_names=source_config.properties,
                                   port=source_config.port)
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

            if source.property_names:
                self.property_names += [n for n in source.property_names if n != "time"]

                for name in source.property_names:
                    item = ECDFNormaliser(global_history_length,
                                          recent_history_length)
                    self.data[name] = item

        #--------------------------------------------------------------
        # Init: Destinations
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
        # If not specified (e.g. in CSV), set the time to now.
        #--------------------------------------------------------------
        if "time" not in record:
            record["time"] = datetime.datetime.now()

        #--------------------------------------------------------------
        # Register new data
        #--------------------------------------------------------------
        for key in record:
            if key == "time":
                self.data[key] = record[key]
            else:
                if isinstance(self.data[key], ECDFNormaliser):
                    self.data[key].register(record[key])
                else:
                    self.data[key] = record[key]

        #--------------------------------------------------------------
        # If any of our data sources are not yet set (returning None),
        # skip this iteration.
        #--------------------------------------------------------------
        missing_data = False
        for key in self.property_names:
            if self.data[key] is None:
                logger.warning("Awaiting data for %s..." % key)
                missing_data = True
            elif isinstance(self.data[key], ECDFNormaliser) and self.data[key].value is None:
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

        for rolling_buffer in self.rolling_buffers:
            rolling_buffer.append(self.data)

        return self.data

    def run(self):
        """
        Run the main server process, blocking indefinitely.
        """

        #--------------------------------------------------------------
        # Print output
        #--------------------------------------------------------------
        logger.info("Sources: ")
        for source_name, source in self.sources.items():
            logger.info(" - %s" % source)
        logger.info("Destinations: ")
        for destination in self.destinations:
            logger.info(" - %s" % destination)

        #------------------------------------------------------------------------------
        # Run any initialisation code for sources whose properties may have been
        # set during setup.
        #------------------------------------------------------------------------------
        for source in self.sources.values():
            source.start()

        while True:
            self.next()

            #--------------------------------------------------------------
            # Wait until next cycle
            #--------------------------------------------------------------
            if isinstance(list(self.sources.keys())[0], SourceCSV):
                time.sleep(0.01)
            else:
                time.sleep(self.config.read_interval)

    def add_source(self,
                   source: Optional[Source] = None,
                   type: Optional[str] = None,
                   properties: Optional[dict] = None,
                   **kwargs):
        """
        Add a source to the server.

        Args:
            source (Source): The source object to add.
        """
        if type is not None:
            if type not in Dataplex.SOURCE_CLASS_MAP:
                raise ValueError(f"Source type not known: {type}")
            source = Dataplex.SOURCE_CLASS_MAP[type](**kwargs)
            self.sources[type] = source
        elif source is not None:
            source_name = list(filter(lambda type: isinstance(source, Dataplex.SOURCE_CLASS_MAP[type]), Dataplex.SOURCE_CLASS_MAP.keys()))[0]
            self.sources[source_name] = source
        else:
            raise ValueError("Either source or type must be provided")

        if properties is not None:
            for property_name, property_type in properties.items():
                if property_name not in self.property_names:
                    if property_type == "float":
                        item = ECDFNormaliser(global_history_length,
                                              recent_history_length)
                        self.data[property_name] = item
                        
                        self.property_names.append(property_name)
                    elif property_type == "vec3":
                        for suffix in ["x", "y", "z"]:
                            property_subname = "%s_%s" % (property_name, suffix)
                            print("Adding property %s" % property_subname)
                            item = ECDFNormaliser(global_history_length,
                                                  recent_history_length)
                            self.data[property_subname] = item
                            self.property_names.append(property_subname)
        return source

    def add_destination(self,
                        destination: Optional[Union[str, Destination]] = None,
                        **kwargs):
        """
        Add a destination to the server.

        Args:
            destination (Destination): The destination object to add.
        """
        if isinstance(destination, str):
            if destination not in Dataplex.DESTINATION_CLASS_MAP:
                raise ValueError(f"Destination type not known: {destination}")
            destination = Dataplex.DESTINATION_CLASS_MAP[destination](**kwargs)
            self.destinations.append(destination)
        elif isinstance(destination, Destination):
            self.destinations.append(destination)
        else:
            raise ValueError("Destination %s invalid" % destination)
    
        return destination

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

    def create_rolling_buffer(self, max_size: int = sys.maxsize) -> RollingFeatureBuffer:
        """
        Create a rolling buffer for the current data.

        Returns:
            RollingBuffer: The rolling buffer object.
        """
        buffer = RollingFeatureBuffer(max_size=max_size)
        self.rolling_buffers.append(buffer)
        return buffer