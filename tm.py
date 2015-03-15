import sys
import datetime
import pprint
import math
import random
import itertools

import sortedcontainers


class TimeSeries(object):

    def __init__(self):
        self.d = sortedcontainers.SortedDict()

    def __iter__(self):
        return self.d.iteritems()

    def set(self, time, value):
        self.d[time] = value

    def __setitem__(self, time, value):
        return self.set(time, value)

    def get(self, time):
        index = self.d.bisect_right(time)
        if index:
            closest_time = self.d.iloc[index - 1]
            return self.d[closest_time]
        else:
            return 0
            raise ValueError('No item found with time at or below: %r' % time)

    def __getitem__(self, time):
        return self.get(time)

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
            
    def iterminutes(self, state=None):
        """Iterate over all minutes where the time series is on."""
        for (t0, v0), (t1, v1) in self.iterintervals(state):
            for minute in minute_range(t0, t1):
                yield minute, v0

    def mean(self, start_time, end_time):
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


    def operation(self, other, function):
        """Calculate operation between two TimeSeries:

        operation(t) = function(self(t), other(t))

        """
        result = TimeSeries()
        for time, value in self:
            result[time] = function(value, other[time])
        for time, value in other:
            result[time] = function(self[time], value)
        return result

    def sum(self, other):
        """sum(t) = self(t) + other(t)."""
        return self.operation(other, lambda x, y: x + y)

    def multiply(self, other):
        """sum(t) = self(t) * other(t)."""
        return self.operation(other, lambda x, y: x * y)

    def difference(self, other):
        """sum(t) = self(t) - other(t)."""
        return self.operation(other, lambda x, y: x - y)

    def logical_and(self, other):
        """logical_and(t) = self(t) and other(t)."""
        return self.operation(other, lambda x, y: x and y)

    def logical_or(self, other):
        """logical_or(t) = self(t) or other(t)."""
        return self.operation(other, lambda x, y: x or y)

    def logical_xor(self, other):
        """logical_xor(t) = self(t) ^ other(t)."""
        return self.operation(other, lambda x, y: bool(x) ^ bool(y))


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
    for dt, i in a.sum(b).sum(c):
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
        l[dt] = math.sin(i/float(math.pi))

    dt -= datetime.timedelta(hours=500)
    dt -= datetime.timedelta(minutes=30)
    for i in range(1000):
        dt += datetime.timedelta(hours=random.random())
        l[dt] = math.cos(i/float(math.pi))

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
        

if __name__ == '__main__':

    example_mean()
    # example_sum()
    # example_dictlike()
    
