import struct
import pyaudio
import math
import threading

from .. import settings
from .source import Source

BLOCK_SIZE = 256

class SourceAudio(Source):
	def __init__(self):
		self.audio = pyaudio.PyAudio()
		self.stream = self.audio.open(format = pyaudio.paInt16, channels = 1, rate = 44100, input = True, frames_per_buffer = BLOCK_SIZE)
		self.stream.start_stream()

		self.buffer = self.stream.read(BLOCK_SIZE)

		self.read_thread = threading.Thread(target = self.read_thread)
		self.read_thread.setDaemon(True)
		self.read_thread.start()

	def read_thread(self):
		while True:
			self.buffer += self.stream.read(BLOCK_SIZE)

	def collect(self):
		values = struct.unpack("%dh" % (len(self.buffer) / 2), self.buffer)
		mean = sum([ sample * sample for sample in values ]) / float(len(self.buffer))
		rms = math.sqrt(mean) / 32768.0
		data = { "rms" : rms }

		# import time
		# data["time"] = time.time()

		return data

	@property
	def fields(self):
		return [ "rms" ]