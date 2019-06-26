import struct
import time
import math
import threading

import metoffer
import json

from .. import settings
from .source import Source

class SourceMetOffice(Source):
    def __init__(self):
        api_key = '0296975e-c0af-4ee0-ace6-b3c083980fa4'
        self.api = metoffer.MetOffer(api_key)
        self.data = {}
        self.read_thread = threading.Thread(target = self.read_thread)
        self.read_thread.setDaemon(True)
        self.read_thread.start()

    def read(self):
        observations = self.api.nearest_loc_obs(53.8460, -1.8360)

        data = observations['SiteRep']
        params = data['Wx']['Param']
        param_names = {}
        for param in params:
            param_names[param["name"]] = param["$"]
        location = data['DV']['Location']
        today = location['Period'][-1]
        latest = today['Rep'][-1]

        for key, value in list(latest.items()):
            if key in param_names:
                identifier = param_names[key].lower().replace(" ", "_")
                if identifier == "screen_relative_humidity":
                    identifier = "humidity"

                #------------------------------------------------------------------------
                # Only log items that we have selected
                #------------------------------------------------------------------------
                if identifier in self.fields:
                    try:
                        self.data[identifier] = float(value)
                    except:
                        self.data[identifier] = value

    def read_thread(self):
        while True:
            self.read()
            time.sleep(1200)

    def collect(self):
        return self.data

    @property
    def fields(self):
        return [ "humidity" ]
