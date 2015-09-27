import time

from .destination import Destination
from .. import settings

class DestinationStdout (Destination):
	def send(self, data):
		num_records = len(data[settings.fields[0]])

		#--------------------------------------------------------------
		# add a heading every N lines for readability.
		#--------------------------------------------------------------
		if num_records % settings.print_interval == 1:
			print " ".join([ "%-20s" % key for key in [ "time" ] + settings.fields ])

		#--------------------------------------------------------------
		# add a heading every N lines for readability.
		#--------------------------------------------------------------
		print "%-20s" % time.strftime(settings.time_format, time.localtime(data["time"])),
		for key in settings.fields:
			if data[key].value is not None:
				values = "[%.2f, %.2f]" % (
					data[key].value,
					data[key].normalised
				)
				print "%-20s" % values,
			else:
				print "%-20s" % "",
		print ""
