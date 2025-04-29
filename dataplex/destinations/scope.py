from jdp import JDPClient

from .destination import Destination

class DestinationScope (Destination):
    def __init__(self, property_names: list[str]):
        self.client = JDPClient("127.0.0.1", 48000)
        self.property_names = property_names

        plot_height = 1.0 / len(property_names)

        config = {}
        for index, property in enumerate(property_names):
            config[property] = {
                "position": [0.0, plot_height * index],
                "size": [1.0, plot_height]
            }

        self.client.send({"config": config})

    def send(self, data):
        message = {}
        for property, value in data.items():
            if property in self.property_names:
                message[property] = value.value

        self.client.send({"data": message})