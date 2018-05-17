"""A class for manipulating time series based on measurements at
unevenly-spaced times, see:

http://en.wikipedia.org/wiki/Unevenly_spaced_time_series

"""
# standard library
import csv
import datetime
import pprint
from itertools import tee
from queue import PriorityQueue

# 3rd party
import sortedcontainers
from dateutil.parser import parse as date_parse
from future.utils import iteritems, listitems
from infinity import inf
from traces import operations

# local
from . import histogram, utils

# python 2/3 compatibility
try:
    import itertools.izip as zip
except ImportError:
    pass


# EXTEND_BACK = object()


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

    def __init__(self, data=None, default=None):
        self._d = sortedcontainers.SortedDict(data)
        self.default = default

        self.getter_functions = {
            'previous': self._get_previous,
            'linear': self._get_linear_interpolate,
        }

    def __getstate__(self):
        return {
            "data": self.items(),
            "default": self.default
        }

    def __setstate__(self, state):
        self.__init__(**state)

    def __iter__(self):
        """Iterate over sorted (time, value) pairs."""
        return iteritems(self._d)

    def __bool__(self):
        return bool(self._d)

    def is_empty(self):
        return len(self) == 0

    # def is_floating(self):
    #     """An empty TimeSeries with no specific default value is said to be
    #     "floating", since the value of the TimeSeries is
    #     undefined. Any operation that needs to look up the value of
    #     the TimeSeries is not defined on a floating TimeSeries.
    #
    #     """
    #     return (self.extend_back and len(self) == 0)

    @property
    def default(self):
        """Return the default value of the time series."""
        # if self.is_floating():
        #     msg = "can't get value of empty TimeSeries with no default value"
        #     raise KeyError(msg)
        # else:
        # if self._default == EXTEND_BACK:
        #     return self.first_item()[1]
        # else:
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
            return self.last_item()[1]
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

    def get(self, time, interpolate='previous'):
        """Get the value of the time series, even in-between measured values.

        """
        try:
            getter = self.getter_functions[interpolate]
        except KeyError:
            msg = (
                "unknown value '{}' for interpolate, "
                "valid values are in [{}]"
            ).format(interpolate, ', '.join(self.getter_functions))
            raise ValueError(msg)
        else:
            return getter(time)

    def get_item_by_index(self, index):
        """Get the (t, value) pair of the time series by index."""
        return self._d.peekitem(index)

    def last_item(self):
        """Returns the last (time, value) pair of the time series."""
        return self.get_item_by_index(-1)

    def last_key(self):
        """Returns the last time recorded in the time series"""
        return self.last_item()[0]

    def last_value(self):
        """Returns the last recorded value in the time series"""
        return self.last_item()[1]

    def first_item(self):
        """Returns the first (time, value) pair of the time series."""
        return self.get_item_by_index(0)

    def first_key(self):
        """Returns the first time recorded in the time series"""
        return self.first_item()[0]

    def first_value(self):
        """Returns the first recorded value in the time series"""
        return self.first_item()[1]

    def set(self, time, value, compact=False):
        """Set the value for the time series. If compact is True, only set the
        value if it's different from what it would be anyway.

        """
        if (len(self) == 0) or (not compact) or \
                (compact and self.get(time) != value):
            self._d[time] = value

    def set_interval(self, start, end, value, compact=False):
        """Set the value for the time series on an interval. If compact is
        True, only set the value if it's different from what it would
        be anyway.

        """
        # for each interval to render
        for i, (s, e, v) in enumerate(self.iterperiods(start, end)):
            # look at all intervals included in the current interval
            # (always at least 1)
            if i == 0:
                # if the first, set initial value to new value of range
                self.set(s, value, compact)
            else:
                # otherwise, remove intermediate key
                del self[s]

        # finish by setting the end of the interval to the previous value
        self.set(end, v, compact)

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

    def exists(self):
        """returns False when the timeseries has a None value,
        True otherwise"""
        result = TimeSeries(default=False if self.default is None else True)
        for t, v in self:
            result[t] = False if v is None else True
        return result

    def remove(self, time):
        """Allow removal of measurements from the time series. This throws an
        error if the given time is not actually a measurement point.

        """
        try:
            del self._d[time]
        except KeyError:
            raise KeyError('no measurement at %s' % time)

    def remove_points_from_interval(self, start, end):
        """Allow removal of all points from the time series within a interval
        [start:end].

        """
        for s, e, v in self.iterperiods(start, end):
            try:
                del self._d[s]
            except KeyError:
                pass

    def n_measurements(self):
        """Return the number of measurements in the time series."""
        return len(self._d)

    def __len__(self):
        """Number of points in the TimeSeries."""
        return self.n_measurements()

    def __repr__(self):
        return '<TimeSeries>\n%s\n</TimeSeries>' % \
               pprint.pformat(self._d)

    def iterintervals(self, n=2):
        """Iterate over groups of `n` consecutive measurement points in the
        time series.

        """
        # tee the original iterator into n identical iterators
        streams = tee(iter(self), n)

        # advance the "cursor" on each iterator by an increasing
        # offset, e.g. if n=3:
        #
        #                   [a, b, c, d, e, f, ..., w, x, y, z]
        #  first cursor -->  *
        # second cursor -->     *
        #  third cursor -->        *
        for stream_index, stream in enumerate(streams):
            for i in range(stream_index):
                next(stream)

        # now, zip the offset streams back together to yield tuples,
        # in the n=3 example it would yield:
        # (a, b, c), (b, c, d), ..., (w, x, y), (x, y, z)
        for intervals in zip(*streams):
            yield intervals

    @staticmethod
    def _value_function(value):

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

        return value_function

    def iterperiods(self, start=None, end=None, value=None):
        """This iterates over the periods (optionally, within a given time
        span) and yields (interval start, interval end, value) tuples.

        TODO: add mask argument here.

        """
        start, end, mask = \
            self._check_boundaries(start, end, allow_infinite=False)

        value_function = self._value_function(value)

        # get start index and value
        start_index = self._d.bisect_right(start)
        if start_index:
            start_value = self._d[self._d.iloc[start_index - 1]]
        else:
            start_value = self.default

        # get last index before end of time span
        end_index = self._d.bisect_right(end)

        interval_t0, interval_value = start, start_value

        for interval_t1 in self._d.islice(start_index, end_index):

            if value_function(interval_t0, interval_t1, interval_value):
                yield interval_t0, interval_t1, interval_value

            # set start point to the end of this interval for next
            # iteration
            interval_t0 = interval_t1
            interval_value = self[interval_t0]

        # yield the time, duration, and value of the final period
        if interval_t0 < end:
            if value_function(interval_t0, end, interval_value):
                yield interval_t0, end, interval_value

    def slice(self, start, end):
        """Return an equivalent TimeSeries that only has points between
        `start` and `end` (always starting at `start`)

        """
        start, end, mask = \
            self._check_boundaries(start, end, allow_infinite=True)

        result = TimeSeries(default=self.default)
        for t0, t1, value in self.iterperiods(start, end):
            result[t0] = value

        result[t1] = self[t1]

        return result

    def _check_regularization(self, start, end, sampling_period=None):

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

    def sample(self, sampling_period, start=None, end=None,
               interpolate='previous'):
        """Sampling at regular time periods.

        """
        start, end, mask = self._check_boundaries(start, end)

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
        start, end, mask = self._check_boundaries(start, end)

        # default to sampling_period if not given
        if window_size is None:
            window_size = sampling_period

        sampling_period = \
            self._check_regularization(start, end, sampling_period)

        # convert to datetime if the times are datetimes
        full_window = window_size * 1.  # convert to float if int or do nothing
        half_window = full_window / 2.  # divide by 2
        if (isinstance(start, datetime.datetime) and
                not isinstance(full_window, datetime.timedelta)):
            half_window = datetime.timedelta(seconds=half_window)
            full_window = datetime.timedelta(seconds=full_window)

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
            try:
                mean = self.mean(window_start, window_end)
            except TypeError as e:
                if 'NoneType' in str(e):
                    mean = None
                else:
                    raise e
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

    @staticmethod
    def rebin(binned, key_function):

        result = sortedcontainers.SortedDict()
        for bin_start, value in iteritems(binned):
            new_bin_start = key_function(bin_start)
            try:
                result[new_bin_start] += value
            except KeyError:
                result[new_bin_start] = value

        return result

    def bin(self, unit, n_units=1, start=None, end=None, mask=None,
            smaller=None, transform='distribution'):

        # return an empty sorted dictionary if there is no time span
        if mask is not None and mask.is_empty():
            return sortedcontainers.SortedDict()
        elif start is not None and start == end:
            return sortedcontainers.SortedDict()

        # use smaller if available
        if smaller:
            return self.rebin(
                smaller,
                lambda x: utils.datetime_floor(x, unit, n_units),
            )

        start, end, mask = self._check_boundaries(start, end, mask=mask)

        start = utils.datetime_floor(start, unit=unit, n_units=n_units)

        function = getattr(self, transform)
        result = sortedcontainers.SortedDict()
        for bin_start, bin_end in mask.spans_between(start, end, unit,
                                                     n_units=n_units):

            result[bin_start] = function(bin_start, bin_end,
                                         mask=mask, normalized=False)

        return result

    def mean(self, start=None, end=None, mask=None):
        """This calculated the average value of the time series over the given
        time range from `start` to `end`, when `mask` is truthy.

        """
        return self.distribution(start=start, end=end, mask=mask).mean()

    def distribution(self, start=None, end=None, normalized=True, mask=None):
        """Calculate the distribution of values over the given time range from
        `start` to `end`.

        Args:

            start (orderable, optional): The lower time bound of
                when to calculate the distribution. By default, the
                first time point will be used.

            end (orderable, optional): The upper time bound of
                when to calculate the distribution. By default, the
                last time point will be used.

            normalized (bool): If True, distribution will sum to
                one. If False and the time values of the TimeSeries
                are datetimes, the units will be seconds.

            mask (:obj:`TimeSeries`, optional): A
                domain on which to calculate the distribution.

        Returns:

            :obj:`Histogram` with the results.

        """

        start, end, mask = self._check_boundaries(start, end, mask=mask)

        counter = histogram.Histogram()
        for start, end, _ in mask.iterperiods(value=True):
            for t0, t1, value in self.iterperiods(start, end):
                duration = utils.duration_to_number(
                    t1 - t0,
                    units='seconds',
                )
                try:
                    counter[value] += duration
                except histogram.UnorderableElements as e:

                    counter = histogram.Histogram.from_dict(
                        dict(counter), key=hash)
                    counter[value] += duration

        # divide by total duration if result needs to be normalized
        if normalized:
            return counter.normalized()
        else:
            return counter

    def n_points(self, start=-inf, end=+inf, mask=None,
                 include_start=True, include_end=False, normalized=False):
        """Calculate the number of points over the given time range from
        `start` to `end`.

        Args:

            start (orderable, optional): The lower time bound of when
                to calculate the distribution. By default, start is
                -infinity.

            end (orderable, optional): The upper time bound of when to
                calculate the distribution. By default, the end is
                +infinity.

            mask (:obj:`TimeSeries`, optional): A
                domain on which to calculate the distribution.

        Returns:

             `int` with the result

        """
        # just go ahead and return 0 if we already know it regarless
        # of boundaries
        if not self.n_measurements():
            return 0

        start, end, mask = self._check_boundaries(start, end, mask=mask)

        count = 0
        for start, end, _ in mask.iterperiods(value=True):

            if include_end:
                end_count = self._d.bisect_right(end)
            else:
                end_count = self._d.bisect_left(end)

            if include_start:
                start_count = self._d.bisect_left(start)
            else:
                start_count = self._d.bisect_right(start)

            count += (end_count - start_count)

        if normalized:
            count /= float(self.n_measurements())

        return count

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
                t, value = next(iterator)
            except StopIteration:
                pass
            else:
                queue.put((t, index, value, iterator))

        # `state` keeps track of the value of the merged
        # TimeSeries. It starts with the default. It starts as a list
        # of the default value for each individual TimeSeries.
        state = [ts.default for ts in timeseries_list]
        while not queue.empty():

            # get the next time with a measurement from queue
            t, index, next_value, iterator = queue.get()

            # make a copy of previous state, and modify only the value
            # at the index of the TimeSeries that this item came from
            state = list(state)
            state[index] = next_value
            yield t, state

            # add the next measurement from the time series to the
            # queue (if there is one)
            try:
                t, value = next(iterator)
            except StopIteration:
                pass
            else:
                queue.put((t, index, value, iterator))

    @classmethod
    def iter_merge(cls, timeseries_list):
        """Iterate through several time series in order, yielding (time, list)
        tuples where list is the values of each individual TimeSeries
        in the list at time t.

        """
        # using return without an argument is the way to say "the
        # iterator is empty" when there is nothing to iterate over
        # (the more you know...)
        if not timeseries_list:
            return

        # for ts in timeseries_list:
        #     if ts.is_floating():
        #         msg = "can't merge empty TimeSeries with no default value"
        #         raise KeyError(msg)

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
        # If operation is not given then the default is the list
        # of defaults of all time series
        # If operation is given, then the default is the result of
        # the operation over the list of all defaults
        default = [ts.default for ts in ts_list]
        if operation:
            default = operation(default)

        result = cls(default=default)
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
    def from_csv(cls, filename,
                 time_column=0,
                 value_column=1,
                 time_transform=None,
                 value_transform=None,
                 skip_header=True,
                 default=None):

        # use default on class if not given
        if time_transform is None:
            time_transform = cls.csv_time_transform
        if value_transform is None:
            value_transform = cls.csv_value_transform

        result = cls(default=default)
        with open(filename) as infile:
            reader = csv.reader(infile)
            if skip_header:
                next(reader)
            for row in reader:
                time = time_transform(row[time_column])
                value = value_transform(row[value_column])
                result[time] = value
        return result

    def operation(self, other, function, **kwargs):
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
        result = TimeSeries(**kwargs)
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
            def function(x, y):
                return False if x else True
        else:
            def function(x, y):
                return True if x else False
        return self.operation(None, function)

    def threshold(self, value, inclusive=False):
        """Return True if > than treshold value (or >= threshold value if
        inclusive=True).

        """
        if inclusive:
            def function(x, y):
                return True if x >= y else False
        else:
            def function(x, y):
                return True if x > y else False
        return self.operation(value, function)

    def sum(self, other):
        """sum(x, y) = x(t) + y(t)."""
        return TimeSeries.merge(
            [self, other], operation=operations.ignorant_sum
        )

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
        """Allow a[time] = value syntax or a a[start:end]=value."""
        if isinstance(time, slice):
            return self.set_interval(time.start, time.stop, value)
        else:
            return self.set(time, value)

    def __getitem__(self, time):
        """Allow a[time] syntax."""
        if isinstance(time, slice):
            raise ValueError("Syntax a[start:end] not allowed")
        else:
            return self.get(time)

    def __delitem__(self, time):
        """Allow del[time] syntax."""
        if isinstance(time, slice):
            return self.remove_points_from_interval(time.start, time.stop)
        else:
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
        return not (self == other)

    def _check_boundary(self, value, allow_infinite, lower_or_upper):

        if lower_or_upper == 'lower':
            infinity_value = -inf
            method_name = 'first_item'
        elif lower_or_upper == 'upper':
            infinity_value = inf
            method_name = 'last_item'
        else:
            msg = '`lower_or_upper` must be "lower" or "upper", got {}'.format(
                lower_or_upper,
            )
            raise ValueError(msg)

        if value is None:
            if allow_infinite:
                return infinity_value
            else:
                try:
                    return getattr(self, method_name)()[0]
                except IndexError:
                    msg = (
                        "can't use '{}' for default {} boundary "
                        "of empty TimeSeries"
                    ).format(method_name, lower_or_upper)
                    raise KeyError(msg)
        else:
            return value

    def _check_boundaries(self, start, end, mask=None, allow_infinite=False):

        if mask is not None and mask.is_empty():
            raise ValueError('mask can not be empty')

        # if only a mask is passed in, return mask boundaries and mask
        if start is None and end is None and mask is not None:
            return mask.first_key, mask.last_key, mask

        # replace with defaults if not given
        start = self._check_boundary(start, allow_infinite, 'lower')
        end = self._check_boundary(end, allow_infinite, 'upper')

        if start >= end:
            msg = "start can't be >= end ({} >= {})".format(start, end)
            raise ValueError(msg)

        start_end_mask = TimeSeries(default=False)
        start_end_mask[start] = True
        start_end_mask[end] = False

        if mask is None:
            mask = start_end_mask
        else:
            mask = mask & start_end_mask

        return start, end, mask

    def distribution_by_hour_of_day(self,
                                    first=0, last=23,
                                    start=None, end=None):

        start, end, mask = self._check_boundaries(start, end)

        result = []
        for hour in range(first, last + 1):
            mask = hour_of_day(start, end, hour)
            histogram = self.distribution(mask=mask)
            result.append((hour, histogram))

        return result

    def distribution_by_day_of_week(self,
                                    first=0, last=6,
                                    start=None, end=None):

        start, end, mask = self._check_boundaries(start, end)

        result = []
        for week in range(first, last + 1):
            mask = day_of_week(start, end, week)
            histogram = self.distribution(mask=mask)
            result.append((week, histogram))

        return result


def hour_of_day(start, end, hour):

    # start should be date, or if datetime, will use date of datetime
    floored = utils.datetime_floor(start)

    domain = TimeSeries(default=False)
    for day_start in utils.datetime_range(floored, end, 'days',
                                          inclusive_end=True):
        interval_start = day_start + datetime.timedelta(hours=hour)
        interval_end = interval_start + datetime.timedelta(hours=1)
        domain[interval_start] = True
        domain[interval_end] = False

    result = domain.slice(start, end)
    result[end] = False
    return result


def day_of_week(start, end, weekday):

    # allow weekday name or number
    number = utils.weekday_number(weekday)

    # start should be date, or if datetime, will use date of datetime
    floored = utils.datetime_floor(start)

    next_week = floored + datetime.timedelta(days=7)
    for day in utils.datetime_range(floored, next_week, 'days'):
        if day.weekday() == number:
            first_day = day
            break

    domain = TimeSeries(default=False)
    for week_start in utils.datetime_range(first_day, end, 'weeks',
                                           inclusive_end=True):
        interval_start = week_start
        interval_end = interval_start + datetime.timedelta(days=1)
        domain[interval_start] = True
        domain[interval_end] = False

    result = domain.slice(start, end)
    result[end] = False
    return result
