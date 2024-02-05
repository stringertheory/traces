import itertools

import sortedcontainers

from . import utils
from .timeseries import TimeSeries


class EventSeries(sortedcontainers.SortedList):
    def __init__(self, data=None):
        super().__init__(data)

    def cumsum(self):
        """Alias for cumulative_sum"""
        return self.cumulative_sum()

    def cumulative_sum(self):
        """Returns a TimeSeries with each unique time in the
        EventSeries as an index point and with the cumulative number
        of events that have occured since the earliest time in the
        EventSeries as the value

        """
        ts = TimeSeries(default=0)
        running_total = 0
        for t, event_group in itertools.groupby(self):
            running_total += len(list(event_group))
            ts[t] = running_total

        return ts

    def events_between(self, start, end):
        """Returns the number of events that occured between `start
        and `end.  Calculates on a closed interval, so start and end
        are included in the range

        """
        start_idx = self.bisect_left(start)
        end_idx = self.bisect_right(end)
        return end_idx - start_idx

    def iter_interevent_times(self):
        """Returns a list of inter-event arrival times."""
        for t0, t1 in utils.pairwise(self):
            yield t1 - t0

    @staticmethod
    def count_active(es_open, es_closed):
        """
        Calculates the running difference from two event series
        `es_open` is an EventSeries that adds to the cumulative sum and
        `es_closed` is an EventSeries of subtracts from it

        Returns a TimeSeries of the number of open cases at any given time,
        assuming 0 open cases at the earliest time in either EventSeries
        """
        return es_open.cumsum() - es_closed.cumsum()
