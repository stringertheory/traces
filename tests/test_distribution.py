import datetime

import nose

from traces import TimeSeries, Domain


def test_distribution():

    start_time = datetime.datetime(2015, 3, 1)

    # v. simple
    a = TimeSeries()
    a.set(start_time, 1)
    a.set(datetime.datetime(2015, 3, 2), 0)
    a.set(datetime.datetime(2015, 3, 3), 1)
    a.set(datetime.datetime(2015, 3, 4), 0)
    end_time = datetime.datetime(2015, 3, 5)

    # not normalized
    distribution = a.distribution(
        start_time=start_time, end_time=end_time, normalized=False,
    )
    assert distribution[0] == 24 * 60 * 60 * 2  # two days
    assert distribution[1] == 24 * 60 * 60 * 2

    # normalized
    distribution = a.distribution(start_time=start_time, end_time=end_time)
    assert distribution[0] == 0.5
    assert distribution[1] == 0.5


def test_default_values():

    # v. simple
    a = TimeSeries()
    a.set(datetime.datetime(2015, 3, 1), 1)
    a.set(datetime.datetime(2015, 3, 2), 0)
    a.set(datetime.datetime(2015, 3, 3), 1)
    a.set(datetime.datetime(2015, 3, 4), 0)

    # not normalized
    nose.tools.assert_raises(ValueError, a.distribution)
    # distribution = a.distribution()
    #
    # total = 24 * 60 * 60 * 3
    # assert distribution[0] == 24 * 60 * 60 * 1 / float(total)
    # assert distribution[1] == 24 * 60 * 60 * 2 / float(total)


def test_mask():

    start_time = datetime.datetime(2015, 3, 1)

    # v. simple
    a = TimeSeries()
    a.set(start_time, 1)
    a.set(datetime.datetime(2015, 3, 2), 0)
    a.set(datetime.datetime(2015, 3, 3), 1)
    a.set(datetime.datetime(2015, 3, 4), 0)
    end_time = datetime.datetime(2015, 3, 5)

    mask = Domain(datetime.datetime(2015, 3, 1), datetime.datetime(2015, 3, 3))

    # not normalized
    distribution = a.distribution(
        start_time=start_time, end_time=end_time, normalized=False, mask=mask,
    )
    assert distribution[0] == 24 * 60 * 60  # one day
    assert distribution[1] == 24 * 60 * 60

    # normalized
    distribution = a.distribution(
        start_time=start_time, end_time=end_time, mask=mask,
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

    distribution = a.distribution(start_time=0, end_time=6)

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
