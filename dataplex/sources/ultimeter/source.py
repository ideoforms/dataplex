import time
import sys

from ..source import Source
from . import ultimeter

FIELDS = [ "temperature", "wind_speed", "wind_dir", "rain", "pressure" ]

class SourceUltimeter(Source):
    def __init__(self, port = None):
        self.ultimeter = ultimeter.Ultimeter(port = port)
        self.ultimeter.start()

    def __str__(self):
        return("Ultimeter")

    def collect(self):
        data = {}

        for name, value in list(self.ultimeter.values.items()):
            data[name] = self.ultimeter.values[name]

        return data

    def close(self):
        self.ultimeter.close()
    
    @property
    def fields(self):
        return FIELDS
