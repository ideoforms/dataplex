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

class SourceUltimeter:
    def __init__(self,
                 field_names: list[str] = FIELDS,
                 port: Optional[str] = None):
        self.ultimeter = ultimeter.Ultimeter(port=port)
        self.ultimeter.start()
        self.fields = field_names

    def __str__(self):
        return ("Ultimeter")

    def collect(self):
        data = {}

        for name in self.fields:
            if name in self.ultimeter.values:
                data[name] = self.ultimeter.values[name]

        return data

    def close(self):
        self.ultimeter.close()
