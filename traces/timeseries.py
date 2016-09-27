"""A class for manipulating time series based on measurements at
unevenly-spaced times, see:

http://en.wikipedia.org/wiki/Unevenly_spaced_time_series

"""
# standard library
import datetime
import pprint
from itertools import tee
import csv
try:
    import itertools.izip as zip
except ImportError:
    pass
from copy import deepcopy
from queue import PriorityQueue
from future.utils import listitems, iteritems

# 3rd party
import sortedcontainers
from dateutil.parser import parse as date_parse
from infinity import inf


# local
from . import histogram
from . import utils
from .domain import Domain
from . import masks

EXTEND_BACK = object()


class TimeSeries(object):
    """A class to help manipulate and analyze time series that are the
    result of taking measurements at irregular points in time. For
    example, here would be a simple time series that starts at 8am and
    goes to 9:59am:

    >>> ts = TimeSeries()
    >>> ts['8:00am'] = 0
    >>> ts['8:47am'] = 1
    >>> ts['8:51am'] = 0
    >>> ts['9:15am'] = 1
    >>> ts['9:59am'] = 0

    The value of the time series is the last recorded measurement: for
    example, at 8:05am the value is 0 and at 8:48am the value is 1. So:

    >>> ts['8:05am']
    0

    >>> ts['8:48am']
    1

    There are also a bunch of things for operating on another time
    series: sums, difference, logical operators and such.

    """

    def __init__(self, data=None, domain=None, default=EXTEND_BACK):
        self._d = sortedcontainers.SortedDict(data)
        self.default = default
        self.domain = domain

    @property
    def domain(self):
        """Return the domain"""
        return self._domain

    @domain.setter
    def domain(self, domain):
        """Set the domain for this TimeSeries.

        Args:
            domain (:ref:`Domain <domain>`): the new domain.

        """
        if isinstance(domain, Domain):
            self._domain = domain
        else:
            self._domain = Domain(domain)

        self._check_data()

    def _check_data(self):
        """Check if data (sorteddict/dict) is inside the domain"""
        for t, v in self:
            baddies = []
            if t not in self.domain:
                baddies.append(t)
            if baddies:
                msg = '{} times are not in the domain'.format(len(baddies))
                raise ValueError(msg)

    def __iter__(self):
        """Iterate over sorted (time, value) pairs."""
        return iteritems(self._d)

    @property
    def default(self):
        """Return the default value of the time series."""
        if self._default == EXTEND_BACK and self.n_measurements() == 0:
            msg = "can't get value without a measurement (or a default)"
            raise KeyError(msg)
        else:
            if self._default == EXTEND_BACK:
                return self.first()[1]
            else:
                return self._default

    @default.setter
    def default(self, value):
        """Set the default value of the time series."""
        self._default = value

    def _get_linear_interpolate(self, time):
        right_index = self._d.bisect_right(time)
        left_index = right_index - 1
        if left_index < 0:
            return self.default
        elif right_index == len(self._d):
            # right of last measurement
            return self.last()[1]
        else:
            left_time = self._d.iloc[left_index]
            left_value = self._d[left_time]
            right_time = self._d.iloc[right_index]
            right_value = self._d[right_time]
            dt_interval = right_time - left_time
            dt_start = time - left_time
            if isinstance(dt_interval, datetime.timedelta):
                dt_interval = dt_interval.total_seconds()
                dt_start = dt_start.total_seconds()
            slope = float(right_value - left_value) / dt_interval
            value = slope * dt_start + left_value
            return value

    def _get_previous(self, time):
        right_index = self._d.bisect_right(time)
        left_index = right_index - 1
        if right_index > 0:
            left_time = self._d.iloc[left_index]
            left_value = self._d[left_time]
            return left_value
        elif right_index == 0:
            return self.default
        else:
            msg = (
                'self._d.bisect_right({}) returned a negative value. '
                """This "can't" happen: please file an issue at """
                'https://github.com/datascopeanalytics/traces/issues'
            ).format(time)
            raise ValueError(msg)

    def get(self, time, interpolate=None):
        """Get the value of the time series, even in-between measured values.

        """
        if time not in self.domain:
            msg = "{} is outside of the domain.".format(time)
            raise KeyError(msg)

        if interpolate is None:
            return self._get_previous(time)
        elif interpolate == 'linear':
            return self._get_linear_interpolate(time)
        else:
            msg = "unknown value '{}' for interpolate".format(interpolate)
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
        if time not in self.domain:
            raise KeyError("{} is outside of the domain.".format(time))

        if (len(self) == 0) or (not compact) or \
                (compact and self.get(time) != value):
            self._d[time] = value

    def compact(self):
        """Convert this instance to a compact version: the value will be the
        same at all times, but repeated measurements are discarded.

        """
        previous_value = object()
        redundant = []
        for time, value in self:
            if value == previous_value:
                redundant.append(time)
            previous_value = value
        for time in redundant:
            del self[time]

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
        return '<TimeSeries>\n%s\n</TimeSeries>' % \
            pprint.pformat(self._d)

    def iterintervals(self, n=2):
        """Iterate over groups of `n` consecutive measurement points in the
        time series, optionally only the groups where the starting
        value of the time series matches `value`.

        """
        # tee the original iterator into n identical iterators
        streams = tee(iter(self), n)

        # advance the "cursor" on each iterator by an increasing
        # offset
        for stream_index, stream in enumerate(streams):
            for i in range(stream_index):
                next(stream)

        # now, zip the offset streams back together to yield tuples
        for intervals in zip(*streams):
            yield intervals

    def iterperiods(self, start=None, end=None, value=None):
        """This iterates over the periods (optionally, within a given time
        span) and yields (interval start, interval end, value) tuples.

        Will only yield time intervals that are not length 0 that are
        within the domain.

        """
        start, end = self._check_start_end(start, end, allow_infinite=True)

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
            start_value = self.default

        # get last measurement before end of time span
        end_index = self._d.bisect_right(end)

        # look over each interval of time series within the
        # region. Use the region start time and value to begin
        ts_interval_closes = set(self._d.islice(start_index, end_index))
        domain_interval_opens = set(
            b for (b, e) in self.domain.intervals() if b > start)
        iter_time = sorted(
            list(ts_interval_closes.union(domain_interval_opens)))

        int_t0, int_value = start, start_value

        for int_t1 in iter_time:

            try:
                domain_t0, domain_t1 = self.domain.get_interval(int_t0)
            except KeyError:
                pass
            else:
                if domain_t1 < int_t1:
                    clipped_t1 = domain_t1
                else:
                    clipped_t1 = int_t1

                # yield the time, duration, and value of the period
                nonzero = (clipped_t1 != int_t0)
                if nonzero and value_function(int_t0, clipped_t1, int_value):
                    yield int_t0, clipped_t1, int_value

            # set start point to the end of this interval for next
            # iteration
            int_t0 = int_t1
            int_value = self[int_t0]

        # yield the time, duration, and value of the final period
        if int_t0 < end:

            try:
                domain_t0, domain_t1 = self.domain.get_interval(int_t0)
            except KeyError:
                pass
            else:
                if domain_t1 < end:
                    end = domain_t1

                nonzero = (end != int_t0)
                if nonzero and value_function(int_t0, end, int_value):
                    yield int_t0, end, int_value

    def slice(self, start, end, slice_domain=True):
        """Return a slice of the time series that has a first reading at
        `start` and a last reading at `end`.

        """
        start, end = self._check_start_end(start, end, allow_infinite=True)

        if start > self.domain.end() or end < self.domain.start():
            message = (
                "Can't slice a Timeseries when end and "
                "start are outside of the domain. "
                "Received start={} and end={}. "
                "Domain is {}."
            ).format(start, end, self.domain)
            raise ValueError(message)

        result = TimeSeries()
        if start in self.domain:
            result[start] = self[start]
        for time, value in self.items():
            if (time > start) and (time <= end):
                result[time] = value

            if time > end:
                break

        if slice_domain:
            result.domain = self.domain.slice(start, end)

        return result

    def _check_regularization(self, start, end, sampling_period=None):

        if self.domain.n_intervals() > 1:
            raise NotImplementedError('Domain is not connected')

        if start < self.domain.start() or end > self.domain.end():
            message = (
                "end or start is outside of the domain. "
                "Received start={} and end={}. "
                "Domain is {}."
            ).format(start, end, self.domain)
            raise ValueError(message)

        # only do these checks if sampling period is given
        if sampling_period is not None:

            # cast to both seconds and timedelta for error checking
            if isinstance(sampling_period, datetime.timedelta):
                sampling_period_seconds = sampling_period.total_seconds()
                sampling_period_timedelta = sampling_period
            else:
                sampling_period_seconds = sampling_period
                sampling_period_timedelta = \
                    datetime.timedelta(seconds=sampling_period)

            if sampling_period_seconds <= 0:
                msg = "sampling_period must be > 0"
                raise ValueError(msg)

            if sampling_period_seconds > utils.duration_to_number(end - start):
                msg = "sampling_period " \
                      "is greater than the duration between " \
                      "start and end."
                raise ValueError(msg)

            if isinstance(start, datetime.datetime):
                sampling_period = sampling_period_timedelta
            else:
                sampling_period = sampling_period_seconds

        return sampling_period

    def sample(self, sampling_period, start=None, end=None, interpolate=None):
        """Sampling at regular time periods.

        """
        start, end = self._check_start_end(start, end)

        sampling_period = \
            self._check_regularization(start, end, sampling_period)

        result = []
        current_time = start
        while current_time <= end:
            value = self.get(current_time, interpolate=interpolate)
            result.append((current_time, value))
            current_time += sampling_period
        return result

    def moving_average(self, sampling_period,
                       window_size=None,
                       start=None, end=None,
                       placement='center',
                       pandas=False):
        """Averaging over regular intervals

        """
        start, end = self._check_start_end(start, end)

        # default to sampling_period if not given
        if window_size is None:
            window_size = sampling_period

        sampling_period = \
            self._check_regularization(start, end, sampling_period)

        # convert to datetime if the times are datetimes
        half_window = float(window_size) / 2
        full_window = float(window_size)
        if isinstance(start, datetime.datetime):
            half_window = datetime.timedelta(seconds=half_window)
            full_window = datetime.timedelta(seconds=full_window)

        # create a copy with a domain that is wide enough to
        # accomodate the averaging window. TODO: get rid of this copy.
        temp = deepcopy(self)
        temp.default = self.default
        temp.domain = Domain(
            min(start, self.domain.lower) - full_window,
            max(end, self.domain.upper) + full_window,
        )

        result = []
        current_time = start
        while current_time <= end:

            if placement == 'center':
                window_start = current_time - half_window
                window_end = current_time + half_window
            elif placement == 'left':
                window_start = current_time
                window_end = current_time + full_window
            elif placement == 'right':
                window_start = current_time - full_window
                window_end = current_time
            else:
                msg = 'unknown placement "{}"'.format(placement)
                raise ValueError(msg)

            # calculate mean over window and add (t, v) tuple to list
            mean = temp.mean(window_start, window_end)
            result.append((current_time, mean))

            current_time += sampling_period

        # convert to pandas Series if pandas=True
        if pandas:

            try:
                import pandas as pd
            except ImportError:
                msg = "can't have pandas=True if pandas is not installed"
                raise ImportError(msg)

            result = pd.Series(
                [v for t, v in result],
                index=[t for t, v in result],
            )

        return result

    def mean(self, start=None, end=None):
        """This calculated the average value of the time series over the given
        time range from `start` to `end`.

        """
        start, end = self._check_start_end(start, end)

        self._check_regularization(start, end)

        total_seconds = utils.duration_to_number(end - start)

        mean = 0.0
        for (t0, t1, value) in self.iterperiods(start, end):
            # calculate contribution to weighted average for this
            # interval
            try:
                mean += (utils.duration_to_number(t1 - t0) * value)
            except TypeError:
                msg = "Can't take mean of non-numeric type (%s)" % type(value)
                raise TypeError(msg)

        # return the mean value over the time period
        return mean / float(total_seconds)

    def distribution(self, start=None, end=None,
                     normalized=True, mask=None):
        """Calculate the distribution of values over the given time range from
        `start` to `end`.

        Args:

            start (orderable, optional): The lower time bound of
                when to calculate the distribution. By default, the
                start of the domain will be used.

            end (orderable, optional): The upper time bound of
                when to calculate the distribution. By default, the
                end of the domain will be used.

            normalized (bool): If True, distribution will sum to
                one. If False and the time values of the TimeSeries
                are datetimes, the units will be seconds.

            mask (:obj:`Domain` or :obj:`TimeSeries`, optional): A
                Domain on which to calculate the distribution. This
                Domain is combined with a logical and with either the
                (start, end) time domain, if given, or the domain of
                the TimeSeries.

        Returns:

            :obj:`Histogram` with the results.

        """
        start, end = self._check_start_end(start, end)

        # if a TimeSeries is given as mask, convert to a domain
        if isinstance(mask, TimeSeries):
            mask = mask.to_domain()

        # logical and with start, end time domain
        distribution_mask = Domain([start, end])
        if mask:
            distribution_mask &= mask

        counter = histogram.Histogram()
        for start, end in distribution_mask.intervals():
            for t0, t1, value in self.iterperiods(start, end):
                counter[value] += utils.duration_to_number(
                    t1 - t0,
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
        state = [ts.default for ts in timeseries_list]
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

        domain = timeseries_list[0].domain
        for ts in timeseries_list:
            if len(ts) == 0:
                raise ValueError("Can't merge empty TimeSeries.")
            if not domain == ts.domain:
                raise ValueError(
                    "The domains of the TimeSeries are not the same.")

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

    @staticmethod
    def csv_time_transform(raw):
        return date_parse(raw)

    @staticmethod
    def csv_value_transform(raw):
        return str(raw)

    @classmethod
    def from_csv(cls, filename, time_column, value_column,
                 time_transform=None,
                 value_transform=None,
                 skip_header=True):

        # use default on class if not given
        if time_transform is None:
            time_transform = cls.csv_time_transform
        if value_transform is None:
            value_transform = cls.csv_value_transform

        result = cls()
        with open(filename) as infile:
            reader = csv.reader(infile)
            if skip_header:
                reader.next()
            for row in reader:
                time = time_transform(row[time_column])
                value = value_transform(row[value_column])
                result[time] = value
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

    def to_domain(self, start=None, end=None):
        """"""
        intervals = []
        iterator = self.iterperiods(start=start, end=end)
        for t0, t1, value in iterator:
            if value:
                intervals.append((t0, t1))
        return Domain(intervals)

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
        return TimeSeries.merge([self, other], operation=sum)

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

    def __ne__(self, other):
        return not(self == other)

    def _check_boundary(self, value, allow_infinite, lower):
        infinity_value, first_or_last = {
            'lower': (-inf, 'first'),
            'upper': (inf, 'last'),
        }[lower]
        if value is None:
            if getattr(self.domain, lower) == infinity_value:
                if allow_infinite:
                    return infinity_value
                else:
                    return getattr(self, first_or_last)()[0]
            else:
                return getattr(self.domain, lower)
        else:
            return value

    def _check_start_end(self, start, end, allow_infinite=False):

        # replace with defaults if not given
        start = self._check_boundary(start, allow_infinite, 'lower')
        end = self._check_boundary(end, allow_infinite, 'upper')

        if start >= end:
            msg = "start can't be >= end ({} >= {})".format(start, end)
            raise ValueError(msg)

        return start, end

    def distribution_by_hour_of_day(self,
                                    first=0, last=23,
                                    start=None, end=None):

        start, end = self._check_start_end(start, end)

        result = []
        for hour in range(first, last + 1):
            mask = masks.hour_of_day(start, end, hour)
            histogram = self.distribution(mask=mask)
            result.append((hour, histogram))

        return result

    def distribution_by_day_of_week(self,
                                    first=0, last=6,
                                    start=None, end=None):

        start, end = self._check_start_end(start, end)

        result = []
        for week in range(first, last + 1):
            mask = masks.day_of_week(start, end, week)
            histogram = self.distribution(mask=mask)
            result.append((week, histogram))

        return result
