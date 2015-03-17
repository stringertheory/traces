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

# 3rd party
import sortedcontainers
import arrow


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

    def __init__(self):
        self.d = sortedcontainers.SortedDict()

    def __iter__(self):
        """Iterate over sorted (time, value) pairs."""
        return self.d.iteritems()

    def get(self, time, default=0):
        """This is probably the most important method. It allows the user to
        get the value of the time series inbetween measured values.

        THERE SHOULD BE THE OPTION TO INTERPOLATE!

        """
        index = self.d.bisect_right(time)
        if index:
            closest_time = self.d.iloc[index - 1]
            return self.d[closest_time]
        else:
            return default

    def set(self, time, value):
        """Set a value for the time series."""
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
            value_function = lambda x: True
        elif callable(value):
            value_function = value
        else:
            value_function = lambda x: x[0][1] == value

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

    def regularize(self):
        """Should there be a different function for sampling at regular time
        periods versus averaging over regular intervals?

        """
        pass

    def mean(self, start_time, end_time):
        """This calculated the average value of the time series over the given
        time range from `start_time` to `end_time`.

        """
        total_seconds = (end_time - start_time).total_seconds()

        # get start index and value
        start_index = self.d.bisect_right(start_time)
        if start_index:
            start_value = self.d[self.d.iloc[start_index - 1]]
        else:
            raise ValueError('%s before start of time series' % start_time)

        # get end index
        end_index = self.d.bisect_right(end_time)

        # start weighted average at zero
        mean = 0

        # look over each interval of time series within the
        # region. Use the region start time and value to begin
        int_t0, int_value = start_time, start_value
        for index in range(start_index, end_index):

            # look up end time of interval
            int_t1 = self.d.iloc[index]

            # calculate contribution to weighted average for this
            # interval
            weight = (int_t1 - int_t0).total_seconds() / total_seconds
            mean += (weight * int_value)

            # set start point to the end of this interval for next
            # iteration
            int_t0 = int_t1
            int_value = self.d[int_t0]

        # use the region end time as the end of the final interval
        int_t1 = end_time

        # calculate contribution to weighted average
        weight = (int_t1 - int_t0).total_seconds() / total_seconds
        mean += (weight * int_value)

        return mean

    def _check_type(self, other):
        """Function used to check the type of the argument and raise an
        informative error message if it's not a TimeSeries.

        """
        if not isinstance(other, TimeSeries):
            msg = "unsupported operand types(s) for +: %s and %s" % \
                (type(self), type(other))
            raise TypeError(msg)

    def operation(self, other, function):
        """Calculate operation between two TimeSeries:

        operation(t) = function(self(t), other(t))

        """
        self._check_type(other)
        result = TimeSeries()
        for time, value in self:
            result[time] = function(value, other[time])
        for time, value in other:
            result[time] = function(self[time], value)
        return result

    def sum(self, other):
        """sum(x, y) = x(t) + y(t)."""
        return self.operation(other, lambda x, y: x + y)

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
            self._check_type(other)

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


def example_sum():

    a = TimeSeries()
    a.set(datetime.datetime(2015, 3, 1), 1)
    a.set(datetime.datetime(2015, 3, 2), 0)
    a.set(datetime.datetime(2015, 3, 3), 1)
    a.set(datetime.datetime(2015, 3, 5), 0)
    a.set(datetime.datetime(2015, 3, 6), 0)

    b = TimeSeries()
    b.set(datetime.datetime(2015, 3, 1), 0)
    b.set(datetime.datetime(2015, 3, 2, 12), 1)
    b.set(datetime.datetime(2015, 3, 3, 13, 13), 0)
    b.set(datetime.datetime(2015, 3, 4), 1)
    b.set(datetime.datetime(2015, 3, 5), 0)
    b.set(datetime.datetime(2015, 3, 5, 12), 1)
    b.set(datetime.datetime(2015, 3, 5, 19), 0)

    c = TimeSeries()
    c.set(datetime.datetime(2015, 3, 1, 17), 0)
    c.set(datetime.datetime(2015, 3, 1, 21), 1)
    c.set(datetime.datetime(2015, 3, 2, 13, 13), 0)
    c.set(datetime.datetime(2015, 3, 4, 18), 1)
    c.set(datetime.datetime(2015, 3, 5, 4), 0)

    # output the three time series
    for i, ts in enumerate([a, b, c]):

        for (t0, v0), (t1, v1) in ts.iterintervals(1):
            print t0.isoformat(), i
            print t1.isoformat(), i

        print ''

        for (t0, v0), (t1, v1) in ts.iterintervals(0):
            print t0.isoformat(), i
            print t1.isoformat(), i

        print ''

    # output the sum

    for dt, i in sum([a, b, c]):
        print dt.isoformat(), i


