from simutils import AttributeDictionary

import jdp
import time

class Client (object):
    def __init__(self):
        self.server = jdp.Server(11000)
        self.server.add_callback(self.handler)
        self.server.start()
        self.data = AttributeDictionary()
        self.callbacks = []

    def __iter__(self):
        return iter(self.data)
    
    def wait_for_data(self, num_fields = 1):
        while not len(list(self.data.keys())) >= num_fields:
            print("Waiting for data..")
            time.sleep(0.1)
        print("Got data: %s" % list(self.data.keys()))

    def handler(self, data):
        for key, value in list(data.items()):
            self.data.set(key, value)
        for callback in self.callbacks:
            callback(data)
    
    def add_callback(self, callback):
        self.callbacks.append(callback)

    def remove_callback(self, callback):
        self.callbacks.remove(callback)
    
    def get_data(self):
        return self.data

    def get_value(self, condition):
        d = self.data.get(condition)
        if d:
            return d["value"]

    def get_normalised(self, condition):
        d = self.data.get(condition)
        if d:
            return d["normalised"]

