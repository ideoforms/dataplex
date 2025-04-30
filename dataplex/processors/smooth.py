from .base import Processor

class ProcessorSmooth (Processor):
    def __init__(self, smoothing=None, max_rise_rate=None, max_fall_rate=None, max_rate_change=None):
        self.value = None
        self.smoothing = smoothing

    def process(self, value):
        if self.value is None:
            self.value = value
        else:
            self.value = (self.smoothing * self.value) + ((1 - self.smoothing) * value)
        return self.value