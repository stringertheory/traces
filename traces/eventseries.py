import sortedcontainers
import collections

from . import TimeSeries


class EventSeries(sortedcontainers.SortedList):
    def __init__(self, data=None):
        super().__init__(data)

    def cumulative_sum(self):
        '''
        Returns a TimeSeries with each unique time in the EventSeries as an
        index point and with the cumulative number of events that have occured
        since the earliest time in the EventSeries as the value
        '''
        # Multiple events can happen at the same time so we need to hash them
        # as counts
        c = collections.Counter(self)
        # Then we want to sort them and calculate the cumulative_sum
        c = sortedcontainers.SortedDict(c)
        keys = c.keys()
        values = accumulate(list(c.values()))

        return TimeSeries(zip(keys, values), default=0)

    def n_measurements(self, start=None, end=None):
        '''
        Returns the number of events that occured between `start and `end.
        If start or end aren't provided defaults to the start or end of the EventSeries.
        Calculates on a closed interval, so start and end are included in the
        range
        '''
        start_idx = self.bisect_left(start) if start else 0
        end_idx = self.bisect_right(end) if end else len(self)
        return end_idx - start_idx

    def interevent_times(self):
        '''
        Returns a list of inter event arrival times. This will only work
        for EventSeries of a type that have a minus operation implemented.
        '''
        interevent_times = []
        for a, b in zip(self[1:], self[0:-1]):
            interevent_times.append(a-b)
        return interevent_times

    @staticmethod
    def count_active(es_open, es_closed):
        '''
        Calculates the running difference from two event series
        `es_open` is an EventSeries that adds to the cumulative sum and
        `es_closed` is an EventSeries of subtracts from it

        Returns a TimeSeries of the number of open cases at any given time,
        assuming 0 open cases at the earliest time in either EventSeries
        '''
        return es_open.cumulative_sum() - es_closed.cumulative_sum()


def accumulate(values_list):
    total = 0
    for i in values_list:
        total += i
        yield total
