import time
import sys

from ..source import Source
from . import ultimeter

FIELDS = [ "temperature", "humidity", "wind_speed", "wind_dir", "rain", "pressure" ]

class SourceUltimeter(Source):
	def __init__(self):
		self.ultimeter = ultimeter.Ultimeter()
		self.ultimeter.start()

	def collect(self):
		data = {}

		for name, value in self.ultimeter.values.items():
			data[name] = self.ultimeter.values[name]

		data["time"] = int(time.time())

		return data

	def close(self):
		self.ultimeter.close()
	
	@property
	def fields(self):
		return FIELDS
