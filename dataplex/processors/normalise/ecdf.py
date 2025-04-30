import sys

from ..base import Processor

#--------------------------------------------------------------
# ECDF:
#--------------------------------------------------------------
def ecdf(distribution, sample):
    """
    ecdf: returns the percentile position of a sample within an empirical
    cumulative distribution, with linear interpolation between data points.
    """
    distribution = sorted(distribution)

    if len(distribution) == 0:
        return 0.5
    elif sample == distribution[0]:
        return 0.0
    elif sample == distribution[-1]:
        return 1.0
    else:
        for n, occurrence in enumerate(distribution):
            if occurrence > sample:
                lerp = (sample - distribution[n - 1]) / float(distribution[n] - distribution[n - 1])
                n_frac = ((n - 1) + lerp) / (len(distribution) - 1)

                return n_frac

class ProcessorECDFNormalise(Processor):
    def __init__(self, max_history_size=sys.maxsize):
        self.max_history_size = max_history_size
        self.history = []

    def __len__(self):
        return len(self.history)

    def process(self, value):
        if value is not None:
            normalized = ecdf(self.history, value)
            #--------------------------------------------------------------------------
            # Whatever the type of our entities, add them to history, then
            # crop history to the maximum specified histsize
            #--------------------------------------------------------------------------
            self.history.append(value)
            while len(self.history) > self.max_history_size:
                self.history.pop(0)

            return normalized

        else:
            #--------------------------------------------------------------------------
            # No value is specified and we don't have a last normalised value.
            #--------------------------------------------------------------------------
            return None

class ClassNormaliser:
    """
    Records instances of a discrete set of values, and returns the
    proportional number of times that each value has occurred over a
    given history window.

    Usage:
        norm = ClassNormaliser()
        for n in range(50):
            if random.uniform(0, 1) < 0.3:
                norm.add("alice");
            else:
                norm.add("bob");
        print norm.proportions()
    """

    def __init__(self, histsize=50, classes=[]):
        self.histsize = histsize
        self.history = []
        self.classes = classes

    def add(self, item):
        self.history.append(item)
        if item not in self.classes:
            self.classes.append(item)
        while len(self.history) > self.histsize:
            self.history.pop(0)

    def proportions(self):
        proportions = {}
        for item in self.classes:
            count = self.history.count(item)
            proportion = float(count) / len(self.history)
            proportions[item] = proportion
        return proportions
