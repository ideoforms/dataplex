#!/usr/local/bin/python

import os
import csv
import OSC
import sys
import math
import time
import socket
import pickle
import getopt

import settings

from simutils import mean, stddev

MODE_FILE = 0
MODE_PAKBUS = 1
MODE_ULTIMETER = 2

def mean(values):
	#--------------------------------------------------------------
	# mean of set
	#--------------------------------------------------------------
	if len(values) is None:
		print "***** no values! %s" % values
		return 0.0
	return float(sum(values)) / len(values)

def stddev(values, value_mean = None):
	#--------------------------------------------------------------
	# standard deviation
	#--------------------------------------------------------------
	if value_mean is None:
		value_mean = mean(values)
	sumsquares = sum([ (n - value_mean) ** 2 for n in values ])
	return math.sqrt(sumsquares / len(values))

def scale(value, min, mean, max):
	#--------------------------------------------------------------
	# linear scaling with mean
	#--------------------------------------------------------------
	if value < mean:
		return 0.5 * (value - min) / (mean - min)
	else:
		return 0.5 + 0.5 * (value - mean) / (max - mean)


class Collector:
	def __init__(self):
		#--------------------------------------------------------------
		# general-purpose initialisation.
		#--------------------------------------------------------------
		self.smoothed = dict([ (name, 0.0) for name in settings.fields ])
		self.history = dict([ (name, []) for name in settings.fields ])
		self.data = {}
		self.data_norm = {}
		self.data_min  = {}
		self.data_mean = {}
		self.data_max  = {}

		#--------------------------------------------------------------
		# we always want to transmit over OSC. set this up now.
		# support specifying multiple OSC ports for multicast.
		#--------------------------------------------------------------
		self.osc_clients = []
		for destination in settings.osc_destinations:
			osc_host, osc_port = destination.split(":")
			osc_port = int(osc_port)
			if settings.debug:
				print "connecting: %s, %s" % (osc_host, osc_port)
			osc_client = OSC.OSCClient()
			osc_client.connect((osc_host, osc_port))
			self.osc_clients.append(osc_client)

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
				while len(self.history[key]) > settings.histsize:
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
		# self.logwriter.writerow([ now ] +  [ self.data[key] for key in settings.fields ])
		self.logwriter.writerow([ now ] + [ self.data[key] for key in settings.fields ])

	def sendOSC(self, address, *args):
		msg = OSC.OSCMessage(address)
		msg.extend(list(args))

		for client in self.osc_clients:
			try:
				client.send(msg)
			except Exception, e:
				if settings.debug:
					print "send failed (%s)" % e

	def send(self):
		#--------------------------------------------------------------
		# first, send current time in hours and minutes 
		#--------------------------------------------------------------
		localtime = time.localtime(data["time"])
		# DJJ - use now
		localtime = time.localtime(time.time())
		hours   = localtime[3]
		minutes = localtime[4]

		self.sendOSC("/weather/time", hours, minutes, int(data["time"]))

		if settings.debug:
			print " - sendMsg: /weather/time %d %d %d" % (hours, minutes, data["time"])
		

		for name in settings.fields:
			#--------------------------------------------------------------
			# send OSC message.
			# for some variables, we might want to always send out our
			# peak value (eg, rain).
			#--------------------------------------------------------------
			value = self.smoothed[name]
			if settings.use_peak[name]:
				value = self.data_max[name]

			#--------------------------------------------------------------
			# why do we need to send min/max values?
			#--------------------------------------------------------------
			self.sendOSC("/weather/%s" % name, value, self.data_norm[name], self.data_min[name], self.data_mean[name], self.data_max[name])
			if settings.debug:
				print " - sendMsg: /weather/%s %.3f %.3f %.3f %.3f %.3f" % (name, value, self.data_norm[name], self.data_min[name], self.data_mean[name], self.data_max[name] )

	def close(self):
		pass 

	def calculate_norms(self):
		#--------------------------------------------------------------
		# normalise values over <histsize> readings.
		#--------------------------------------------------------------
		for name in settings.fields:
			value = self.data[name]

			#--------------------------------------------------------------
			# apply smoothing based on current and previous values.
			#--------------------------------------------------------------
			if self.smoothed[name] is None:
				self.smoothed[name] = value
			else:
				self.smoothed[name] = (settings.smoothing[name] * self.smoothed[name]) + (value * (1.0 - settings.smoothing[name]))

			#--------------------------------------------------------------
			# calculate minimum, mean and max of values over <histsize>.
			# use these to generate normalised [0,1] values.
			#--------------------------------------------------------------
			hist = self.history[name] 
			field_min = min(hist)
			field_max = max(hist)
			field_mean = mean(hist)
			field_sd = stddev(hist, field_mean)
			if field_max == field_min:
				value_norm = 0.5
			else:
				value_norm = scale(value, field_min, field_mean, field_max)

			if value_norm < 0:
				value_norm = 0
			if value_norm > 1:
				value_norm = 1

			#--------------------------------------------------------------
			# store values in data_norm for future use.
			# XXX: should we also use stddev;
			#--------------------------------------------------------------
			self.data_norm[name] = value_norm
			self.data_min[name]  = field_min
			self.data_mean[name] = field_mean
			self.data_max[name]  = field_max

			# print "%s: norm = %.3f, value = %.3f, min = %.3f, mean = %.3f, max = %.3f, sd = %.3f" % (name, value_norm, value, field_min, field_mean, field_max, field_sd)

