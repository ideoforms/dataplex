#------------------------------------------------------------------------
# needed to import a package whose name clashes with my own:
# http://stackoverflow.com/questions/4816595/how-do-i-import-a-module-whose-name-clashes-with-a-module-in-my-package
#------------------------------------------------------------------------
from __future__ import absolute_import 

import os
import csv
import time

from .. import settings
from .source import Source

class SourceCSV (Source):
	def __init__(self, filename, rate = 1.0):
		#--------------------------------------------------------------
		# set up our file reader.
		#--------------------------------------------------------------
		self.filename = filename
		self.fd = open(filename, "r")
		self.rate = rate
		self.reader = csv.reader(self.fd)
		self.fields = self.reader.next()

		self.t0_log = None
		self.t0_time = None

	def read(self):
		row = self.reader.next()
		row[0] = time.mktime(time.strptime(row[0], settings.time_format))
		row = dict([ (self.fields[n], float(value)) for n, value in enumerate(row) ])
		return row

	def collect(self):
		""" Block until the next reading is due, based on our CSV read rate. """

		if self.t0_log is None:
			#--------------------------------------------------------------
			# first field is always timestamp.
			#--------------------------------------------------------------
			data = self.read()
			self.t0_log  = data["time"]
			self.t0_time = time.time()
			return data

		row = self.read()

		log_delta = (row["time"] - self.t0_log) / float(settings.csv_rate)
		time_delta = time.time() - self.t0_time

		while time_delta <= log_delta:
			#------------------------------------------------------------------------
			# wait until we've hit the required time
			#------------------------------------------------------------------------
			time.sleep(0.1)
			time_delta = time.time() - self.t0_time
			
		"""
		while time_delta >= log_delta:
			#------------------------------------------------------------------------
			# TODO
			# skip over multiple readings
			#------------------------------------------------------------------------
			found = True
			self.set_data(self.next)
			self.next = self.read()
			log_delta = (self.next["time"] - self.t0_log) / float(settings.csv_rate)
		"""

		return row
