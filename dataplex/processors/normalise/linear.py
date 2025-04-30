from ..base import Processor
import sys

class ProcessorLinearNormalise(Processor):
    def __init__(self, max_history_size: int = sys.maxsize):
        self.max_history_size = max_history_size
        self.history = []
        self.min_value = None
        self.max_value = None

    def __len__(self):
        return len(self.history)

    def process(self, value):
        if value is not None:
            if self.max_value is None or value > self.max_value:
                self.max_value = value
            if self.min_value is None or value < self.min_value:
                self.min_value = value

            if (self.max_value - self.min_value) > 0:
                normalized = (value - self.min_value) / (self.max_value - self.min_value)
            else:
                normalized = 0.5

            self.history.append(normalized)
            if len(self.history) > self.max_history_size:
                self.history.pop(0)

            return normalized