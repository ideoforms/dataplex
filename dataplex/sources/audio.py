import math
import time
import struct
import threading

try:
    import pyaudio
except ModuleNotFoundError:
    print("Skipping source: Audio")

from .source import Source


class SourceAudio(Source):
    def __init__(self, block_size: int = 256):
        self.audio = pyaudio.PyAudio()
        self.block_size = block_size
        self.stream = self.audio.open(format=pyaudio.paInt16,
                                      channels=1,
                                      rate=44100,
                                      input=True,
                                      frames_per_buffer=self.block_size)
        self.stream.start_stream()

        self.buffer = self.stream.read(self.block_size)

        self.read_thread = threading.Thread(target=self.read_thread)
        self.read_thread.setDaemon(True)
        self.read_thread.start()

    def read_thread(self):
        while True:
            self.buffer = self.stream.read(self.block_size)

    def collect(self):
        values = struct.unpack("%dh" % (len(self.buffer) / 2), self.buffer)
        mean = sum([sample * sample for sample in values]) / float(len(self.buffer))
        rms = math.sqrt(mean) / 32768.0
        data = {"rms": rms}

        return data

    @property
    def fields(self):
        return ["rms"]

if __name__ == "__main__":
    source = SourceAudio()

    while True:
        print(source.collect())
        time.sleep(0.1)