def example_dictlike():

    # test overwriting keys
    l = TimeSeries()
    l[datetime.datetime(2010, 1, 1)] = 5
    l[datetime.datetime(2010, 1, 2)] = 4
    l[datetime.datetime(2010, 1, 3)] = 3
    l[datetime.datetime(2010, 1, 7)] = 2
    l[datetime.datetime(2010, 1, 4)] = 1
    l[datetime.datetime(2010, 1, 4)] = 10
    l[datetime.datetime(2010, 1, 4)] = 5
    l[datetime.datetime(2010, 1, 1)] = 1
    l[datetime.datetime(2010, 1, 7)] = 1.2
    l[datetime.datetime(2010, 1, 8)] = 1.3
    l[datetime.datetime(2010, 1, 12)] = 1.3

    # do some wackiness with a bunch of points
    dt = datetime.datetime(2010, 1, 12)
    for i in range(1000):
        dt += datetime.timedelta(hours=random.random())
        l[dt] = math.sin(i / float(math.pi))

    dt -= datetime.timedelta(hours=500)
    dt -= datetime.timedelta(minutes=30)
    for i in range(1000):
        dt += datetime.timedelta(hours=random.random())
        l[dt] = math.cos(i / float(math.pi))

    # what does this get?
    print >> sys.stderr, l[datetime.datetime(2010, 1, 3, 23, 59, 59)]

    # output the time series
    for i, j in l:
        print i.isoformat(), j


def example_mean():

    l = TimeSeries()
    l[datetime.datetime(2010, 1, 1)] = 0
    l[datetime.datetime(2010, 1, 3, 10)] = 1
    l[datetime.datetime(2010, 1, 5)] = 0
    l[datetime.datetime(2010, 1, 8)] = 1
    l[datetime.datetime(2010, 1, 17)] = 0
    l[datetime.datetime(2010, 1, 19)] = 1
    l[datetime.datetime(2010, 1, 23)] = 0
    l[datetime.datetime(2010, 1, 26)] = 1
    l[datetime.datetime(2010, 1, 28)] = 0
    l[datetime.datetime(2010, 1, 31)] = 1
    l[datetime.datetime(2010, 2, 5)] = 0

    for time, value in l:
        print time.isoformat(), 0.1 * value + 1.1

    print ''

    timestep = {'hours': 25}
    start_time = datetime.datetime(2010, 1, 1)
    while start_time <= datetime.datetime(2010, 2, 5):
        end_time = start_time + datetime.timedelta(**timestep)
        print start_time.isoformat(), l.mean(start_time, end_time)
        start_time = end_time

    print ''

    start_time = datetime.datetime(2010, 1, 1)
    while start_time <= datetime.datetime(2010, 2, 5):
        end_time = start_time + datetime.timedelta(**timestep)
        print start_time.isoformat(), -0.2
        print start_time.isoformat(), 1.2
        start_time = end_time


def example_arrow():

    l = TimeSeries()
    l[arrow.Arrow(2010, 1, 1)] = 0
    l[arrow.Arrow(2010, 1, 3, 10)] = 1
    l[arrow.Arrow(2010, 1, 5)] = 0
    l[arrow.Arrow(2010, 1, 8)] = 1
    l[arrow.Arrow(2010, 1, 17)] = 0
    l[arrow.Arrow(2010, 1, 19)] = 1
    l[arrow.Arrow(2010, 1, 23)] = 0
    l[arrow.Arrow(2010, 1, 26)] = 1
    l[arrow.Arrow(2010, 1, 28)] = 0
    l[arrow.Arrow(2010, 1, 31)] = 1
    l[arrow.Arrow(2010, 2, 5)] = 0

    for time, value in l:
        print time.naive.isoformat(), 0.1 * value + 1.1

    print ''

    start = arrow.Arrow(2010, 1, 1)
    end = arrow.Arrow(2010, 2, 5)
    unit = {'hours': 25}
    for start_time, end_time in span_range(start, end, unit):
        print start_time.naive.isoformat(), l.mean(start_time, end_time)

    print ''

    for start_time, end_time in span_range(start, end, unit):
        print start_time.naive.isoformat(), -0.2
        print start_time.naive.isoformat(), 1.2


if __name__ == '__main__':

    # example_arrow()
    # example_mean()
    example_sum()
    # example_dictlike()
