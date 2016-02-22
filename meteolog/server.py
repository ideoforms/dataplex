import os
import csv
import sys
import math
import time
import getopt

import settings

from .constants import *
from .sources import *
from .destinations import *

from simutils import mean, stddev, AttributeDictionary, ECDFNormaliser


class Collector:
	def __init__(self):
		#--------------------------------------------------------------
		# unbuffered stdout for launchctl logging
		#--------------------------------------------------------------
		# (not using right now)
		# sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
		#--------------------------------------------------------------
		self.parse_args()

		#--------------------------------------------------------------
		# init: SOURCE
		# create our collector object, adopting whatever mode is
		# selected in settings.source.
		#--------------------------------------------------------------

		self.sources = []
		for source in settings.sources:
			if source == SOURCE_PAKBUS:
				self.sources.append(SourcePakbus())
			elif source == SOURCE_ULTIMETER:
				self.sources.append(SourceUltimeter())
			elif source == SOURCE_CSV:
				self.sources.append(SourceCSV(settings.csv_file))
			elif source == SOURCE_WEBCAM:
				self.sources.append(SourceWebcam())

		#--------------------------------------------------------------
		# init: DATA
		#--------------------------------------------------------------
		settings.fields = []
		for source in self.sources:
			settings.fields += source.fields
		settings.fields = filter(lambda n: n != "time", settings.fields)

		self.data = {}

		for source in self.sources:
			for name in source.fields:
				item = ECDFNormaliser(settings.global_history, settings.recent_history)
				self.data[name] = item

		#--------------------------------------------------------------
		# init: DESTINATIONS
		# we always want to transmit over OSC. set this up now.
		# support specifying multiple OSC ports for multicast.
		#--------------------------------------------------------------
		self.destinations = []

		#--------------------------------------------------------------
		# by default, output to a logfile and stdout.
		#--------------------------------------------------------------
		if filter(lambda source: source.should_log, self.sources):
			self.destinations.append(DestinationLog())
		self.destinations.append(DestinationStdout())

		#--------------------------------------------------------------
		# we currently always want to transmit over OSC. set this up now.
		# support specifying multiple OSC ports for multicast.
		#--------------------------------------------------------------
		for destination_address in settings.osc_destinations:
			osc_host, osc_port = destination_address.split(":")
			destination = DestinationOSC(osc_host, int(osc_port))

			print "connecting: %s, %s" % (osc_host, osc_port)

			self.destinations.append(destination)

	def run(self):
		try:
			while True:
				#--------------------------------------------------------------
				# eternal loop. pull the latest data and output to screen.
				#--------------------------------------------------------------
				try:
					record = {}
					for source in self.sources:
						record.update(source.collect())
				except StopIteration:
					#--------------------------------------------------------------
					# TODO: we should throw this when a CSV file has finished
					#--------------------------------------------------------------
					print "Source %s ended stream." % self.source
					break

				#--------------------------------------------------------------
				# Set time value, and record any values that are present.
				#--------------------------------------------------------------
				self.data["time"] = record["time"]
				for key in settings.fields:
					if key in record:
						self.data[key].register(record[key])

				#--------------------------------------------------------------
				# send our current data to each destination
				#--------------------------------------------------------------
				for destination in self.destinations:
					destination.send(self.data)

				#--------------------------------------------------------------
				# send our current data to each destination
				#--------------------------------------------------------------
				time.sleep(settings.serial_sleep)
				"""
				if settings.source == SOURCE_PAKBUS or settings.source == SOURCE_ULTIMETER:
					time.sleep(settings.serial_sleep)
				elif settings.source == SOURCE_CSV:
					time.sleep(settings.csv_sleep)
				"""

		except KeyboardInterrupt:
			#--------------------------------------------------------------
			# die silently.
			#--------------------------------------------------------------
			print "killed by ctrl-c"
			pass

	def parse_args(self):
		def usage():
			print "Usage: %s [-f <csv_file>] [-s]" % sys.argv[0]
			print "  -p: input mode pakbus (Campbell Scientific)"
			print "  -u: input mode ultimeter (Peet Bros)"
			print "  -f: input mode .csv file"
			print "  -r: rate of CSV reading"
			print "  -d: debug output"
			print "  -n: disable smoothing"
			print "  -h: show this help"

			sys.exit(1)

		#--------------------------------------------------------------
		# pull commandline opts and update settings appropriately.
		#--------------------------------------------------------------
		try:
			flags, args = getopt.getopt(sys.argv[1:], "f:pudnr:h")
		except:
			usage()

		for key, value in flags:
			if key == "-f":
				settings.source = SOURCE_CSV
				settings.csv_file = value
			elif key == "-p":
				settings.source = SOURCE_PAKBUS
			elif key == "-u":
				settings.source = SOURCE_ULTIMETER
			elif key == "-d":
				settings.debug = True
			elif key == "-r":
				settings.csv_rate = float(value)
			elif key == "-n":
				for key, value in settings.smoothing.items():
					settings.smoothing[key] = 0.0
			elif key == "-h":
				usage()
			

