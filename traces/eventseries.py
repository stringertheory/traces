import sortedcontainers
import numpy as np
import collections

from . import TimeSeries


class EventSeries(sortedcontainers.SortedList):
    def __init__(self, data=None):
        super().__init__(data)

    def cumsum(self):
        '''
        Returns a TimeSeries with each unique time in the EventSeries as an index point
        and with the cumulative number of events that have occured since the earliest time
        in the EventSeries as the value
        '''
        # Multiple events can happen at the same time so we need to hash them as counts
        c = collections.Counter(self)
        # Then we want to sort them and calculate the cumsum
        c = sortedcontainers.SortedDict(c)
        keys = c.keys()
        values = np.cumsum(list(c.values()))

        return TimeSeries(zip(keys, values), default=0)

    def events_between(self, start, end):
        '''
        Returns the number of events that occured between `start and `end.
        Calculates on a closed interval, so start and end are included in the range
        '''
        start_idx = self.bisect_left(start)
        end_idx = self.bisect_right(end)
        return end_idx - start_idx

    def time_lag(self):
        '''
        Returns a `np.array` of inter event arrival times.
        This will only work for EventSeries of a type that have a minus operation implemented.
        '''
        return (np.array(self[1:]) - np.array(self[0:-1]))

    @staticmethod
    def count_active(es_open, es_closed):
        '''
        Calculates the running difference from two event series
        `es_open` is an EventSeries that adds to the cumulative sum and
        `es_closed` is an EventSeries of subtracts from it

        Returns a TimeSeries of the number of open cases at any given time,
        assuming 0 open cases at the earliest time in either EventSeries
        '''
        return es_open.cumsum() - es_closed.cumsum()
