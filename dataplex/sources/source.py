class Source:
    def __init__(self):
        self.property_names = []

    def start(self):
        """
        Start the Source. This may be overridden by subclasses to run any initialisation
        code whose properties may have been set during setup.
        """
        pass
        