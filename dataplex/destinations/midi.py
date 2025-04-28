import mido

from .destination import Destination

class DestinationMidi (Destination):
    def __init__(self, port_name):
        self.port_name = port_name
        self.output = mido.open_output(self.port_name)
        self.mappings = {}

    def __str__(self):
        return "Midi (%s)" % (self.port_name)
    
    def add_mapping(self, property: str, cc: int):
        self.mappings[property] = cc

    def send(self, data):
        for name, record in list(data.items()):
            if name in self.mappings:
                cc = self.mappings[name]
                msg = mido.Message("control_change", channel=0, control=cc, value=int(record.normalised * 127))
                self.output.send(msg)