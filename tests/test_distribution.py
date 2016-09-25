import datetime

import nose

from traces import TimeSeries, Domain


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
    total = (end - start).total_seconds()
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
    a.set(datetime.datetime(2015, 3, 2), 0)
    a.set(datetime.datetime(2015, 3, 3), 1)
    a.set(datetime.datetime(2015, 3, 4), 0)
    end = datetime.datetime(2015, 3, 5)

    mask = Domain(datetime.datetime(2015, 3, 1), datetime.datetime(2015, 3, 3))

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
