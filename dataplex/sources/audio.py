import time

try:
    from signalflow import *
except ModuleNotFoundError:
    pass

from .source import Source


class SourceAudio (Source):
    def __init__(self, properties=[]):
        super().__init__()

        self.property_names = properties
        self.graph = AudioGraph()
        self.feature_nodes = {}
        self.input_node = None

    def set_input_node(self, node: Node):
        assert isinstance(node, Node), "Input node must be a SignalFlow Node"
        self.input_node = node

    def start(self):
        """
        Start the Source. This may be overridden by subclasses to run any initialisation
        code whose properties may have been set during setup.
        """
        feature_node_map = {
            "rms": RMS,
            "f0": "vamp:pyin:yin:f0",
            "f0-voiced-prob": "vamp:pyin:pyin:voicedprob",
            "spectral-flux": "vamp:bbc-vamp-plugins:bbc-spectral-flux:spectral-flux",
            "spectral-flatness": "vamp:vamp-libxtract:flatness:flatness",
            "spectral-centroid": "vamp:vamp-example-plugins:spectralcentroid:linearcentroid",
        }

        if self.input_node is None:
            self.input_node = AudioIn(1)

        for property_name in self.property_names:
            if property_name in feature_node_map.keys():
                feature_node_name = feature_node_map[property_name]
                if isinstance(feature_node_name, str):
                    feature_node = VampAnalysis(input=self.input_node,
                                                 plugin_id=feature_node_name)
                else:
                    feature_node = feature_node_map[property_name](input=self.input_node)
            elif property_name.startswith("vamp:"):
                feature_node = VampAnalysis(input=self.input_node,
                                             plugin_id=property_name)
            
            # TODO: This smoothing should be configurable
            feature_node = Smooth(feature_node, 0.9999)
            self.graph.add_node(feature_node)
            self.feature_nodes[property_name] = feature_node


    def collect(self):
        data = {}
        for property_name, feature_node in self.feature_nodes.items():
            data[property_name] = float(feature_node.output_buffer[0][0])

        return data

    @property
    def fields(self):
        return self.properties

if __name__ == "__main__":
    source = SourceAudio()

    while True:
        print(source.collect())
        time.sleep(0.1)
