import mido
import time
import threading
from typing import Callable

from .destination import Destination

class EventTracker:
    def __init__(self, property: str, when: str, value: float, debounce_time: float, action: Callable):
        self.property = property
        self.when = when
        self.value = value
        self.debounce_time = debounce_time
        self.action = action

        self.last_triggered = None
        self.last_value = None

    def process(self, data):
        current_value = data[self.property]

        if self.last_triggered is None or (time.time() - self.last_triggered >= self.debounce_time):
            if self.when == "value_crossed":
                if self.last_value is None or (self.last_value < self.value and current_value >= self.value) \
                    or (self.last_value > self.value and current_value <= self.value):                
                    self.action(data)
                    self.last_triggered = time.time()

        self.last_value = current_value
        

class DestinationMidi (Destination):
    def __init__(self, port_name):
        self.port_name = port_name
        self.output = mido.open_output(self.port_name)
        self.mappings = {}
        self.event_trackers = []

    def __str__(self):
        return "Midi (%s)" % (self.port_name)
    
    def add_mapping(self, property: str, cc: int):
        self.mappings[property] = cc
    
    def add_event(self,
                  property: str,
                  when: str,
                  value: float,
                  note: int,
                  debounce_time: float = 0.5):
        
        def action(data):            
            msg = mido.Message("note_on", channel=0, note=note, velocity=64)
            self.output.send(msg)
            def note_off_thread():
                time.sleep(1.0)
                msg = mido.Message("note_off", channel=0, note=note, velocity=64)
                self.output.send(msg)
            threading.Thread(target=note_off_thread).start()
        event = EventTracker(property, when, value, debounce_time, action=action)
        self.event_trackers.append(event)

    def send(self, data):
        for name, record in list(data.items()):
            if name in self.mappings:
                cc = self.mappings[name]
                msg = mido.Message("control_change", channel=0, control=cc, value=int(record * 127))
                self.output.send(msg)
        for event_tracker in self.event_trackers:
            event_tracker.process(data)