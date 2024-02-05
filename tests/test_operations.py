import datetime

import pytest

from traces import TimeSeries
from traces.decorators import ignorant


def test_scalar_ops():
    a = TimeSeries()
    a.set(datetime.datetime(2015, 3, 1), 1)
    a.set(datetime.datetime(2015, 3, 2), 0)
    a.set(datetime.datetime(2015, 3, 3), 3)
    a.set(datetime.datetime(2015, 3, 4), 2)

    ts_half = a.multiply(0.5)
    ts_bool = a.to_bool(invert=False)
    ts_threshold = a.threshold(value=1.1)

    # test before domain, should give default value
    assert ts_half[datetime.datetime(2015, 2, 24)] is None
    assert ts_bool[datetime.datetime(2015, 2, 24)] is None
    assert ts_threshold[datetime.datetime(2015, 2, 24)] is None

    # test values throughout series
    assert ts_half[datetime.datetime(2015, 3, 1, 6)] == 0.5
    assert ts_bool[datetime.datetime(2015, 3, 1, 6)] is True
    assert ts_threshold[datetime.datetime(2015, 3, 1, 6)] is False

    assert ts_half[datetime.datetime(2015, 3, 2, 6)] == 0
    assert ts_bool[datetime.datetime(2015, 3, 2, 6)] is False
    assert ts_threshold[datetime.datetime(2015, 3, 2, 6)] is False

    assert ts_half[datetime.datetime(2015, 3, 3, 6)] == 1.5
    assert ts_bool[datetime.datetime(2015, 3, 3, 6)] is True
    assert ts_threshold[datetime.datetime(2015, 3, 3, 6)] is True

    # test after domain, should give last value
    assert ts_half[datetime.datetime(2015, 3, 4, 18)] == 1
    assert ts_bool[datetime.datetime(2015, 3, 4, 18)] is True
    assert ts_threshold[datetime.datetime(2015, 3, 4, 18)] is True


def test_sum():
    a = TimeSeries()
    a.set(datetime.datetime(2015, 3, 1), 1)
    a.set(datetime.datetime(2015, 3, 2), 0)
    a.set(datetime.datetime(2015, 3, 3), 1)
    a.set(datetime.datetime(2015, 3, 4), 0)

    b = TimeSeries()
    b.set(datetime.datetime(2015, 3, 1), 0)
    b.set(datetime.datetime(2015, 3, 1, 12), 1)
    b.set(datetime.datetime(2015, 3, 2), 0)
    b.set(datetime.datetime(2015, 3, 2, 12), 1)
    b.set(datetime.datetime(2015, 3, 3), 0)

    c = TimeSeries()
    c.set(datetime.datetime(2015, 3, 1), 0)
    c.set(datetime.datetime(2015, 3, 1, 18), 1)
    c.set(datetime.datetime(2015, 3, 5), 0)

    ts_sum = TimeSeries.merge([a, b, c], operation=ignorant(sum))

    # test before domain, should give default value
    assert ts_sum[datetime.datetime(2015, 2, 24)] == 0

    # test values throughout sum
    assert ts_sum[datetime.datetime(2015, 3, 1)] == 1
    assert ts_sum[datetime.datetime(2015, 3, 1, 6)] == 1
    assert ts_sum[datetime.datetime(2015, 3, 1, 12)] == 2
    assert ts_sum[datetime.datetime(2015, 3, 1, 13)] == 2
    assert ts_sum[datetime.datetime(2015, 3, 1, 17)] == 2
    assert ts_sum[datetime.datetime(2015, 3, 1, 18)] == 3
    assert ts_sum[datetime.datetime(2015, 3, 1, 19)] == 3
    assert ts_sum[datetime.datetime(2015, 3, 3)] == 2
    assert ts_sum[datetime.datetime(2015, 3, 4)] == 1
    assert ts_sum[datetime.datetime(2015, 3, 4, 18)] == 1
    assert ts_sum[datetime.datetime(2015, 3, 5)] == 0

    # test after domain, should give last value
    assert ts_sum[datetime.datetime(2015, 3, 6)] == 0

    assert 0 + a + b == a + b


