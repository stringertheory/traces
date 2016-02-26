import datetime

import nose

from traces import TimeSeries


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
    distribution = a.distribution()

    total = 24 * 60 * 60 * 3
    assert distribution[0] == 24 * 60 * 60 * 1 / float(total)
    assert distribution[1] == 24 * 60 * 60 * 2 / float(total)


def test_mask():

    start_time = datetime.datetime(2015, 3, 1)

    # v. simple
    a = TimeSeries()
    a.set(start_time, 1)
    a.set(datetime.datetime(2015, 3, 2), 0)
    a.set(datetime.datetime(2015, 3, 3), 1)
    a.set(datetime.datetime(2015, 3, 4), 0)
    end_time = datetime.datetime(2015, 3, 5)

    mask = TimeSeries()
    mask.set(datetime.datetime(2015, 3, 1), 1)
    mask.set(datetime.datetime(2015, 3, 3), 0)

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
