import glob
import time
import serial
import logging
import threading

from .source import Source
logger = logging.getLogger(__name__)


class SourceSerial (Source):
    def __init__(self,
                 field_names: list[str],
                 port_name: str = None,
                 record_delimiter: str = "\n",
                 field_delimiter: str = ","):
        """
        Reads data from a serial connection

        Args:
            field_names (list[str]): The list of field names for the data received over the connection.
            port (str, optional): Path to serial port (e.g., "/dev/cu.usbmodem2101"). Defaults to None.
            record_delimiter (str, optional): In the serial protocol, the record delimiter. Defaults to "\n".
            field_delimiter (str, optional): In the serial protocol, the field delimiter. Defaults to ",".
        """
        super().__init__()
        self.field_names = field_names
        self.port_name = port_name
        self.record_delimiter = record_delimiter
        self.field_delimiter = field_delimiter

        self.port = None
        self.buffer = ""
        self.handler = None
        self.data = dict((field_name, None) for field_name in field_names)
        
        self.read_thread = None

        self.open()
        self.start()

    def start(self):
        if self.read_thread:
            logger.warning("Serial: Thread is already running")
            return
        else:
            self.read_thread = threading.Thread(target=self.run, daemon=True)
            self.read_thread.start()

    @property
    def is_open(self):
        """
        Indicates whether this serial device is connected.
        """
        return True if self.port else False

    def open(self, port_name: str = None):
        """
        Open a connection to the named serial device (eg /dev/tty.*)
        """
        if self.is_open:
            return

        if port_name is not None:
            self.port_name = port_name

        if self.port_name is None or self.port_name == "auto" or "*" in self.port_name:
            #------------------------------------------------------------------------
            # Look for a default interface
            #------------------------------------------------------------------------
            wildcard = self.port_name if "*" in self.port_name else "/dev/cu.usb*"
            interfaces = glob.glob(wildcard)
            interfaces = list(sorted(interfaces))
            if interfaces:
                self.port_name = interfaces[0]
                logger.info(("Serial: Using port %s" % self.port_name))


        if self.port_name is None:
            raise Exception("No serial port given and couldn't auto-detect")

        self.port = serial.Serial(port=self.port_name,
                                  baudrate=2400,
                                  timeout=0.1)

    def close(self):
        if self.port:
            self.port.close()
        self.port = None

    def run(self):
        """
        Read loop that continuously reads CR-delimited serial data.
        If the connection is closed, it will be reopened automatically. 
        """
        while True:
            try:
                self.open()

                while self.port.isOpen():
                    n = self.port.inWaiting()
                    text = self.port.read(size=n)
                    if len(text) == 0:
                        continue
                    text = text.decode()
                    self.buffer += text
                    while "\n" in self.buffer:
                        position = self.buffer.index(self.record_delimiter)
                        line = self.buffer[:position]
                        self.buffer = self.buffer[position + 1:]
                        values = [float(value) for value in line.split(self.field_delimiter)]
                        logger.debug("Serial: Read values: %s" % values)
                        if len(values) != len(self.field_names):
                            raise RuntimeError("Unexpected number of fields read from serial connection (found %d, expected %d)" %
                                               (len(values), len(self.field_names)))
                        for field, value in zip(self.field_names, values):
                            self.data[field] = value

                    time.sleep(0.01)

            except (serial.SerialException, OSError) as e:
                logger.warning("Error reading serial: %s" % e)
            
            self.close()
            logger.warning("Serial: Trying to re-open port...")
            time.sleep(1)

    def collect(self):
        return self.data


if __name__ == "__main__":
    source = SourceSerial(field_names=["value"])
    source.start()

    while True:
        time.sleep(0.1)
