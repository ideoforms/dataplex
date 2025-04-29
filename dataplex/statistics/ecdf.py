import sys

from statistics import mean

#--------------------------------------------------------------
# ECDF:
#--------------------------------------------------------------
def ecdf(distribution, sample):
    """
    ecdf: returns the percentile position of a sample within an empirical
    cumulative distribution, with linear interpolation between data points.
    """
    distribution = sorted(distribution)

    if sample == distribution[0]:
        return 0.0
    elif sample == distribution[-1]:
        return 1.0
    else:
        for n, occurrence in enumerate(distribution):
            if occurrence > sample:
                lerp = (sample - distribution[n - 1]) / float(distribution[n] - distribution[n - 1])
                n_frac = ((n - 1) + lerp) / (len(distribution) - 1)
                
                return n_frac

class ECDFNormaliser(object):
    def __init__(self, global_history = sys.maxsize, recent_history = 20, distribution = None):
        self.global_history = global_history
        self.recent_history = recent_history
        self.history = []

        if distribution is not None:
            self.history += distribution
        while len(self.history) > self.global_history:
            self.history.pop(0)

        self.recent_size = 20 
    
    def __len__(self):
        return len(self.history)

    @property
    def value(self):
        try:
            return self.history[-1]
        except:
            return None
    
    @property
    def change(self):
        value = self.value
        previous = self.previous_value
        if value is None or previous is None:
            return None
        else:
            return value - previous
    
    @property
    def previous_value(self):
        return self.value_at(-2)

    @property
    def previous_normalised(self):
        previous = self.previous_value
        if previous is None:
            return None
        else:
            return self.norm(previous, add = False)
    
    def value_at(self, index):
        try:
            return self.history[index]
        except:
            return None

    @property
    def recent_mean(self):
        num_recent = self.recent_size
        recent_items = self.history[-num_recent:]
        return mean(recent_items)

    @property
    def global_mean(self):
        return mean(self.history)

    @property
    def normalised(self):
        return self.norm()

    def norm(self, value = None, add = True):
        if value is not None:
            #--------------------------------------------------------------------------
            # Value to normalise is specified.
            # Normalise (and optionally add to history)
            #--------------------------------------------------------------------------
            try:
                normalized = [ecdf([ histitem[n] for histitem in self.history ], value[n]) for n in range(len(value))]
            except (ZeroDivisionError, KeyError):
                # not got any history - start from the beginning
                normalized = (0.5,) * len(value)
            #--------------------------------------------------------------------------
            # if this fails, attempt to normalize as if we have a scalar
            #--------------------------------------------------------------------------
            except TypeError:
                try:
                    normalized = ecdf(self.history, value)
                except ZeroDivisionError:
                    normalized = 0.5
            if add:
                self.register(value)

            # Override with normal normaliser!
            if len(self.history) > 1:
                history_min = min(self.history)
                history_max = max(self.history)
                if history_max - history_min > 0:
                    normalized = (value - history_min) / float(history_max - history_min)

            return normalized

        elif self.value is not None:
            #--------------------------------------------------------------------------
            # No value is specified.
            # Return last normalised value.
            #--------------------------------------------------------------------------
            return self.norm(self.value, False)
        else:

            #--------------------------------------------------------------------------
            # No value is specified and we don't have a last normalised value.
            #--------------------------------------------------------------------------
            return None

    def register(self, value):
        #--------------------------------------------------------------------------
        # whatever the type of our entities, add them to history, then
        # crop history to the maximum specified histsize
        #--------------------------------------------------------------------------
        self.history.append(value)
        while len(self.history) > self.global_history:
            self.history.pop(0)

    def recent(self):
        #--------------------------------------------------------------------------
        # takes the average of the past <n>
        # crop history to the maximum specified histsize
        #--------------------------------------------------------------------------
        recent_items = self.history[-self.recent_history:]

        #--------------------------------------------------------------------------
        # handle tuples and lists
        #--------------------------------------------------------------------------
        try:
            averages = []
            for n in range(len(recent_items[0])):
                average = sum([ item[n] for item in recent_items ]) / float(len(recent_items))
                averages.append(average)
            if type(recent_items[0]) == tuple:
                averages = tuple(averages)
            print("averages: %s" % str(averages))
            return self.norm(averages, False)
        #--------------------------------------------------------------------------
        # handle scalars
        #--------------------------------------------------------------------------
        except TypeError as e:
            recent_mean = mean(recent_items)
            global_mean = mean(self.history)
            return self.norm(recent_mean, False)
        except IndexError:
            return 0.5

class ClassNormaliser:
    """ Records instances of a discrete set of values, and returns the
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
    def __init__(self, histsize = 50, classes = []):
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

