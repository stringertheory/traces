"""A class for manipulating time series based on measurements at
unevenly-spaced times, see:

http://en.wikipedia.org/wiki/Unevenly_spaced_time_series

"""
import pprint
from queue import PriorityQueue

import sortedcontainers
from future.utils import iteritems, listitems
from infinity import inf


class Booga(object):

    def __init__(self, data=None, domain=None, default_value=None):
        self._d = sortedcontainers.SortedDict(data)
        self.default_value = default_value

    def __iter__(self):
        """Iterate over sorted (time, value) pairs."""
        return iteritems(self._d)

    def __contains__(self, key):
        return key in self._d

    def default(self):
        """Return the default value of the time series."""
        if self.default_value is None and self.n_measurements() == 0:
            msg = "can't get value without a default value or measurements"
            raise KeyError(msg)
        else:
            if self.default_value is None:
                return self.first()[1]
            else:
                return self.default_value

    def get(self, time):
        """Get the value of the time series, even in-between measured values.

        """
        index = self._d.bisect_right(time)
        if index > 0:
            previous_measurement_time = self._d.iloc[index - 1]
            return self._d[previous_measurement_time]
        elif index == 0:
            return self.default()
        else:
            msg = (
                'self._d.bisect_right({}) returned a negative value. '
                """This "can't" happen: please file an issue at """
                'https://github.com/datascopeanalytics/traces/issues'
            ).format(time)
            raise ValueError(msg)

    def get_by_index(self, index):
        """Get the (t, value) pair of the time series by index."""
        return self._d.peekitem(index)

    def last(self):
        """Returns the last (time, value) pair of the time series."""
        return self.get_by_index(-1)

    def first(self):
        """Returns the first (time, value) pair of the time series."""
        return self.get_by_index(0)

    def set(self, time, value, compact=False):
        """Set the value for the time series. If compact is True, only set the
        value if it's different from what it would be anyway.

        """
        if (len(self) == 0) or (not compact) or \
                (compact and self.get(time) != value):
            self._d[time] = value

    def update(self, data, compact=False):
        """Set the values of TimeSeries using a list.
        Compact it if necessary."""
        self._d.update(data)
        if compact:
            self.compact()

    def compact(self):
        """Convert this instance to a compact version: the value will be the
        same at all times, but repeated measurements are discarded.

        """
        previous_value = None
        remove_item = []
        for time, value in self._d.items():
            if value == previous_value:
                remove_item.append(time)
            previous_value = value
        for item in remove_item:
            del self[item]

    def items(self):
        """ts.items() -> list of the (key, value) pairs in ts, as 2-tuples"""
        return listitems(self._d)

    def remove(self, time):
        """Allow removal of measurements from the time series. This throws an
        error if the given time is not actually a measurement point.

        """
        try:
            del self._d[time]
        except KeyError:
            raise KeyError('no measurement at %s' % time)

    def n_measurements(self):
        """Return the number of measurements in the time series."""
        return len(self._d)

    def __len__(self):
        """Should this return the length of time in seconds that the time
        series spans, or the number of measurements in the time
        series? For now, it's the number of measurements.

        """
        return self.n_measurements()

    def __repr__(self):
        return '<Lookup>\n%s\n</Lookup>' % \
            pprint.pformat(self._d)

    def _check_time_series(self, other):
        """Function used to check the type of the argument and raise an
        informative error message if it's not a TimeSeries.

        """
        if not isinstance(other, TimeSeries):
            msg = "unsupported operand types(s) for +: %s and %s" % \
                (type(self), type(other))
            raise TypeError(msg)

    @staticmethod
    def _iter_merge(timeseries_list):
        """This function uses a priority queue to efficiently yield the (time,
        value_list) tuples that occur from merging together many time
        series.

        """
        # cast to list since this is getting iterated over several
        # times (causes problem if timeseries_list is a generator)
        timeseries_list = list(timeseries_list)

        # Create iterators for each timeseries and then add the first
        # item from each iterator onto a priority queue. The first
        # item to be popped will be the one with the lowest time
        queue = PriorityQueue()
        for index, timeseries in enumerate(timeseries_list):
            iterator = iter(timeseries)
            try:
                item = (next(iterator), index, iterator)
            except StopIteration:
                pass
            else:
                queue.put(item)

        # `state` keeps track of the value of the merged
        # TimeSeries. It starts with the default. It starts as a list
        # of the default value for each individual TimeSeries.
        state = [ts.default() for ts in timeseries_list]
        while not queue.empty():

            # get the next time with a measurement from queue
            (t, next_value), index, iterator = queue.get()

            # make a copy of previous state, and modify only the value
            # at the index of the TimeSeries that this item came from
            state = list(state)
            state[index] = next_value
            yield t, state

            # add the next measurement from the time series to the
            # queue (if there is one)
            try:
                queue.put((next(iterator), index, iterator))
            except StopIteration:
                pass

    @classmethod
    def iter_merge(cls, timeseries_list):
        """Iterate through several time series in order, yielding (time, list)
        tuples where list is the values of each individual TimeSeries
        in the list at time t.

        """
        if len(timeseries_list) == 0:
            raise ValueError(
                "timeseries_list is empty. There is nothing to merge.")

        # This function mostly wraps _iter_merge, the main point of
        # this is to deal with the case of tied times, where we only
        # want to yield the last list of values that occurs for any
        # group of tied times.
        index, previous_t, previous_state = -1, object(), object()
        for index, (t, state) in enumerate(cls._iter_merge(timeseries_list)):
            if index > 0 and t != previous_t:
                yield previous_t, previous_state
            previous_t, previous_state = t, state

        # only yield final thing if there was at least one element
        # yielded by _iter_merge
        if index > -1:
            yield previous_t, previous_state

    @classmethod
    def merge(cls, ts_list, compact=True, operation=None):
        """Iterate through several time series in order, yielding (time,
        `value`) where `value` is the either the list of each
        individual TimeSeries in the list at time t (in the same order
        as in ts_list) or the result of the optional `operation` on
        that list of values.

        """
        result = cls()
        for t, merged in cls.iter_merge(ts_list):
            if operation is None:
                value = merged
            else:
                value = operation(merged)
            result.set(t, value, compact=compact)
        return result

    def __setitem__(self, time, value):
        """Allow a[time] = value syntax."""
        return self.set(time, value)

    def __getitem__(self, time):
        """Allow a[time] syntax."""
        return self.get(time)

    def __delitem__(self, time):
        """Allow del[time] syntax."""
        return self.remove(time)

    def iterperiods(self, start=-inf, end=inf, value=None):
        """This iterates over the periods (optionally, within a given time
        span) and yields (interval start, interval end, value) tuples.

        Will only yield time intervals that are not length 0 that are
        within the domain.

        """
        # if value is None, don't filter
        if value is None:
            def value_function(t0_, t1_, value_):
                return True

        # if value is a function, use the function to filter
        elif callable(value):
            value_function = value

        # if value is a constant other than None, then filter to
        # return only the intervals where the value equals the
        # constant
        else:
            def value_function(t0_, t1_, value_):
                return value_ == value

        # get start index and value
        start_index = self._d.bisect_right(start)
        if start_index:
            start_value = self._d[self._d.iloc[start_index - 1]]
        else:
            start_value = self.default()

        # get last measurement before end of time span
        end_index = self._d.bisect_right(end)

        int_t0, int_value = start, start_value

        for int_t1 in self._d.islice(start_index, end_index):

            if value_function(int_t0, int_t1, int_value):
                yield int_t0, int_t1, int_value

            # set start point to the end of this interval for next
            # iteration
            int_t0 = int_t1
            int_value = self[int_t0]

        # yield the time, duration, and value of the final period
        if int_t0 < end:
            if value_function(int_t0, end, int_value):
                yield int_t0, end, int_value
