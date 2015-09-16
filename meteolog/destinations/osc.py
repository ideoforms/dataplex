import time
import OSC

from .destination import Destination

class DestinationOSC (Destination):
	def __init__(self, host, port):
		self.host = host
		self.port = port

		self.osc_client = OSC.OSCClient()
		self.osc_client.connect((host, port))

	def sendMsg(self, address, *args):
		msg = OSC.OSCMessage(address)
		msg.extend(list(args))
		try:
			self.osc_client.send(msg)
		except OSC.OSCClientError:
			#------------------------------------------------------------------------
			# Most likely because this client isn't listening
			#------------------------------------------------------------------------
			pass

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

				self.sendMsg("/weather/%s" % name, value, norm)
			except IndexError:
				#------------------------------------------------------------------------
				# haven't yet got any data for this field (might not have read
				# anything yet)
				#------------------------------------------------------------------------
				pass
