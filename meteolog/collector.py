#!/usr/local/bin/python

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
		if settings.source == SOURCE_PAKBUS:
			self.source = SourcePakbus()
		elif settings.source == SOURCE_ULTIMETER:
			self.source = SourceUltimeter()
		elif settings.source == SOURCE_CSV:
			self.source = SourceCSV(settings.csv_file)

		#--------------------------------------------------------------
		# init: DATA
		#--------------------------------------------------------------
		settings.fields = self.source.fields
		settings.fields = filter(lambda n: n != "time", settings.fields)

		self.data = {}

		for name in self.source.fields:
			item = ECDFNormaliser(settings.global_history, settings.recent_history)
			self.data[name] = item

		#--------------------------------------------------------------
		# init: DESTINATIONS
		# we always want to transmit over OSC. set this up now.
		# support specifying multiple OSC ports for multicast.
		#--------------------------------------------------------------
		self.destinations = []
		for destination_address in settings.osc_destinations:
			osc_host, osc_port = destination_address.split(":")
			destination = DestinationOSC(osc_host, int(osc_port))

			if settings.debug:
				print "connecting: %s, %s" % (osc_host, osc_port)

			self.destinations.append(destination)

	def run(self):
		try:
			count = 0

			while True:
				#--------------------------------------------------------------
				# eternal loop. pull the latest data and output to screen.
				#--------------------------------------------------------------
				try:
					record = self.source.collect()
				except StopIteration:
					#--------------------------------------------------------------
					# TODO: we should throw this when a CSV file has finished
					#--------------------------------------------------------------
					print "STOP"
					break

				if filter(lambda field: field not in record.keys(), settings.fields):
					continue

				self.data["time"] = record["time"]
				for key in settings.fields:
					if key in record:
						self.data[key].register(record[key])

				self.send(self.data)

				#--------------------------------------------------------------
				# add a heading every N lines for readability.
				#--------------------------------------------------------------
				if count % settings.print_interval == 0:
					print " ".join([ "%-26s" % key for key in [ "time" ] + settings.fields ])
				count = count + 1
		
				#--------------------------------------------------------------
				# add a heading every N lines for readability.
				#--------------------------------------------------------------
				print "%-26s" % time.strftime(settings.time_format, time.localtime(self.data["time"])),
				for key in settings.fields:
					values = "[%.2f, %.2f]" % (
						self.data[key].value,
						self.data[key].normalised
					)
					print "%-26s" % values,
				print ""
	
				if settings.source == SOURCE_PAKBUS or settings.source == SOURCE_ULTIMETER:
					time.sleep(settings.serial_sleep)
				elif settings.source == SOURCE_CSV:
					time.sleep(settings.csv_sleep)

		except KeyboardInterrupt:
			#--------------------------------------------------------------
			# die silently.
			#--------------------------------------------------------------
			print "killed by ctrl-c"
			pass

	def init_log(self):
		#--------------------------------------------------------------
		# start writing to output logfile.
		#--------------------------------------------------------------
		logfile = time.strftime(settings.logfile)
		self.logfd = open(logfile, "w")
		self.logwriter = csv.writer(self.logfd)
		self.logwriter.writerow([ "time" ] + settings.fields)

	def set_data(self, data):
		# print "set_data %s" % data
		self.data = data
		for key, value in self.data.items():
			try:
				self.history[key].append(value)
				while len(self.history[key]) > settings.global_history:
					self.history[key].pop(0)
			except KeyError:
				# print "key %s not found in history!" % key
				pass
		try:
			self.calculate_norms()
		except TypeError, e:
			print "Error whilst calculating normalised values! %s" % e

	def log(self):
		#--------------------------------------------------------------
		# write the latest set of data to logfile.
		#--------------------------------------------------------------
		now = time.strftime(settings.time_format, time.localtime(self.data["time"]))
		self.logwriter.writerow([ now ] + [ self.data[key] for key in settings.fields ])

	def send(self, data):
		#--------------------------------------------------------------
		# send our current data to each destination
		#--------------------------------------------------------------
		for destination in self.destinations:
			destination.send(data)

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
				print "smoothing disabled"
				for key, value in settings.smoothing.items():
					settings.smoothing[key] = 0.0
			elif key == "-h":
				usage()
			

