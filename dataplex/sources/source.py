class Source:
    def __init__(self):
        self.property_names = []

    def start(self):
        """
        Start the Source. This may be overridden by subclasses to run any initialisation
        code whose properties may have been set during setup.
        """
        pass
        
    def collect(self, blocking: bool = False):
        """
        Return new data, if available.

        Args:
            blocking (bool, optional): If True, blocks until new data is available.
                                       In the general dataplex loop, a non-blocking collect() is always used.

        Returns:
            dict: The new data, or None if no new data is available.
        """
        if self.data:
            return self.data