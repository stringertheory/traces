"""A class for manipulating time series based on measurements at
unevenly-spaced times, see:

http://en.wikipedia.org/wiki/Unevenly_spaced_time_series

"""

import contextlib
import csv
import datetime
import itertools
from queue import PriorityQueue

from sortedcontainers import SortedDict

from . import histogram, infinity, operations, plot, utils

NotGiven = object()


class TimeSeries:
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
        self._d = SortedDict(data)
        self.default = default
        self.getter_functions = {
            "previous": self._get_previous,
            "linear": self._get_linear_interpolate,
        }

    def __getstate__(self):
        return {
            "data": self.items(),
            "default": self.default,
        }

    def __setstate__(self, state):
        self.__init__(**state)

    def __iter__(self):
        """Iterate over sorted (time, value) pairs."""
        return iter(self.items())

    def __bool__(self):
        return bool(self._d)

    def is_empty(self):
        return len(self) == 0

    @staticmethod
    def linear_interpolate(v0, v1, t):
        return v0 + t * (v1 - v0)

    @staticmethod
    def scaled_time(t0, t1, time):
        return (time - t0) / (t1 - t0)

    def _get_linear_interpolate(self, time):
        right_index = self._d.bisect_right(time)
        left_index = right_index - 1
        if left_index < 0:  # before first measurement
            return self.default
        elif right_index == len(self._d):  # after last measurement
            return self.last_value()
        else:
            left_time, left_value = self._d.peekitem(left_index)
            right_time, right_value = self._d.peekitem(right_index)
            t = self.scaled_time(left_time, right_time, time)
            return self.linear_interpolate(left_value, right_value, t)

    def _get_previous(self, time):
        right_index = self._d.bisect_right(time)
        left_index = right_index - 1
        if right_index > 0:
            _, left_value = self._d.peekitem(left_index)
            return left_value
        elif right_index == 0:
            return self.default
        else:  # pragma: no cover
            msg = (
                f"self._d.bisect_right({time}) returned a negative value. "
                """This "can't" happen: please help by filing an issue."""
            )
            raise ValueError(msg)

    def get(self, time, interpolate="previous"):
        """Get the value of the time series, even in-between measured values."""
        try:
            getter = self.getter_functions[interpolate]
        except KeyError as error:
            getter_string = ", ".join(self.getter_functions)
            msg = (
                f"unknown value '{interpolate}' for interpolate, "
                f"valid values are in [{getter_string}]"
            )
            raise ValueError(msg) from error
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
        if (
            (len(self) == 0)
            or (not compact)
            or (compact and self.get(time) != value)
        ):
            self._d[time] = value

    def set_interval(self, start, end, value, compact=False):
        """Sets the value for the time series within a specified time
        interval.

        Args:

            start: The start time of the interval, inclusive
            end: The end time of the interval, exclusive.
            value: The value to set within the interval.
            compact (optional): If compact is True, only set the value
                if it's different from what it would be anyway. Defaults
                to False.

        Raises:

            ValueError: If the start time is equal or after the end
            time, indicating an invalid interval.

        Example:

            >>> ts = TimeSeries(data=[(1, 5), (3, 2), (5, 4), (6, 1)])
            >>> ts.set_interval(2, 6, 3)
            >>> ts
            TimeSeries({1: 5, 2: 3, 6: 1})

        Note:

            The method sets the value over the interval by removing
            measurements points from the time series between start and
            end (exclusive), rather than changing the value of any
            intermediate points to equal the value.

        """
        if start >= end:
            msg = f"start must be less than end, got start={start!r} and end={end!r}"
            raise ValueError(msg)

        end_value = self[end]

        # delete all intermediate items between start and end
        for t in list(self._d.irange(start, end, inclusive=(False, False))):
            del self[t]

        self.set(start, value, compact)
        self.set(end, end_value, compact)

    def compact(self):
        """Convert this instance to a "compact" version: the value
        will be the same at all times, but repeated measurements are
        discarded.

        Compacting the time series can significantly reduce the length
        and memory usage for data with many repeated values.

        No arguments are required for this method, and it modifies the
        time series in place.

        Example:
          >>> ts = TimeSeries(data=[(1, 5), (2, 5), (5, 5), (6, 1)])
          >>> ts.compact()
          >>> ts
          TimeSeries({1: 5, 6: 1})

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
        return self._d.items()

    def exists(self):
        """returns False when the timeseries has a None value, True
        otherwise

        """

        # todo: this needs a better name. mark exists as deprecated

        result = TimeSeries(default=self.default is not None)
        for t, v in self:
            result[t] = v is not None
        return result

    def remove(self, time):
        """Allow removal of measurements from the time series. This throws an
        error if the given time is not actually a measurement point.

        """
        try:
            del self._d[time]
        except KeyError as error:
            msg = f"no measurement at {time}"
            raise KeyError(msg) from error

    def remove_points_from_interval(self, start, end):
        """Allow removal of all points from the time series within a interval
        [start:end].

        """

        # todo: consider whether this key error should be suppressed

        for s, _e, _v in self.iterperiods(start, end):
            with contextlib.suppress(KeyError):
                del self._d[s]

    def n_measurements(self):
        """Return the number of measurements in the time series."""
        return len(self._d)

    def __len__(self):
        """Number of points in the TimeSeries."""
        return self.n_measurements()

    def __repr__(self):
        """A detailed string representation for debugging."""

        # todo: show default in string representation

        def format_item(item):
            return "{!r}: {!r}".format(*item)

        items = dict(self._d.items())
        return f"{type(self).__name__}(default={self.default!r}, {items!r})"

    def __str__(self):
        """A human-readable string representation (truncated if it gets too
        long).

        """

        # todo: show default in string representation

        def format_item(item):
            return "{!s}: {!s}".format(*item)

        MAX_LENGTH = 20
        half = MAX_LENGTH // 2
        if len(self) > MAX_LENGTH:
            one = ", ".join(format_item(_) for _ in self._d.items()[:half])
            two = ", ".join(format_item(_) for _ in self._d.items()[half:-half])
            three = ", ".join(format_item(_) for _ in self._d.items()[-half:])
            truncate_string = f"<...{len(self) - MAX_LENGTH} items...>"
            if len(truncate_string) < len(two):
                two = truncate_string
            items = ", ".join([one, two, three])
        else:
            items = ", ".join(format_item(_) for _ in self._d.items())

        return f"{type(self).__name__}(default={self.default!r}, {{{items}}})"

        # return f"{type(self).__name__}({{{items}}})"

    def iterintervals(self, n=2):
        """Iterate over groups of `n` consecutive measurement points in the
        time series.

        """
        # tee the original iterator into n identical iterators
        streams = itertools.tee(iter(self), n)

        # advance the "cursor" on each iterator by an increasing
        # offset, e.g. if n=3:
        #
        #                   [a, b, c, d, e, f, ..., w, x, y, z]
        #  first cursor -->  *
        # second cursor -->     *
        #  third cursor -->        *
        for stream_index, stream in enumerate(streams):
            for _ in range(stream_index):
                next(stream)

        # now, zip the offset streams back together to yield tuples,
        # in the n=3 example it would yield:
        # (a, b, c), (b, c, d), ..., (w, x, y), (x, y, z)
        yield from zip(*streams)

    @staticmethod
    def _value_function(value):
        # todo: should this be able to take NotGiven, so that it would
        # be possible to filter for None explicitly?

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

        """

        # todo: add mask argument here.
        # todo: check whether this can be simplified with newer SortedDict

        start, end, mask = self._check_boundaries(
            start, end, allow_infinite=False
        )

        value_function = self._value_function(value)

        # get start index and value

        start_index = self._d.bisect_right(start)
        if start_index:
            _, start_value = self._d.peekitem(start_index - 1)
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
        if interval_t0 < end and value_function(
            interval_t0, end, interval_value
        ):
            yield interval_t0, end, interval_value

    def slice(self, start, end):
        """Return an equivalent TimeSeries that only has points between
        `start` and `end` (always starting at `start`)

        """
        start, end, mask = self._check_boundaries(
            start, end, allow_infinite=True
        )

        result = TimeSeries(default=self.default)
        for t0, t1, value in self.iterperiods(start, end):  # noqa: B007
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
                sampling_period_timedelta = datetime.timedelta(
                    seconds=sampling_period
                )

            if sampling_period_seconds <= 0:
                msg = "sampling_period must be > 0"
                raise ValueError(msg)

            if sampling_period_seconds > utils.duration_to_number(end - start):
                msg = (
                    "sampling_period "
                    "is greater than the duration between "
                    "start and end."
                )
                raise ValueError(msg)

            sampling_period = (
                sampling_period_timedelta
                if isinstance(start, datetime.date)
                else sampling_period_seconds
            )

        return sampling_period

    def sample(
        self,
        sampling_period,
        start=None,
        end=None,
        interpolate="previous",
        mask=None,
    ):
        """Sampling at regular time periods."""
        start, end, mask = self._check_boundaries(start, end)

        sampling_period = self._check_regularization(
            start, end, sampling_period
        )

        result = []
        for start, end, _ in mask.iterperiods(value=True):
            current_time = start
            while current_time <= end:
                value = self.get(current_time, interpolate=interpolate)
                result.append((current_time, value))
                current_time += sampling_period
        return result

    def sample_interval(  # noqa: C901
        self,
        sampling_period=None,
        start=None,
        end=None,
        idx=None,
        operation="mean",
    ):
        """Sampling on intervals by using some operation (mean,max,min).

        It can be called either with sampling_period, [start], [end]
        or with a idx as a DateTimeIndex.

        The returing pandas.Series will be indexed either on
        pandas.date_range(start,end,freq=sampling_period) or on idx.

        :param sampling_period: the sampling period
        :param start: the start time of the sampling
        :param end: the end time of the sampling
        :param idx: a DateTimeIndex with the start times of the intervals
        :param operation: "mean", "max" or "min"
        :return: a pandas Series with the Trace sampled
        """

        try:
            import pandas as pd
        except ImportError as error:
            msg = "sample_interval need pandas to be installed"
            raise ImportError(msg) from error

        if idx is None:
            start, end, mask = self._check_boundaries(start, end)
            sampling_period = self._check_regularization(
                start, end, sampling_period
            )
            # create index on [start, end)
            idx = pd.date_range(
                start, end, freq=sampling_period, inclusive="both"
            )
        else:
            start, end, mask = self._check_boundaries(idx[0], idx[-1])

        idx_list = idx.values  # list(idx)

        # create all inflexion points
        def items_in_horizon():
            # yields all items between start and end as well as start and end
            yield (start, self[start])
            for t, v in self.items():
                if t <= start:
                    continue
                if t >= end:
                    break
                yield t, v
            yield (end, self[end])

        inflexion_times, inflexion_values = zip(*items_in_horizon())
        inflexion_times = pd.DatetimeIndex(inflexion_times)

        # identify all inflexion intervals
        inflexion_intervals = idx.get_indexer(inflexion_times, method="ffill")

        # convert DatetimeIndex to numpy array for faster indexation
        inflexion_times = inflexion_times.values

        Np1 = len(idx_list) - 1

        # convert to timestamp
        # (to make interval arithmetic faster, no need for total_seconds)
        inflexion_times = inflexion_times.astype("int64")
        idx_times = idx.astype("int64")

        # initialise init, update and finish functions depending
        # on the aggregation operator
        init, update, finish = {
            "mean": (
                lambda t, v: 0.0,
                lambda agg, t0, t1, v: agg + (t1 - t0) * v,
                lambda agg, t_start, t_end: agg / (t_end - t_start),
            ),
            "max": (
                lambda t, v: v,
                lambda agg, t0, t1, v: max(agg, v),
                lambda agg, t_start, t_end: agg,
            ),
            "min": (
                lambda t, v: v,
                lambda agg, t0, t1, v: min(agg, v),
                lambda agg, t_start, t_end: agg,
            ),
        }[operation]

        # initialise first interval
        t_start, t_end = idx_times[0:2]
        i0, t0, v0 = 0, t_start, self[start]
        agg = init(t0, v0)

        result = []
        for i1, t1, v1 in zip(
            inflexion_intervals, inflexion_times, inflexion_values
        ):
            if i0 != i1:
                # change of interval

                # finish previous interval
                agg = update(agg, t0, t_end, v0)
                agg = finish(agg, t_start, t_end)
                result.append((idx_list[i0], agg))

                # handle all intervals between t_end and t1
                if i1 != i0 + 1:
                    result.append((idx_list[i0 + 1], v0))

                # if last_point, break
                if i1 == Np1:
                    break

                # set up new interval
                t_start, t_end = idx_times[i1 : i1 + 2]
                i0, t0 = i1, t_start
                agg = init(t0, v0)

            agg = update(agg, t0, t1, v0)

            i0, t0, v0 = i1, t1, v1

        df = pd.DataFrame.from_records(result)
        return df.set_index(0).iloc[:, 0].reindex(idx[:-1]).ffill()

    def moving_average(  # noqa: C901
        self,
        sampling_period,
        window_size=None,
        start=None,
        end=None,
        placement="center",
        pandas=False,
    ):
        """Averaging over regular intervals"""
        start, end, mask = self._check_boundaries(start, end)

        # default to sampling_period if not given
        if window_size is None:
            window_size = sampling_period

        sampling_period = self._check_regularization(
            start, end, sampling_period
        )

        # convert to datetime if the times are datetimes
        full_window = window_size * 1.0
        half_window = full_window / 2
        if isinstance(start, datetime.date) and not isinstance(
            full_window, datetime.timedelta
        ):
            half_window = datetime.timedelta(seconds=half_window)
            full_window = datetime.timedelta(seconds=full_window)

        result = []
        current_time = start
        while current_time <= end:
            if placement == "center":
                window_start = current_time - half_window
                window_end = current_time + half_window
            elif placement == "left":
                window_start = current_time
                window_end = current_time + full_window
            elif placement == "right":
                window_start = current_time - full_window
                window_end = current_time
            else:
                msg = f'unknown placement "{placement}"'
                raise ValueError(msg)

            # calculate mean over window and add (t, v) tuple to list
            try:
                mean = self.mean(window_start, window_end)
            except TypeError as e:
                if "NoneType" in str(e):
                    mean = None
                else:
                    raise
            result.append((current_time, mean))

            current_time += sampling_period

        # convert to pandas Series if pandas=True
        if pandas:
            try:
                import pandas as pd
            except ImportError as error:
                msg = "can't have pandas=True if pandas is not installed"
                raise ImportError(msg) from error

            result = pd.Series(
                [v for t, v in result],
                index=[t for t, v in result],
            )

        return result

    @staticmethod
    def rebin(binned, key_function):
        result = SortedDict()
        for bin_start, value in binned.items():
            new_bin_start = key_function(bin_start)
            try:
                result[new_bin_start] += value
            except KeyError:
                result[new_bin_start] = value

        return result

    def bin(
        self,
        unit,
        n_units=1,
        start=None,
        end=None,
        mask=None,
        smaller=None,
        transform="distribution",
    ):
        if mask is not None and mask.is_empty():
            return SortedDict()

        if start is not None and start == end:
            return SortedDict()

        # use smaller if available
        if smaller:
            return self.rebin(
                smaller,
                lambda x: utils.datetime_floor(x, unit, n_units),
            )

        start, end, mask = self._check_boundaries(start, end, mask=mask)

        start = utils.datetime_floor(start, unit=unit, n_units=n_units)

        function = getattr(self, transform)
        result = SortedDict()
        dt_range = utils.datetime_range(start, end, unit, n_units=n_units)
        for bin_start, bin_end in utils.pairwise(dt_range):
            result[bin_start] = function(
                bin_start, bin_end, mask=mask, normalized=False
            )

        return result

    def mean(self, start=None, end=None, mask=None, interpolate="previous"):
        """This calculated the average value of the time series over the given
        time range from `start` to `end`, when `mask` is truthy.

        """
        return self.distribution(
            start=start, end=end, mask=mask, interpolate=interpolate
        ).mean()

    def distribution(
        self,
        start=None,
        end=None,
        normalized=True,
        mask=None,
        interpolate="previous",
    ):
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

            mask (:obj:`TimeSeries`, optional): A domain on which to
                calculate the distribution.

            interpolate (str, optional): Method for interpolating
                between measurement points: either "previous"
                (default) or "linear". Note: if "previous" is used,
                then the resulting histogram is exact. If "linear" is
                given, then the values used for the histogram are the
                average value for each segment -- the mean of this
                histogram will be exact, but higher moments (variance)
                will be approximate.

        Returns:

            :obj:`Histogram` with the results.

        """

        start, end, mask = self._check_boundaries(start, end, mask=mask)

        counter = histogram.Histogram()
        for i_start, i_end, _ in mask.iterperiods(value=True):
            for t0, t1, _ in self.iterperiods(i_start, i_end):
                duration = utils.duration_to_number(
                    t1 - t0,
                    units="seconds",
                )
                midpoint = utils.time_midpoint(t0, t1)
                value = self.get(midpoint, interpolate=interpolate)
                try:
                    counter[value] += duration
                except histogram.UnorderableElements:
                    counter = histogram.Histogram.from_dict(
                        dict(counter), key=hash
                    )
                    counter[value] += duration

        # divide by total duration if result needs to be normalized
        if normalized:
            return counter.normalized()
        else:
            return counter

    def n_points(
        self,
        start=-infinity.inf,
        end=+infinity.inf,
        mask=None,
        include_start=True,
        include_end=False,
        normalized=False,
    ):
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
        # just go ahead and return 0 if we already know it regardless
        # of boundaries
        if not self.n_measurements():
            return 0

        start, end, mask = self._check_boundaries(start, end, mask=mask)

        count = 0
        for i_start, i_end, _ in mask.iterperiods(value=True):
            end_count = (
                self._d.bisect_right(i_end)
                if include_end
                else self._d.bisect_left(i_end)
            )

            start_count = (
                self._d.bisect_left(i_start)
                if include_start
                else self._d.bisect_right(i_start)
            )

            count += end_count - start_count

        if normalized:
            count /= self.n_measurements()

        return count

    def _check_time_series(self, other):
        """Function used to check the type of the argument and raise an
        informative error message if it's not a TimeSeries.

        """
        if not isinstance(other, TimeSeries):
            msg = f"unsupported operand types(s) for +: {type(self)} and {type(other)}"
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
            value = merged if operation is None else operation(merged)
            result.set(t, value, compact=compact)
        return result

    @classmethod
    def from_csv(
        cls,
        filename,
        time_column=0,
        value_column=1,
        time_transform=None,
        value_transform=None,
        skip_header=True,
        default=None,
    ):
        # todo: allowing skipping n header rows

        # use default on class if not given
        if time_transform is None:
            time_transform = lambda s: datetime.datetime.strptime(
                s, "%Y-%m-%d %H:%M:%S"
            )
        if value_transform is None:
            value_transform = lambda s: s

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

    def operation(self, other, function, default=None):
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

        # todo: consider the best way to deal with default, and make
        # consistent with other methods. check to_bool maybe

        result = TimeSeries(default=default)
        if isinstance(other, TimeSeries):
            for time, value in self:
                result[time] = function(value, other[time])
            for time, value in other:
                result[time] = function(self[time], value)
        else:
            for time, value in self:
                result[time] = function(value, other)
        return result

    def to_bool(self, invert=False, default=NotGiven):
        """Return the truth value of each element.


        Args:

            invert: opposite truth values

            default: If default is not explicitly given, keep it as
             None if it's None (which often means "undefined" rather
             than "false"), otherwise cast to bool

        Returns:

            :obj:`TimeSeries` with the results.

        """
        if default is NotGiven:
            if self.default is None:
                new_default = None
            else:
                new_default = bool(self.default)
                if invert:
                    new_default = not (new_default)
        else:
            # should this complain if default not in {None, True, False}?
            new_default = default

        if invert:

            def function(x, y):
                return not bool(x)
        else:

            def function(x, y):
                return bool(x)

        return self.operation(None, function, default=new_default)

    def threshold(self, value, inclusive=False):
        """Return True if > than treshold value (or >= threshold value if
        inclusive=True).

        """

        # todo: this seems like it's wrong... make a test to check (and fix if so!)
        # todo: deal with default

        if inclusive:

            def function(x, y):
                return x >= y

        else:

            def function(x, y):
                return x > y

        return self.operation(value, function)

    def sum(self, other):
        """sum(x, y) = x(t) + y(t)."""

        # todo: better consistency and documentation about when Nones are ignored

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
        return self.operation(other, lambda x, y: x and y)

    def logical_or(self, other):
        """logical_or(t) = self(t) or other(t)."""
        return self.operation(other, lambda x, y: x or y)

    def logical_xor(self, other):
        """logical_xor(t) = self(t) ^ other(t)."""
        return self.operation(other, lambda x, y: bool(x) ^ bool(y))

    def __setitem__(self, time, value):
        """Allow a[time] = value syntax or a a[start:end]=value."""
        if isinstance(time, slice):
            return self.set_interval(time.start, time.stop, value)
        else:
            return self.set(time, value)

    def __getitem__(self, time):
        """Allow a[time] syntax."""
        if isinstance(time, slice):
            msg = "Syntax a[start:end] not allowed"
            raise ValueError(msg)  # noqa: TRY004
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
        if other != 0:
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

    def __invert__(self):
        """Allow ~a syntax"""
        return self.to_bool(invert=True)

    def __eq__(self, other):
        return self.items() == other.items()

    def __ne__(self, other):
        return not (self == other)

    def _check_boundary(self, value, allow_infinite, lower_or_upper):
        if lower_or_upper == "lower":
            infinity_value = -infinity.inf
            method_name = "first_key"
        elif lower_or_upper == "upper":
            infinity_value = infinity.inf
            method_name = "last_key"
        else:
            msg = (
                f'`lower_or_upper` must be "lower" or "upper", '
                f"got {lower_or_upper}"
            )
            raise ValueError(msg)

        if value is None:
            if allow_infinite:
                return infinity_value
            else:
                try:
                    return getattr(self, method_name)()
                except IndexError as error:
                    msg = (
                        f"can't use '{method_name}' for default "
                        f"{lower_or_upper} boundary of empty TimeSeries"
                    )
                    raise KeyError(msg) from error
        else:
            return value

    def _check_boundaries(self, start, end, mask=None, allow_infinite=False):
        if mask is not None and mask.is_empty():
            msg = "mask can not be empty"
            raise ValueError(msg)

        # if only a mask is passed in, return mask boundaries and mask
        if start is None and end is None and mask is not None:
            return mask.first_key(), mask.last_key(), mask

        # replace with defaults if not given
        start = self._check_boundary(start, allow_infinite, "lower")
        end = self._check_boundary(end, allow_infinite, "upper")

        if start >= end:
            msg = f"start can't be >= end ({start} >= {end})"
            raise ValueError(msg)

        start_end_mask = TimeSeries(default=False)
        start_end_mask[start] = True
        start_end_mask[end] = False

        mask = start_end_mask if mask is None else mask & start_end_mask

        return start, end, mask

    def distribution_by_hour_of_day(
        self, first=0, last=23, start=None, end=None
    ):
        start, end, mask = self._check_boundaries(start, end)

        result = []
        for hour in range(first, last + 1):
            mask = hour_of_day(start, end, hour)
            result.append((hour, self.distribution(mask=mask)))

        return result

    def distribution_by_day_of_week(
        self, first=0, last=6, start=None, end=None
    ):
        start, end, mask = self._check_boundaries(start, end)

        result = []
        for week in range(first, last + 1):
            mask = day_of_week(start, end, week)
            result.append((week, self.distribution(mask=mask)))

        return result

    def plot(
        self,
        interpolate="previous",
        figure_width=12,
        linewidth=1,
        marker="o",
        markersize=3,
        color="#222222",
    ):
        return plot.plot(
            self,
            interpolate=interpolate,
            figure_width=figure_width,
            linewidth=linewidth,
            marker=marker,
            markersize=markersize,
            color=color,
        )


def hour_of_day(start, end, hour):
    # start should be date, or if datetime, will use date of datetime
    floored = utils.datetime_floor(start)

    domain = TimeSeries(default=False)
    for day_start in utils.datetime_range(
        floored, end, "days", inclusive_end=True
    ):
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
    for day in utils.datetime_range(floored, next_week, "days"):
        if day.weekday() == number:
            first_day = day
            break

    domain = TimeSeries(default=False)
    for week_start in utils.datetime_range(
        first_day, end, "weeks", inclusive_end=True
    ):
        interval_start = week_start
        interval_end = interval_start + datetime.timedelta(days=1)
        domain[interval_start] = True
        domain[interval_end] = False

    result = domain.slice(start, end)
    result[end] = False
    return result