class CollectorPakbus(Collector):
	def __init__(self):
		import pakbus

		Collector.__init__(self)

		#--------------------------------------------------------------
		# if we're in serial mode, connect to pakbus port.
		#--------------------------------------------------------------
		try:
			self.serial = pakbus.open_serial(settings.pakbus_dev)
		except Exception, e:
			print "Couldn't open serial device %s (%s)" % (settings.pakbus_dev, e)
			sys.exit(1)

		msg = pakbus.ping_node(self.serial, settings.pakbus_nodeid, settings.pakbus_mynodeid)
		if not msg:
			raise Warning('no reply from PakBus node 0x%.3x' % settings.pakbus_nodeid)

		self.init_log()

	def collect(self):
		import pakbus
		data = {}

		data["time"] = int(time.time())

		for name in settings.fields:
			longname = (filter(lambda n: settings.translations[n] == name, settings.translations.keys()))[0]

			#--------------------------------------------------------------
			# get each of our parameters from the device.
			#--------------------------------------------------------------
			value = pakbus.getvalues(self.serial, settings.pakbus_nodeid, settings.pakbus_mynodeid, "Public", 'IEEE4B', longname)
			value = value[0]

			if name == "wind_dir" and settings.reverse_wind_dir:
				value = 360.0 - value

			data[name] = value

		if (not settings.uniq) or (data != self.data):
			#--------------------------------------------------------------
			# only log new data (if specified)
			#--------------------------------------------------------------
			self.set_data(data)
			self.log()

			return data
		else:
			return None


	def close(self):
		self.logfd.close()

		#--------------------------------------------------------------
		# say goodbye and close socket.
		#--------------------------------------------------------------
		pakbus.send(self.serial, pakbus.pkt_bye_cmd(settings.pakbus_nodeid, settings.pakbus_mynodeid))
		self.serial.close()

class CollectorUltimeter(Collector):
	def __init__(self):
		Collector.__init__(self)

		import ultimeter

		#--------------------------------------------------------------
		# if we're in serial mode, connect to pakbus port.
		#--------------------------------------------------------------
		try:
			self.ultimeter = ultimeter.Ultimeter()
			self.ultimeter.start()
		except Exception, e:
			print "Couldn't open serial device: %s" % e
			sys.exit(1)

		self.init_log()

	def collect(self):
		data = {}

		for name in settings.fields:
			if name in self.ultimeter.values:
				data[name] = self.ultimeter.values[name]

		if data and ((not settings.uniq) or (data != self.data)):
			data["time"] = int(time.time())

			#--------------------------------------------------------------
			# only log new data (if specified)
			#--------------------------------------------------------------
			self.set_data(data)
			self.log()

			return data
		else:
			return None

	def close(self):
		self.ultimeter.close()

