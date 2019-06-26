import time

from .destination import Destination
from .. import settings

class DestinationStdout (Destination):
	def __init__(self):
		self.phase = 0

	def send(self, data):
		#--------------------------------------------------------------
		# add a heading every N lines for readability.
		#--------------------------------------------------------------
		if self.phase % settings.print_interval == 0:
			print(" ".join([ "%-19s" % key for key in [ "time" ] + settings.fields ]))

		self.phase = self.phase + 1

		#--------------------------------------------------------------
		# add a heading every N lines for readability.
		#--------------------------------------------------------------
		print("%-19s" % time.strftime(settings.time_format, time.localtime(data["time"])), end=' ')
		for key in settings.fields:
			if data[key].value is not None:
				values = "[%.2f, %.2f]" % (
					data[key].value,
					data[key].normalised
				)
				print("%-19s" % values, end=' ')
			else:
				print("%-19s" % "", end=' ')
		print("")
