import time

try:
    from signalflow import *
except ModuleNotFoundError:
    pass

from .source import Source


class SourceAudio (Source):
    def __init__(self):
        super().__init__()
        graph = AudioGraph()
        self.input_node = AudioIn(1)
        self.rms = RMS(self.input_node)
        graph.add_node(self.rms)
    
    def set_input_node(self, node: Node):
        assert isinstance(node, Node), "Input node must be a SignalFlow Node"
        self.input_node = node

    def collect(self):
        data = {
            "rms": self.rms.output_buffer[0][0]
        }

        return data

    @property
    def fields(self):
        return ["rms"]

if __name__ == "__main__":
    source = SourceAudio()

    while True:
        print(source.collect())
        time.sleep(0.1)
