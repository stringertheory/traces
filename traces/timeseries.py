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


def span_range(start, end, unit):
    """Iterate through time periods starting with start and including end
    by a given unit. Unit is given as a dictionary like {'hour': 1,
    'minute': 15} for units of one hour and fifteen minutes.

    """
    t0 = start
    while t0 <= end:
        t1 = t0.replace(**unit)
        yield t0, t1
        t0 = t1


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
        if self.default_value is None:
            return self.default_type()
        else:
            return self.default_type(self.default_value)
    
    def get(self, time):
        """This is probably the most important method. It allows the user to
        get the value of the time series inbetween measured values.

        THERE SHOULD BE THE OPTION TO INTERPOLATE!

        """
        index = self.d.bisect_right(time)
        if index:
            closest_time = self.d.iloc[index - 1]
            return self.d[closest_time]
        else:
            return self.default()

    def set(self, time, value, compact=False):
        """Set a value for the time series. If compact is True, only set the
        value if it's different from what it would be anyway.

        """
        if compact:
            current_value = self.get(time)
            if not current_value == value:
                self.d[time] = value
        else:
            self.d[time] = value

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

    def domain(self):
        """Return a (min_time, max_time) tuple."""
        if not self.d:
            raise ValueError("can't get domain of empty TimeSeries")

        # get minimum and maximum time with `iloc`
        return (self.d.iloc[0], self.d.iloc[-1])

    def __len__(self):
        """Should this return the length of time in seconds that the time
        series spans, or the number of measurements in the time
        series? For now, it's the number of measurements.

        """
        return self.n_measurements()

    def __repr__(self):
        return '<TimeSeries>\n%s\n</TimeSeries>' % \
            pprint.pformat(self.d)

    def iterintervals(self, value=None, n=2, pad=False, fillvalue=None):
        """Iterate over groups of `n` points in the time series, optionally
        only the groups where the starting value of the time series
        matches `value`.

        """
        # if value isn't a function, then make it one that returns
        # true if the the argument matches value
        if value is None:
            def value_function(x):
                return True
        elif callable(value):
            value_function = value
        else:
            def value_function(x):
                return x[0][1] == value

        # if fillvalue is not given, then use max datetime and default
        # value
        if fillvalue is None:
            fillvalue = (datetime.datetime.max, self.default())

        # tee the original iterator into n identical iterators
        streams = itertools.tee(iter(self), n)

        # advance the "cursor" on each iterator by an increasing
        # offset
        for stream_index, stream in enumerate(streams):
            for i in range(stream_index):
                next(stream)

        # now, zip the offset streams back together to yield pairs
        if pad:
            zipper = itertools.izip_longest(*streams, fillvalue=fillvalue)
        else:
            zipper = itertools.izip(*streams)
        for intervals in zipper:
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
        total_seconds = (end_time - start_time).total_seconds()

        mean = 0.0
        for (t0, duration, value) in self.iterperiods(start_time, end_time):

            # calculate contribution to weighted average for this
            # interval
            mean += (duration.total_seconds() * value)

        # return the mean value over the time period
        return mean / float(total_seconds)

    def distribution(self, start_time=None, end_time=None,
                     normalized=True, mask=None):
        """Calculate the distribution of values over the given time range from
        `start_time` to `end_time`.

        """
        if mask:
            counter = histogram.Histogram()
            mask_iterator = mask.iterperiods(start_time, end_time)
            for mask_start, mask_duration, mask_value in mask_iterator:
                mask_end = mask_start + mask_duration
                if mask_value:
                    self_iterator = self.iterperiods(mask_start, mask_end)
                    for t0, duration, value in self_iterator:
                        counter[value] += duration.total_seconds()
        else:
            # increment counter with duration of each period
            counter = histogram.Histogram()
            for t0, duration, value in self.iterperiods(start_time, end_time):
                counter[value] += duration.total_seconds()

        # divide by total duration if result needs to be normalized
        if normalized:
            return counter.normalized()

        return counter

    def _check_time_series(self, other):
        """Function used to check the type of the argument and raise an
        informative error message if it's not a TimeSeries.

        """
        if not isinstance(other, TimeSeries):
            msg = "unsupported operand types(s) for +: %s and %s" % \
                (type(self), type(other))
            raise TypeError(msg)

    def operation(self, other, function):
        """Calculate elementwise operation between two
        TimeSeries:

        operation(t) = function(self(t), other(t))

        """
        self._check_time_series(other)
        result = TimeSeries()
        for time, value in self:
            result[time] = function(value, other[time])
        for time, value in other:
            result[time] = function(self[time], value)
        return result

    def _scalar_op(self, scalar, function, **kwargs):
        """Calculate operation between a TimeSeries and a
        scalar:

        operation(t) = function(self(t), scalar)

        TODO: add option to do this in place

        """
        result = TimeSeries()
        for time, value in self:
            result[time] = function(value, scalar)
        return result

    def scale_by(self, scalar, **kwargs):
        """Multiply every element by the given scalar
        optional arguments: None
        """
        def op(x, y): return x * y
        return self._scalar_op(scalar, op, **kwargs)

    def to_bool(self, **kwargs):
        """Return the truth value of each element
        TODO: implement invert argument, if needed"""
        def op(x, invert): return bool(x)
        # by default, do not invert
        invert = kwargs.pop('invert', False)
        return self._scalar_op(invert, op, **kwargs)

    @staticmethod
    def iter_many(timeseries_list):

        q = Queue.PriorityQueue()
        for index, timeseries in enumerate(timeseries_list):
            iterator = iter(timeseries)
            q.put(iterator.next())

        while not q.empty():

            yield q.get()

            try:
                q.put(iterator.next())
            except StopIteration:
                pass

    @classmethod
    def from_many(cls, timeseries_list, operation, default_type, default_value=None):
        """Efficiently create a new time series that combines several time
        series with an operation.

        """
        result = cls(default_type=default_type, default_value=default_value)

        # create a list of the timeseries iterators
        q = Queue.PriorityQueue()
        for index, timeseries in enumerate(timeseries_list):
            iterator = iter(timeseries)
            try:
                item = (
                    iterator.next(),
                    timeseries.default(),
                    index,
                    iterator,
                )
            except StopIteration:
                pass
            else:
                q.put(item)

        # start with "empty" default state (0 if default type is int,
        # set([]) if default type is set, etc)
        state = result.default()
        while not q.empty():

            # get the next time with a measurement from queue
            (t, next_state), previous_state, index, iterator = q.get()

            # compute updated state
            state = operation(state, next_state, previous_state, index)
            result[t] = state

            # add the next measurement from the time series to the
            # queue (if there is one)
            try:
                item = (iterator.next(), next_state, index, iterator)
                q.put(item)
            except StopIteration:
                pass

        # return the time series
        return result

    @classmethod
    def from_many_sum(cls, timeseries_list):
        """Efficiently create a new time series that is the sum of many
        TimeSeries.

        """

        def increment_sum(state, next_state, previous_state, index):
            return state + (next_state - previous_state)

        return TimeSeries.from_many(timeseries_list, increment_sum, float)

    @classmethod
    def from_many_set(cls, timeseries_list):
        """Efficiently create a new time series that is the sum of many
        Binary TimeSeries.

        """

        def set_update(state, next_state, previous_state, index):
            if next_state:
                result = state.union({index})
            else:
                result = state.difference({index})
            return result

        return TimeSeries.from_many(timeseries_list, set_update, set)

    @classmethod
    def from_many_union(cls, timeseries_list):
        """Efficiently create a new time series that is the sum of many
        TimeSeries.

        """

        def combine(state, next_state, previous_state, index):
            enter_set = next_state.difference(previous_state)
            exit_set = previous_state.difference(next_state)
            return state.union(enter_set).difference(exit_set)

        return TimeSeries.from_many(timeseries_list, combine, set)

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

    def get_by_index(self, index):
        """Get the (t, value) pair of the time series by index."""
        t = self.d.iloc[index]
        return t, self.d[t]
    
    def last(self):
        """Returns the last value of the time series."""
        return self.get_by_index(-1)
