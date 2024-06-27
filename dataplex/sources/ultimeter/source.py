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

class SourceUltimeter(Source):
    def __init__(self, port: Optional[str] = None):
        self.ultimeter = ultimeter.Ultimeter(port=port)
        self.ultimeter.start()

    def __str__(self):
        return ("Ultimeter")

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