def test_interpolation():
    ts = TimeSeries(data=[(0, 0), (1, 2)])

    assert ts.get(0, interpolate="linear") == 0
    assert ts.get(0.25, interpolate="linear") == 0.5
    assert ts.get(0.5, interpolate="linear") == 1.0
    assert ts.get(0.75, interpolate="linear") == 1.5
    assert ts.get(1, interpolate="linear") == 2

    assert ts.get(-1, interpolate="linear") is None
    assert ts.get(2, interpolate="linear") == 2

    pytest.raises(ValueError, ts.get, 0.5, "spline")


def test_default():
    ts = TimeSeries(data=[(0, 0), (1, 2)])
    ts_no_default = ts.operation(ts, lambda a, b: a + b)
    assert ts_no_default.default is None

    ts_default = ts.operation(ts, lambda a, b: a + b, default=1)
    assert ts_default.default == 1

    ts_none = ts.operation(ts, lambda a, b: a + b, default=None)
    assert ts_none.default is None


def test_difference():
    a = TimeSeries(data=[(0, 0), (2, 2)], default=0)
    b = TimeSeries(data=[(1, 1), (3, 2)], default=0)

    c = a - b
    assert list(c.items()) == [(0, 0), (1, -1), (2, 1), (3, 0)]


def test_to_bool_default():
    data = [(0, 0), (2, 5), (3, 0), (4, 7), (10, 3)]

    assert TimeSeries(data=data, default=None).to_bool().default is None
    assert TimeSeries(data=data, default=None).to_bool()[-1] is None
    assert TimeSeries(data=data, default=0).to_bool().default == 0
    assert TimeSeries(data=data, default=0).to_bool()[-1] == 0
    assert TimeSeries(data=data, default=5).to_bool().default == 1
    assert TimeSeries(data=data, default=5).to_bool()[-1] == 1

    assert (
        TimeSeries(data=data, default=None).to_bool(default=None).default
        is None
    )
    assert (
        TimeSeries(data=data, default=0).to_bool(default=None).default is None
    )
    assert (
        TimeSeries(data=data, default=5).to_bool(default=None).default is None
    )

    assert (
        TimeSeries(data=data, default=None).to_bool(default=False).default
        is False
    )
    assert (
        TimeSeries(data=data, default=0).to_bool(default=False).default is False
    )
    assert (
        TimeSeries(data=data, default=5).to_bool(default=False).default is False
    )

    assert (
        TimeSeries(data=data, default=None).to_bool(default=True).default
        is True
    )
    assert (
        TimeSeries(data=data, default=0).to_bool(default=True).default is True
    )
    assert (
        TimeSeries(data=data, default=5).to_bool(default=True).default is True
    )

    assert TimeSeries(data=data, default=None).to_bool(default=10).default == 10
    assert TimeSeries(data=data, default=0).to_bool(default=10).default == 10
    assert TimeSeries(data=data, default=5).to_bool(default=10).default == 10


def test_truthiness():
    data = [(0, 0), (2, 5), (3, 0), (4, 7), (10, 3)]
    assert bool(TimeSeries()) is False
    assert bool(TimeSeries(data=data)) is True

    if TimeSeries():
        assert "should not be here"


def test_logical_operations():
    ts1 = TimeSeries([(0, 0), (2, 5), (3, 0), (4, 7), (10, 3)])
    ts2 = TimeSeries([(0, 0), (1, 1), (2, 3), (4, 0), (5, 5), (10, 1), (11, 0)])

    a_or = [(0, 0), (1, 1), (2, 5), (3, 3), (4, 7), (5, 7), (10, 3), (11, 3)]
    assert list(ts1.logical_or(ts2).items()) == a_or
    assert list((ts1 | ts2).items()) == a_or

    a_and = [(0, 0), (1, 0), (2, 3), (3, 0), (4, 0), (5, 5), (10, 1), (11, 0)]
    assert list(ts1.logical_and(ts2).items()) == a_and
    assert list((ts1 & ts2).items()) == a_and

    a_xor = [(0, 0), (1, 1), (2, 0), (3, 1), (4, 1), (5, 0), (10, 0), (11, 1)]
    assert list(ts1.logical_xor(ts2).items()) == a_xor
    assert list((ts1 ^ ts2).items()) == a_xor

    a_not = [(0, True), (2, False), (3, True), (4, False), (10, False)]
    assert list(ts1.to_bool(invert=True).items()) == a_not
    assert list((~ts1).items()) == a_not
