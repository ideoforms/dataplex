import time
import liblo

from .destination import Destination

class DestinationOSC (Destination):
	def __init__(self, host, port):
		self.host = host
		self.port = port

		self.osc_host = liblo.Address(host, port)

	def sendMsg(self, address, *args):
		liblo.send(self.osc_host, address, *args)
		#------------------------------------------------------------------------
		# Most likely because this client isn't listening
		#------------------------------------------------------------------------

	def send(self, data):
		#--------------------------------------------------------------
		# first, send current time in hours and minutes 
		#--------------------------------------------------------------
		localtime = time.localtime(data["time"])

		self.sendMsg("/weather/time", int(data["time"]))

		for name, record in data.items():
			if name == "time":
				continue

			#--------------------------------------------------------------
			# send OSC message.
			# for some variables, we might want to always send out our
			# peak value (eg, rain).
			#--------------------------------------------------------------
			# if settings.use_peak[name]:
			#	value = self.data_max[name]

			#--------------------------------------------------------------
			# why do we need to send min/max values?
			#--------------------------------------------------------------
			try:
				value = record.value
				norm = record.normalised

				if value is not None:
					self.sendMsg("/weather/%s" % name, value, norm)
			except IndexError:
				#------------------------------------------------------------------------
				# haven't yet got any data for this field (might not have read
				# anything yet)
				#------------------------------------------------------------------------
				pass

