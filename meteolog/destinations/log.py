import csv
import time

from .destination import Destination
from .. import settings

class DestinationLog (Destination):
	def __init__(self):
		#--------------------------------------------------------------
		# start writing to output logfile.
		#--------------------------------------------------------------
		logfile = time.strftime(settings.logfile)
		self.logfd = open(logfile, "w")
		self.logwriter = csv.writer(self.logfd)
		self.logwriter.writerow([ "time" ] + settings.fields)

	def send(self, data):
		#--------------------------------------------------------------
		# write the latest set of data to logfile.
		#--------------------------------------------------------------
		now = time.strftime(settings.time_format, time.localtime(data["time"]))
		self.logwriter.writerow([ now ] + [ data[key].value for key in settings.fields ])

	def close(self):
		self.logfd.close()
