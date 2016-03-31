"""A class for manipulating [time series based on measurements at
unevenly-spaced
times](http://en.wikipedia.org/wiki/Unevenly_spaced_time_series).

For an discussion of visualizing this type of thing, see [Representing
Unevenly-Spaced Time Series Data for Visualization and Interactive
Exploration](http://hcil2.cs.umd.edu/trs/2005-01/2005-01.pdf#healthycakes)
by Aleks Aris and others.

"""

# standard library
import sys
import datetime
import pprint
import math
import random
import itertools
import Queue

# 3rd party
import sortedcontainers
import arrow

# local
from . import histogram
from . import utils


class TimeSeries(object):

    """A class to help manipulate and analyze time series that are the
    result of taking measurements at irregular points in time. For
    example, here would be a simple time series that starts at 8am and
    goes to 9:59am:

    ts = TimeSeries()
    ts['8:00am'] = 0
    ts['8:47am'] = 1
    ts['8:51am'] = 0
    ts['9:15am'] = 1
    ts['9:59am'] = 0

    The value of the time series is the last recorded measurement: for
    example, at 8:05am the value is 0 and at 8:48am the value is 1. So:

    ts['8:05am']
    >> 0

    ts['8:48am']
    >> 1

    There are also a bunch of things for operating on another time
    series: sums, difference, logical operators and such.

    """

    def __init__(self, default_type=int, default_value=None):
        self.d = sortedcontainers.SortedDict()
        self.default_type = default_type
        self.default_value = default_value

    def __iter__(self):
        """Iterate over sorted (time, value) pairs."""
        return self.d.iteritems()

    def default(self):
        """Return the default value of the time series."""
        if self.default_value is None:
            return self.default_type()
        else:
            return self.default_type(self.default_value)

    def get(self, time):
        """Get the value of the time series, even in-between measured values.

        """
        index = self.d.bisect_right(time)
        if index:
            previous_measurement_time = self.d.iloc[index - 1]
            return self.d[previous_measurement_time]
        else:
            return self.default()

    def get_by_index(self, index):
        """Get the (t, value) pair of the time series by index."""
        t = self.d.iloc[index]
        return t, self.d[t]

    def last(self):
        """Returns the last (time, value) pair of the time series."""
        return self.get_by_index(-1)

    def set(self, time, value, compact=False):
        """Set the value for the time series. If compact is True, only set the
        value if it's different from what it would be anyway.

        """
        if (not compact) or (compact and self.get(time) != value):
            self.d[time] = value

    def compact(self):
        """Convert this instance to a compact version: the value will be the
        same at all times, but repeated measurements are discarded.

        """
        previous_value = self.default()
        for time, value in self.d.items():
            if value == previous_value:
                del self[time]
            previous_value = value

    def items(self):
        """ts.items() -> list of the (key, value) pairs in ts, as 2-tuples"""
        return self.d.items()

    def remove(self, time):
        """Allow removal of measurements from the time series. This throws an
        error if the given time is not actually a measurement point.

        """
        try:
            del self.d[time]
        except KeyError:
            raise KeyError('no measurement at %s' % time)

    def n_measurements(self):
        """Return the number of measurements in the time series."""
        return len(self.d)

    def __len__(self):
        """Should this return the length of time in seconds that the time
        series spans, or the number of measurements in the time
        series? For now, it's the number of measurements.

        """
        return self.n_measurements()

    def __repr__(self):
        return '<TimeSeries>\n%s\n</TimeSeries>' % \
            pprint.pformat(self.d)

    def iterintervals(self, value=None, n=2):
        """Iterate over groups of `n` consecutive measurement points in the
        time series, optionally only the groups where the starting
        value of the time series matches `value`.

        """
        # if value is None, don't filter intervals
        if value is None:
            def value_function(x):
                return True

        # if it's a function, use that to filter
        elif callable(value):
            value_function = value

        # if value isn't a function but it's a value other than None,
        # then make it one that returns true if the the argument
        # matches value
        else:
            def value_function(x):
                return x[0][1] == value

        # tee the original iterator into n identical iterators
        streams = itertools.tee(iter(self), n)

        # advance the "cursor" on each iterator by an increasing
        # offset
        for stream_index, stream in enumerate(streams):
            for i in range(stream_index):
                next(stream)

        # now, zip the offset streams back together to yield tuples
        for intervals in itertools.izip(*streams):
            if value_function(intervals):
                yield intervals

    def iterperiods(self, start_time=None, end_time=None):
        """This iterates over the periods (optionally, within a given time
        span) and yields (time, duration, value) tuples.

        """
        # use first/last measurement as start/end time if not given
        if start_time is None:
            start_time = self.d.iloc[0]
        if end_time is None:
            end_time = self.d.iloc[-1]

        # get start index and value
        start_index = self.d.bisect_right(start_time)
        if start_index:
            start_value = self.d[self.d.iloc[start_index - 1]]
        else:
            start_value = self.default()

        # get last measurement before end of time span
        end_index = self.d.bisect_right(end_time)

        # look over each interval of time series within the
        # region. Use the region start time and value to begin
        int_t0, int_value = start_time, start_value
        for int_t1 in self.d.islice(start_index, end_index):

            # yield the time, duration, and value of the period
            yield int_t0, (int_t1 - int_t0), int_value

            # set start point to the end of this interval for next
            # iteration
            int_t0 = int_t1
            int_value = self.d[int_t0]

        # yield the time, duration, and value of the final period
        if int_t0 < end_time:
            yield int_t0, (end_time - int_t0), int_value

    def slice(self, start_time, end_time):
        """Return a slice of the time series that has a first reading at
        `start_time` and a last reading at `end_time`.

        """
        if end_time <= start_time:
            message = (
                "Can't slice a Timeseries when end_time <= start_time. "
                "Received start_time=%s and end_time=%s"
            ) % (start_time, end_time)
            raise ValueError(message)

        result = TimeSeries(
            default_type=self.default_type,
            default_value=self.default_value,
        )

        # since start_time > end_time, this will always have at least
        # one item, so `value` gets set for following line
        for dt, duration, value in self.iterperiods(start_time, end_time):
            result[dt] = value
        result[end_time] = self[end_time]

        return result

    def regularize(self, window_size, sampling_period, start_time, end_time):
        """Should there be a different function for sampling at regular time
        periods versus averaging over regular intervals?

        """
        result = []
        half = float(window_size) / 2
        current_time = start_time
        while current_time <= end_time:
            window_start = current_time - datetime.timedelta(seconds=half)
            window_end = current_time + datetime.timedelta(seconds=half)
            mean = self.mean(window_start, window_end)
            result.append((current_time, mean))
            current_time += datetime.timedelta(seconds=sampling_period)
        return result

    def mean(self, start_time, end_time):
        """This calculated the average value of the time series over the given
        time range from `start_time` to `end_time`.

        """
        total_seconds = utils.duration_to_number(end_time - start_time)

        mean = 0.0
        for (t0, duration, value) in self.iterperiods(start_time, end_time):
            # calculate contribution to weighted average for this
            # interval
            try:
                mean += (utils.duration_to_number(duration) * value)
            except TypeError:
                msg = "Can't take mean of non-numeric type (%s)" % type(value)
                raise TypeError(msg)

        # return the mean value over the time period
        return mean / float(total_seconds)

    def distribution(self, start_time=None, end_time=None,
                     normalized=True, mask=None):
        """Calculate the distribution of values over the given time range from
        `start_time` to `end_time`.

        """
        counter = histogram.Histogram()
        if mask:
            mask_iterator = mask.iterperiods(start_time, end_time)
            for mask_start, mask_duration, mask_value in mask_iterator:
                mask_end = mask_start + mask_duration
                if mask_value:
                    self_iterator = self.iterperiods(mask_start, mask_end)
                    for t0, duration, value in self_iterator:
                        counter[value] += utils.duration_to_number(
                            duration,
                            units='seconds',
                        )
        else:
            # increment counter with duration of each period
            counter = histogram.Histogram()
            for t0, duration, value in self.iterperiods(start_time, end_time):
                counter[value] += utils.duration_to_number(
                    duration,
                    units='seconds',
                )

        # divide by total duration if result needs to be normalized
        if normalized:
            return counter.normalized()
        else:
            return counter

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
        """Iterate through several time series in order, yielding (time, list)
        tuples where list is the values of each individual TimeSeries
        in the list at time t.

        """
        # cast to list since this is getting iterated over several
        # times (will cause problem if timeseries_list is a generator)
        timeseries_list = list(timeseries_list)

        # Create iterators for each timeseries and then add the first
        # item from each iterator onto a priority queue. The first
        # item to be popped will be the one with the lowest time
        queue = Queue.PriorityQueue()
        for index, timeseries in enumerate(timeseries_list):
            iterator = iter(timeseries)
            try:
                item = (iterator.next(), index, iterator)
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
                queue.put((iterator.next(), index, iterator))
            except StopIteration:
                pass

    @classmethod
    def iter_merge(cls, timeseries_list):
        index, previous_t, previous_state = 0, object(), object()
        for index, (t, state) in enumerate(cls._iter_merge(timeseries_list)):
            if index > 0 and t != previous_t:
                yield previous_t, previous_state
            previous_t, previous_state = t, state
        if index > 0:
            yield previous_t, previous_state

    @classmethod
    def merge(cls, ts_list, compact=False, operation=None):
        """"""
        default_value = [ts.default() for ts in ts_list]
        result = cls(default_type=list, default_value=default_value)
        for t, merged in cls.iter_merge(ts_list):
            if operation is None:
                value = merged
            else:
                value = operation(merged)
            result.set(t, value, compact=compact)
        return result

    @classmethod
    def from_many_sum(cls, timeseries_list, compact=False):
        """Efficiently create a new time series that is the sum of many
        TimeSeries.

        """
        result = cls(default_type=float)
        for t, merged in cls.iter_merge(timeseries_list):
            result.set(t, sum(merged), compact=compact)
        return result

    @classmethod
    def from_many_union(cls, timeseries_list, compact=False):
        """Efficiently create a new time series that is the sum of many
        TimeSeries.

        """
        result = cls(default_type=set)
        for t, merged in cls.iter_merge(timeseries_list):
            result.set(t, set.union(*merged), compact=compact)
        return result

    def operation(self, other, function):
        """Calculate "elementwise" operation either between this TimeSeries
        and another one, i.e.

        operation(t) = function(self(t), other(t))

        or between this timeseries and a constant:

        operation(t) = function(self(t), other)

        If it's another time series, the measurement times in the
        resulting TimeSeries will be the union of the sets of
        measurement times of the input time series. If it's a
        constant, the measurement times will not change.

        """
        result = TimeSeries()
        if isinstance(other, TimeSeries):
            for time, value in self:
                result[time] = function(value, other[time])
            for time, value in other:
                result[time] = function(self[time], value)
        else:
            for time, value in self:
                result[time] = function(value, other)
        return result

    def to_bool(self, invert=False):
        """Return the truth value of each element."""
        if invert:
            def function(x, y): return False if x else True
        else:
            def function(x, y): return True if x else False
        return self.operation(None, function)

    def threshold(self, value, inclusive=False):
        """Return True if > than treshold value (or >= threshold value if
        inclusive=True).

        """
        if inclusive:
            def function(x, y): return True if x >= y else False
        else:
            def function(x, y): return True if x > y else False
        return self.operation(value, function)

    def sum(self, other):
        """sum(x, y) = x(t) + y(t)."""
        return TimeSeries.from_many_sum([self, other])

    def difference(self, other):
        """difference(x, y) = x(t) - y(t)."""
        return self.operation(other, lambda x, y: x - y)

    def multiply(self, other):
        """mul(t) = self(t) * other(t)."""
        return self.operation(other, lambda x, y: x * y)

    def logical_and(self, other):
        """logical_and(t) = self(t) and other(t)."""
        return self.operation(other, lambda x, y: int(x and y))

    def logical_or(self, other):
        """logical_or(t) = self(t) or other(t)."""
        return self.operation(other, lambda x, y: int(x or y))

    def logical_xor(self, other):
        """logical_xor(t) = self(t) ^ other(t)."""
        return self.operation(other, lambda x, y: int(bool(x) ^ bool(y)))

    def __setitem__(self, time, value):
        """Allow a[time] = value syntax."""
        return self.set(time, value)

    def __getitem__(self, time):
        """Allow a[time] syntax."""
        return self.get(time)

    def __delitem__(self, time):
        """Allow del[time] syntax."""
        return self.remove(time)

    def __add__(self, other):
        """Allow a + b syntax"""
        return self.sum(other)

    def __radd__(self, other):
        """Allow the operation 0 + TimeSeries() so that builtin sum function
        works on an iterable of TimeSeries.

        """
        # skip type check if other is the integer 0
        if not other == 0:
            self._check_time_series(other)

        # 0 + self = self
        return self

    def __sub__(self, other):
        """Allow a - b syntax"""
        return self.difference(other)

    def __mul__(self, other):
        """Allow a * b syntax"""
        return self.multiply(other)

    def __and__(self, other):
        """Allow a & b syntax"""
        return self.logical_and(other)

    def __or__(self, other):
        """Allow a | b syntax"""
        return self.logical_or(other)

    def __xor__(self, other):
        """Allow a ^ b syntax"""
        return self.logical_xor(other)