class CollectorCSV(Collector):
	def __init__(self):
		#--------------------------------------------------------------
		# set up our file reader.
		#--------------------------------------------------------------
		self.infd = open(settings.infile, "r")
		self.inreader = csv.reader(self.infd)
		self.log_fields = self.inreader.next()

		settings.fields = self.log_fields[:]
		settings.fields.remove("time")

		#--------------------------------------------------------------
		# init after we've read the CSV header, as this determines
		# what fields we will be reading
		#--------------------------------------------------------------
		Collector.__init__(self)

		#--------------------------------------------------------------
		# first field is always timestamp.
		#--------------------------------------------------------------
		self.data = self.get_next()
		self.t0_log  = self.data["time"]
		self.t0_time = time.time()
		self.next = self.data

	def get_next(self):
		row = self.inreader.next()
		row[0] = time.mktime(time.strptime(row[0], settings.time_format))
		row = dict([ (self.log_fields[n], float(value)) for n, value in enumerate(row) ])
		# print "row %s" % row
		return row

	def collect(self):
		log_delta = (self.next["time"] - self.t0_log) / float(settings.csv_rate)
		time_delta = time.time() - self.t0_time
		found = False
		while time_delta >= log_delta:
			found = True
			self.set_data(self.next)
			self.next = self.get_next()
			log_delta = (self.next["time"] - self.t0_log) / float(settings.csv_rate)
			
		if found:
			return self.data

def usage():
	print "Usage: %s [-f <csv_file>] [-s]" % sys.argv[0]
	print "  -p: input mode pakbus (Campbell Scientific)"
	print "  -u: input mode ultimeter (Peet Bros)"
	print "  -f: input mode .csv file"
	print "  -r: rate of CSV reading"
	print "  -d: debug output"
	print "  -n: disable smoothing"

	sys.exit(1)

if __name__ == "__main__":
	#--------------------------------------------------------------
	# unbuffered stdout for launchctl logging
	#--------------------------------------------------------------
	sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

	#--------------------------------------------------------------
	# pull commandline opts and update settings appropriately.
	#--------------------------------------------------------------
	try:
		flags, args = getopt.getopt(sys.argv[1:], "f:pudnr:")
	except:
		usage()

	for key, value in flags:
		if key == "-f":
			settings.mode = MODE_FILE
			settings.infile = value
		elif key == "-p":
			settings.mode = MODE_PAKBUS
		elif key == "-u":
			settings.mode = MODE_ULTIMETER
		elif key == "-d":
			settings.debug = True
		elif key == "-r":
			settings.csv_rate = float(value)
		elif key == "-n":
			print "smoothing disabled"
			for key, value in settings.smoothing.items():
				settings.smoothing[key] = 0.0
			
	#--------------------------------------------------------------
	# create our collector object, adopting whatever mode is
	# selected in settings.mode.
	#--------------------------------------------------------------
	if settings.mode == MODE_PAKBUS:
		collector = CollectorPakbus()
	if settings.mode == MODE_ULTIMETER:
		collector = CollectorUltimeter()
	elif settings.mode == MODE_FILE:
		collector = CollectorCSV()

	try:
		count = 0

		while True:
			#--------------------------------------------------------------
			# eternal loop. pull the latest data and output to screen.
			# also add a heading every N lines for readability.
			#--------------------------------------------------------------
			data = collector.collect()

			if data:
				collector.send()

				if count % 40 == 0:
					print " ".join([ "%-26s" % key for key in [ "time" ] + settings.fields ])
				count = count + 1
		
				# print "\t".join([ "%.10f" % collector.data[key] for key in settings.fields ])
				# for key in settings.fields:
				# 	print "[%.3f, %.3f, %.3f]\t" % (collector.data_min[key], collector.data[key], collector.data_max[key]),
				try:
					print "%-26s" % time.strftime(settings.time_format, time.localtime(collector.data["time"])),
					for key in settings.fields:
						# values = "[%.2f, %.2f, %.2f]" % (collector.data_min[key], collector.data[key], collector.data_max[key])
						values = "[%.1f, %.2f, %.1f > %.2f]" % (collector.data_min[key], collector.data[key], collector.data_max[key], collector.data_norm[key])
						# values = "[%.2f, %.2f]" % (collector.data[key], collector.data_norm[key])
						print "%-26s" % values,
					print ""
				except Exception, e:
					print "failed: %s" % e
	
			if settings.mode == MODE_PAKBUS or settings.mode == MODE_ULTIMETER:
				time.sleep(settings.serial_sleep)
			elif settings.mode == MODE_FILE:
				time.sleep(settings.csv_sleep)

	except KeyboardInterrupt:
		#--------------------------------------------------------------
		# die silently.
		#--------------------------------------------------------------
		print "killed by ctrl-c"
		pass

