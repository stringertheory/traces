import datetime
import nose
from traces import TimeSeries, Histogram


def test_distribution():

    start = datetime.datetime(2015, 3, 1)

    # v. simple
    a = TimeSeries()
    a.set(start, 1)
    a.set(datetime.datetime(2015, 3, 2), 0)
    a.set(datetime.datetime(2015, 3, 3), 1)
    a.set(datetime.datetime(2015, 3, 4), 0)
    end = datetime.datetime(2015, 3, 5)

    # not normalized
    distribution = a.distribution(
        start=start, end=end, normalized=False,
    )
    assert distribution[0] == 24 * 60 * 60 * 2  # two days
    assert distribution[1] == 24 * 60 * 60 * 2

    # normalized
    distribution = a.distribution(start=start, end=end)
    assert distribution[0] == 0.5
    assert distribution[1] == 0.5


def test_default_values():

    # v. simple
    a = TimeSeries()
    a.set(datetime.datetime(2015, 3, 1), 1)
    a.set(datetime.datetime(2015, 3, 2), 0)
    a.set(datetime.datetime(2015, 3, 3), 1)
    a.set(datetime.datetime(2015, 3, 4), 0)

    start = datetime.datetime(2015, 3, 1)
    end = datetime.datetime(2015, 3, 4)
    default = a.distribution()
    distribution = a.distribution(start=start, end=end)
    assert default == distribution
    assert distribution[0] == 1.0 / 3
    assert distribution[1] == 2.0 / 3


def test_mask():

    start = datetime.datetime(2015, 3, 1)

    # v. simple
    a = TimeSeries()
    a.set(start, 1)
    a.set(datetime.datetime(2015, 4, 2), 0)
    a.set(datetime.datetime(2015, 4, 3), 1)
    a.set(datetime.datetime(2015, 4, 4), 0)
    end = datetime.datetime(2015, 4, 5)

    mask = TimeSeries(default=False)
    mask[datetime.datetime(2015, 4, 1)] = True
    mask[datetime.datetime(2015, 4, 3)] = False

    # not normalized
    distribution = a.distribution(
        start=start, end=end, normalized=False, mask=mask,
    )
    assert distribution[0] == 24 * 60 * 60  # one day
    assert distribution[1] == 24 * 60 * 60

    # normalized
    distribution = a.distribution(
        start=start, end=end, mask=mask,
    )
    assert distribution[0] == 0.5
    assert distribution[1] == 0.5


def test_integer_times():

    # v. simple
    a = TimeSeries()
    a[0] = 1
    a[1] = 0
    a[3] = 1
    a[4] = 0

    distribution = a.distribution(start=0, end=6)

    assert distribution[0] == 2.0 / 3
    assert distribution[1] == 1.0 / 3


def test_distribution_set():
    time_series = TimeSeries()
    time_series[1.2] = {'broccoli'}
    time_series[1.4] = {'broccoli', 'orange'}
    time_series[1.7] = {'broccoli', 'orange', 'banana'}
    time_series[2.2] = {'orange', 'banana'}
    time_series[3.5] = {'orange', 'banana', 'beets'}

    # TODO: How to convert the set into multiple ts?


def test_distribution_empty():

    ts = TimeSeries()

    mask = TimeSeries(default=0)
    mask[0] = 1
    mask[2] = 0

    # distribution with default args and no default value on empty
    # TimeSeries doesn't know what to do
    nose.tools.assert_raises(KeyError, ts.distribution)

    # distribution with start and end, but no default value on empty
    # TimeSeries doesn't know what to do
    assert ts.distribution(0, 10) == Histogram.from_dict({None: 1.0})

    # no matter what is passed in to distribution, if the default
    # value is not set on an empty TimeSeries this should be an error
    ts.distribution(mask=mask) == Histogram.from_dict({None: 1.0})
    # nose.tools.assert_raises(KeyError, ts.distribution, mask=mask)

    ts = TimeSeries(default=0)

    # no mask or start/end on empty TimeSeries, don't know what to do
    nose.tools.assert_raises(KeyError, ts.distribution)

    # start and end or mask given, is fine
    distribution = ts.distribution(0, 10)
    assert distribution[0] == 1.0

    distribution = ts.distribution(mask=mask)
    assert distribution[0] == 1.0

    # empty mask
    mask = TimeSeries(default=0)

    with nose.tools.assert_raises(ValueError):
        ts.distribution(mask=mask)

    with nose.tools.assert_raises(ValueError):
        ts.distribution(start=0, end=2, mask=mask)


def test_none_handling():
    ts = TimeSeries()
    ts[1] = (0, 1)
    ts[2] = (None, 0)
    ts[3] = (2, 0)

    # print(ts.distribution(normalized=False))
    assert(ts.distribution()[(0, 1)] == 0.5)
    assert(ts.distribution()[(None, 0)] == 0.5)
