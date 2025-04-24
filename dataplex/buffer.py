import sys
import copy
import numpy as np

class RollingFeatureBufferSlice:
    def __init__(self, buffer: list):
        """
        Initialise the RollingFeatureBufferSlice.

        Args:
            buffer: The list of dicts to provide as a slice.
        """
        self.buffer = buffer
    
    def __getattribute__(self, name):
        if name == "buffer":
            return object.__getattribute__(self, name)
        else:
            return np.array([record.get(name).value for record in self.buffer])
    
class RollingFeatureBuffer:
    """
    Encapsulates a rolling buffer of feature dicts, in which each entry is automatically
    added on each dataplex record.
    """

    def __init__(self, max_size: int = sys.maxsize):
        """
        Initialise the buffer.

        Args:
            max_size: The maximum size of the buffer.
        """
        self.max_size = max_size
        self.buffer = []
    
    def __len__(self) -> int:
        """
        Get the current size of the buffer.

        Returns:
            The current size of the buffer.
        """
        return len(self.buffer)

    def __getitem__(self, key: slice) -> RollingFeatureBufferSlice:
        """
        Get a slice of the buffer as a RollingFeatureBufferSlice.

        Args:
            key: The slice object specifying the range.

        Returns:
            A RollingFeatureBufferSlice containing the sliced buffer.
        """
        return RollingFeatureBufferSlice(self.buffer[key])

    def __getattribute__(self, name):
        if name in ["buffer", "max_size", "append", "reset"] or name.startswith("_"):
            return object.__getattribute__(self, name)
        else:
            return getattr(RollingFeatureBufferSlice(self.buffer), name)
    
    def append(self, record: dict) -> None:
        """
        Append a new record to the buffer.

        Args:
            record: The record to append.
        """
        self.buffer.append(copy.deepcopy(record))
        if len(self.buffer) > self.max_size:
            self.buffer.pop(0)
    
    def reset(self) -> None:
        """
        Remove all entries from the buffer.
        """
        self.buffer = []

