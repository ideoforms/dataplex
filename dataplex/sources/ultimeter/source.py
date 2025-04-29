from ..source import Source
from . import ultimeter
from typing import Optional

FIELDS = [
    "temperature",
    "wind_speed",
    "wind_dir",
    "rain",
    "humidity"
]

class SourceUltimeter (Source):
    def __init__(self,
                 property_names: list[str] = FIELDS,
                 port: Optional[str] = None):
        self.ultimeter = ultimeter.Ultimeter(port=port)
        self.ultimeter.start()
        self.property_names = property_names

    def __str__(self):
        return ("Ultimeter")

    def collect(self):
        data = {}

        for name in self.property_names:
            if name in self.ultimeter.values:
                data[name] = self.ultimeter.values[name]

        return data

    def close(self):
        self.ultimeter.close()
