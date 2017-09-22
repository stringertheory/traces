import datetime
import random
import sys
import pprint

from infinity import inf
import nose

from traces import TimeSeries


def test_iterintervals():

    ts = TimeSeries()
    ts.set(datetime.datetime(2015, 3, 1), 1)
    ts.set(datetime.datetime(2015, 3, 2), 0)
    ts.set(datetime.datetime(2015, 3, 3), 1)
    ts.set(datetime.datetime(2015, 3, 4), 2)

    answer = [(1, 0), (0, 1), (1, 2)]
    result = []
    for (t0, v0), (t1, v1) in ts.iterintervals():
        result.append((v0, v1))
    assert answer == result


def test_iterperiods():

    # timeseries with no points raises a KeyError
    ts = TimeSeries()
    with nose.tools.assert_raises(KeyError):
        next(ts.iterperiods())

    ts.set(datetime.datetime(2015, 3, 1), 1)
    ts.set(datetime.datetime(2015, 3, 2), 0)
    ts.set(datetime.datetime(2015, 3, 3), 1)
    ts.set(datetime.datetime(2015, 3, 4), 2)

    answer = [
        (datetime.datetime(2015, 3, 1), datetime.datetime(2015, 3, 2), 1),
        (datetime.datetime(2015, 3, 2), datetime.datetime(2015, 3, 3), 0),
        (datetime.datetime(2015, 3, 3), datetime.datetime(2015, 3, 4), 1)]
    result = []
    for (t0, t1, v0) in ts.iterperiods(
            start=datetime.datetime(2015, 3, 1),
            end=datetime.datetime(2015, 3, 4)
    ):
        result.append((t0, t1, v0))
    assert answer == result

    answer = [
        (datetime.datetime(2015, 3, 1), datetime.datetime(2015, 3, 2), 1),
        (datetime.datetime(2015, 3, 3), datetime.datetime(2015, 3, 4), 1),
    ]
    result = []
    for (t0, t1, v0) in ts.iterperiods(
            start=datetime.datetime(2015, 3, 1),
            end=datetime.datetime(2015, 3, 4),
            value=1,
    ):
        result.append((t0, t1, v0))
    assert answer == result

    def filter(t0, t1, value):
        return True if not value else False

    answer = [
        (datetime.datetime(2015, 3, 2), datetime.datetime(2015, 3, 3), 0),
    ]
    result = []
    for (t0, t1, v0) in ts.iterperiods(
            start=datetime.datetime(2015, 3, 1),
            end=datetime.datetime(2015, 3, 4),
            value=filter,
    ):
        result.append((t0, t1, v0))
    assert answer == result


def test_slice():

    ts = TimeSeries(default=1)
    ts[0] = 1
    ts[1] = 5
    ts[4] = 0
    ts[6] = 2

    assert ts.slice(0.5, 2.5).items() == [(0.5, 1), (1, 5), (2.5, 5)]
    assert ts.slice(1.0, 2.5).items() == [(1.0, 5), (2.5, 5)]
    assert ts.slice(-1, 1).items() == [(-1, 1), (0, 1), (1, 5)]
    assert ts.slice(-1, 0.5).items() == [(-1, 1), (0, 1), (0.5, 1)]

    nose.tools.assert_raises(ValueError, ts.slice, 2.5, 0)


def make_random_timeseries():
    length = random.randint(1, 10)
    result = TimeSeries()
    t = 0
    for i in range(length):
        t += random.randint(0, 5)
        x = random.randint(0, 5)
        result[t] = x
    return result


def test_merge():

    # since this is random, do it a bunch of times
    for n_trial in range(1000):

        # make a list of TimeSeries that is anywhere from 0 to 5
        # long. Each TimeSeries is of random length between 0 and 20,
        # with random time points and random values.
        ts_list = []
        for i in range(random.randint(1, 5)):
            ts_list.append(make_random_timeseries())

        method_a = list(TimeSeries.merge(ts_list, compact=False))
        method_b = list(TimeSeries.iter_merge(ts_list))

        msg = '%s != %s' % (pprint.pformat(method_a), pprint.pformat(method_b))
        assert method_a == method_b, msg


def test_single_merges():

    # a single empty time series
    ts = TimeSeries()
    assert TimeSeries.merge([ts]) == TimeSeries(default=[None])

    # multiple empty time series
    ts_a = TimeSeries()
    ts_b = TimeSeries()
    assert TimeSeries.merge([ts_a, ts_b]) == \
        TimeSeries(default=[None, None])

    # test a single time series with only one measurement
    ts = TimeSeries()
    ts[21] = 42

    merged = TimeSeries.merge([ts])

    assert merged.items() == [(21, [42])]

    # test an empty time series and a time series with one measurement
    ts_a = TimeSeries()
    ts_a[21] = 42
    ts_b = TimeSeries()

    ts = TimeSeries.merge([ts_a, ts_b])
    assert ts[20] == [None, None]
    assert ts[23] == [42, None]

    # test an empty time series and a time series with one entry
    ts_a = TimeSeries()
    ts_a[21] = 42
    ts_a[22] = 41
    ts_a[23] = 40

    ts_b = TimeSeries()
    ts_b[20] = 1
    ts_b[22] = 2
    ts_b[24] = 3

    merged = TimeSeries.merge([ts_a, ts_b])

    assert merged.items() == [
        (20, [None, 1]),
        (21, [42, 1]),
        (22, [41, 2]),
        (23, [40, 2]),
        (24, [40, 3]),
    ]
