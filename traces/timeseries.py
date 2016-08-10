"""A class for manipulating [time series based on measurements at
unevenly-spaced
times](http://en.wikipedia.org/wiki/Unevenly_spaced_time_series).

For an discussion of visualizing this type of thing, see [Representing
Unevenly-Spaced Time Series Data for Visualization and Interactive
Exploration](http://hcil2.cs.umd.edu/trs/2005-01/2005-01.pdf#healthycakes)
by Aleks Aris and others.

"""

# standard library
import datetime
import pprint
from itertools import tee
try:
    import itertools.izip as zip
except ImportError:
    pass

from queue import PriorityQueue
from future.utils import listitems, iteritems

# 3rd party
import sortedcontainers

# local
from . import histogram
from . import utils


# TODO: Good name? Traces vs time series vs others
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

    def __init__(self, data=None, domain=None):
        self.domain = None
        self.set_domain(domain)
        if self.is_data_in_domain(data):
            self.d = sortedcontainers.SortedDict(data)
        else:
            raise ValueError("Data given are not in domain.")

    def set_domain(self, domain):
        """Create a time series with default values False
        that represents the domain. domain has to be either
        None, list or list of list"""

        # TODO: Redefine domain so that when domain=[a, b], b is also in the domain?
        # TODO: Timeseries might not be a good object to define domain
        # because it's not a closed interval. Try
        # http://pyinterval.readthedocs.io/en/latest/install.html

        if domain is None:
            ts = None

        else:
            ts = DefaultTimeSeries(default_values=False)
            if any(isinstance(i, list) for i in domain):
                for begin_time, end_time in domain:
                    if begin_time is None:
                        ts.default_values = True
                    else:
                        ts[begin_time] = True

                    if end_time is not None:
                        ts[end_time] = False
            else:
                begin_time, end_time = domain
                if (begin_time is None) and (end_time is None):
                    ts = None
                else:
                    if begin_time is None:
                        ts.default_values = True
                    else:
                        ts[begin_time] = True

                    if end_time is not None:
                        ts[end_time] = False

        if hasattr(self, 'd'):
            if not self.is_data_in_domain(self.d, domain=ts):
                raise ValueError("Data are not in the domain.")

        self.domain = ts

    def get_domain(self):
        """Return the domain as None, list, or list of list"""

        if self.domain is None:
            return None

        result = []
        if self.domain.default() is True:
            result.append([None, self.domain.get_by_index(0)[0]])

        for (t0, v0), (t1, v1) in self.domain.iterintervals(value=True):
            result.append([t0, t1])

        if self.domain.get_by_index(-1)[1] is True:
            result.append([self.domain.get_by_index(-1)[0], None])

        return result if len(result) > 1 else result[0]

    def is_data_in_domain(self, data, domain=None):
        """Check if data (sorteddict/dict) is inside the domain"""
        if domain is None:
            domain = self.domain

        temp = sortedcontainers.SortedDict(data)
        if domain is not None:
            for key in temp.keys():
                if domain[key] is not True:
                    return False

        return True

    def is_time_in_domain(self, *args):
        """Check if time is inside the domain"""
        if self.domain is not None:
            for time in args:
                if time is None:
                    continue
                elif self.domain[time] is not True:
                    return False

        return True

    def __iter__(self):
        """Iterate over sorted (time, value) pairs."""
        return iteritems(self.d)

    def default(self):
        """Return the default value of the time series."""
        if len(self) == 0:
            raise ValueError("There is no data in the TimeSeries.")
        else:
            return self.d.values()[0]

    def get(self, time):
        """Get the value of the time series, even in-between measured values.

        """
        if not self.is_time_in_domain(time):
            raise ValueError("{} is outside of the domain."
                             .format(time))

        index = self.d.bisect_right(time)
        if index > 0:
            previous_measurement_time = self.d.iloc[index - 1]
            return self.d[previous_measurement_time]
        elif index == 0:
            return self.default()
        else:
            return "Something is wrong."
            # TODO: Check if this will ever happen

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
        if not self.is_time_in_domain(time):
            raise ValueError("({}, {}) is outside of the domain."
                             .format(time, value))

        if (len(self) == 0) or (not compact) or (compact and self.get(time) != value):
            self.d[time] = value

    def update(self, data, compact=False):
        """Set the values of TimeSeries using a list. Compact it if necessary."""

        if not self.is_data_in_domain(data):
            raise ValueError("Data are not in the domain.")

        self.d.update(data)
        if compact:
            self.compact()

    def compact(self):
        """Convert this instance to a compact version: the value will be the
        same at all times, but repeated measurements are discarded.

        """
        previous_value = None
        remove_item = []
        for time, value in self.d.items():
            if value == previous_value:
                remove_item.append(time)
            previous_value = value
        for item in remove_item:
            del self[item]

    def items(self):
        """ts.items() -> list of the (key, value) pairs in ts, as 2-tuples"""
        return listitems(self.d)  # Python 3 returns itemView instead of a list

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
        # TODO: How would this change with domain?
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
        streams = tee(iter(self), n)

        # advance the "cursor" on each iterator by an increasing
        # offset
        for stream_index, stream in enumerate(streams):
            for i in range(stream_index):
                next(stream)

        # now, zip the offset streams back together to yield tuples
        for intervals in zip(*streams):
            if value_function(intervals):
                yield intervals

    def iterperiods(self, start_time=None, end_time=None):
        """This iterates over the periods (optionally, within a given time
        span) and yields (time, duration, value) tuples.

        """
        # TODO: How would this change with domain?
        # use first/last measurement as start/end time if not given
        if start_time is None:
            start_time = self.d.iloc[0]
        if end_time is None:
            end_time = self.d.iloc[-1]

        # get start index and value
        start_index = self.d.bisect_right(start_time)
        if start_index > 0:
            start_value = self.d[self.d.iloc[start_index - 1]]
        elif start_index == 0:
            start_value = self.d[self.d.iloc[0]]
        else:
            raise ValueError("start_index is negative for some reason")  # TODO: Verify that this will not happen.

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
                "Received start_time={} and end_time={}."
            ).format(start_time, end_time)
            raise ValueError(message)

        if not self.is_time_in_domain(start_time, end_time):
            message = (
                          "Can't slice a Timeseries when end_time or "
                          "start_time is outside of the domain. "
                          "Received start_time={} and end_time={}. "
                          "Domain is {}."
                      ).format(start_time, end_time, self.get_domain())
            raise ValueError(message)

        result = TimeSeries()

        # since start_time > end_time, this will always have at least
        # one item, so `value` gets set for following line
        for dt, duration, value in self.iterperiods(start_time, end_time):
            result[dt] = value
        result[end_time] = self[end_time]

        return result

    def regularize(self, sampling_period, start_time=None, end_time=None):
        """Sampling at regular time periods

        Output: Dict that can be converted into pandas.Series
        directly by calling pandas.Series(Dict)

        """
        if start_time > end_time:
            msg = (
                "Can't regularize a Timeseries when end_time <= start_time. "
                "Received start_time={} and end_time={}."
            ).format(start_time, end_time)
            raise ValueError(msg)

        if not self.is_time_in_domain(start_time, end_time):
            message = (
                          "Can't regularize a Timeseries when end_time or "
                          "start_time is outside of the domain. "
                          "Received start_time={} and end_time={}. "
                          "Domain is {}."
                      ).format(start_time, end_time, self.get_domain())
            raise ValueError(message)

        if sampling_period <= 0:
            msg = "Can't regularize a Timeseries when sampling_period <= 0."
            raise ValueError(msg)

        if sampling_period > utils.duration_to_number(end_time-start_time):
            msg = "Can't regularize a Timeseries when sampling_period " \
                  "is greater than the duration between start_time and end_time."
            raise ValueError(msg)

        if isinstance(start_time, datetime.datetime):
            if not isinstance(sampling_period, int):
                msg = "Can't regularize a Timeseries when " \
                      "the class of the time is datetime and " \
                      "sampling_period is not an integer."
                raise TypeError(msg)
            period_time = datetime.timedelta(seconds=sampling_period)
        else:
            period_time = sampling_period

        if start_time is None:
            start_time = self.get_by_index(0)[0]
        if end_time is None:
            end_time = self.last()[0]

        result = {}
        current_time = start_time
        while current_time <= end_time:
            result[current_time] = self[current_time]
            current_time += period_time
        return result

    def moving_average(self, window_size, sampling_period, start_time, end_time):
        """Averaging over regular intervals

        Output: Dict that can be converted into pandas.Series
        directly by calling pandas.Series(Dict)

        """
        if start_time > end_time:
            msg = (
                "Can't calculate moving average of a Timeseries "
                "when end_time <= start_time. "
                "Received start_time={} and end_time={}."
            ).format(start_time, end_time)
            raise ValueError(msg)

        if not self.is_time_in_domain(start_time, end_time):
            message = (
                          "Can't calculate moving average of "
                          "a Timeseries when end_time or "
                          "start_time is outside of the domain. "
                          "Received start_time={} and end_time={}. "
                          "Domain is {}."
                      ).format(start_time, end_time, self.get_domain())
            raise ValueError(message)

        if (window_size <= 0) or (sampling_period <= 0):
            msg = "Can't calculate moving average of a Timeseries " \
                  "when window_size <= 0 or sampling_period <= 0."
            raise ValueError(msg)

        if sampling_period > utils.duration_to_number(end_time-start_time):
            msg = "Can't calculate moving average of a Timeseries " \
                  "when sampling_period is greater than " \
                  "the duration between start_time and end_time."
            raise ValueError(msg)

        half = float(window_size) / 2

        if isinstance(start_time, datetime.datetime):
            if not isinstance(sampling_period, int):
                msg = "Can't calculate moving average of a Timeseries " \
                      "when the class of the time is datetime and " \
                      "sampling_period is not an integer."
                raise TypeError(msg)

            buffer_time = datetime.timedelta(seconds=half)
            period_time = datetime.timedelta(seconds=sampling_period)
        else:
            buffer_time = half
            period_time = sampling_period

        result = {}
        current_time = start_time
        while current_time <= end_time:
            window_start = current_time - buffer_time
            window_end = current_time + buffer_time
            mean = self.mean(window_start, window_end)
            result[current_time] = mean
            current_time += period_time
        return result

    def mean(self, start_time, end_time):
        """This calculated the average value of the time series over the given
        time range from `start_time` to `end_time`.

        """

        if start_time > end_time:
            msg = (
                "Can't calculate mean of a Timeseries "
                "when end_time <= start_time. "
                "Received start_time={} and end_time={}."
            ).format(start_time, end_time)
            raise ValueError(msg)

        if not self.is_time_in_domain(start_time, end_time):
            message = (
                          "Can't calculate mean of a Timeseries "
                          "when end_time or "
                          "start_time is outside of the domain. "
                          "Received start_time={} and end_time={}. "
                          "Domain is {}."
                      ).format(start_time, end_time, self.get_domain())
            raise ValueError(message)

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
        if start_time > end_time:
            msg = (
                "Can't calculate distribution of a Timeseries "
                "when end_time <= start_time. "
                "Received start_time={} and end_time={}."
            ).format(start_time, end_time)
            raise ValueError(msg)

        if not self.is_time_in_domain(start_time, end_time):
            message = (
                "Can't calculate distribution of a Timeseries "
                "when end_time or "
                "start_time is outside of the domain. "
                "Received start_time={} and end_time={}. "
                "Domain is {}."
            ).format(start_time, end_time, self.get_domain())
            raise ValueError(message)

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
        # ignore all empty TimeSeries
        clean_timeseries_list = [ts for ts in timeseries_list if len(ts) > 0]

        # This function mostly wraps _iter_merge, the main point of
        # this is to deal with the case of tied times, where we only
        # want to yield the last list of values that occurs for any
        # group of tied times.
        index, previous_t, previous_state = -1, object(), object()
        for index, (t, state) in enumerate(cls._iter_merge(clean_timeseries_list)):
            if index > 0 and t != previous_t:
                yield previous_t, previous_state
            previous_t, previous_state = t, state

        # only yield final thing if there was at least one element
        # yielded by _iter_merge
        if index > -1:
            yield previous_t, previous_state

    @classmethod
    def merge(cls, ts_list, compact=False, operation=None):
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

    @classmethod
    def from_many_sum(cls, timeseries_list, compact=False):
        """Efficiently create a new time series that is the sum of many
        TimeSeries.

        """
        result = cls()
        for t, merged in cls.iter_merge(timeseries_list):
            result.set(t, sum(merged), compact=compact)
        return result

    @classmethod
    def from_many_union(cls, timeseries_list, compact=False):
        """Efficiently create a new time series that is the sum of many
        TimeSeries.

        """
        result = cls()
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

    def __eq__(self, other):
        return self.items() == other.items()


class DefaultTimeSeries(TimeSeries):

    def __init__(self, default_values=None):
        TimeSeries.__init__(self)
        self.default_values = default_values

    def default(self):
        return self.default_values
