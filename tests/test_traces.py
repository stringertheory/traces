from datetime import datetime, timedelta

import nose

from traces import TimeSeries


def test_init_data():
    ts = TimeSeries([(1, 2), (2, 3), (6, 1), (8, 4)])

    assert ts[0] == 2
    assert ts[1] == 2
    assert ts[1.5] == 2
    assert ts[6] == 1
    assert ts[7] == 1
    assert ts[8] == 4
    assert ts[10] == 4

    ts = TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]])

    assert ts[0] == 2
    assert ts[1] == 2
    assert ts[1.5] == 2
    assert ts[6] == 1
    assert ts[7] == 1
    assert ts[8] == 4
    assert ts[10] == 4

    ts = TimeSeries({1: 2, 2: 3, 6: 1, 8: 4})

    assert ts[0] == 2
    assert ts[1] == 2
    assert ts[1.5] == 2
    assert ts[6] == 1
    assert ts[7] == 1
    assert ts[8] == 4
    assert ts[10] == 4


def test_get():
    ts = TimeSeries()
    nose.tools.assert_raises(KeyError, ts.get, 0)

    ts[1.2] = 1
    ts[3] = 0
    ts[6] = 2

    assert ts[0] == 1
    assert ts[5.5] == 0
    assert ts[7] == 2


def test_set_interval():
    ts = TimeSeries()
    nose.tools.assert_raises(KeyError, ts.get, 0)

    nose.tools.assert_raises(KeyError, ts.set_interval, 2, 4, 5)

    ts[1.2] = 1
    ts[3] = 0
    ts[6] = 2

    assert ts[0] == 1
    assert ts[5.5] == 0
    assert ts[7] == 2

    ts[2:4] = 5
    assert ts.items() == [(1.2, 1), (2, 5), (4, 0), (6, 2)]

    ts[3:5] = 4
    assert ts.items() == [(1.2, 1), (2, 5), (3, 4), (5, 0), (6, 2)]

    tsc = TimeSeries(ts)

    ts.set_interval(3, 4, 4)
    assert ts.items() == [(1.2, 1), (2, 5), (3, 4), (4, 4), (5, 0), (6, 2)]

    tsc.set_interval(3, 4, 4, compact=True)
    assert tsc.items() == [(1.2, 1), (2, 5), (3, 4), (5, 0), (6, 2)]


def test_set_interval_datetime():
    ts = TimeSeries(domain=(datetime(2012, 1, 1), datetime(2015, 2, 1)),
                    default=400)
    ts[datetime(2012, 1, 4, 12)] = 5
    ts[datetime(2012, 1, 9, 18)] = 10
    ts[datetime(2012, 1, 8):datetime(2012, 1, 10)] = 100

    assert ts.items() == [(datetime(2012, 1, 4, 12, 0), 5),
                          (datetime(2012, 1, 8, 0, 0), 100),
                          (datetime(2012, 1, 10, 0, 0), 10)]


def test_sample_interval_days():
    import pandas as pd
    ts = TimeSeries(domain=(datetime(2012, 1, 1), datetime(2012, 3, 1)),
                    default=400)

    ts[datetime(2012, 1, 4):datetime(2012, 1, 20)] = 10
    ts[datetime(2012, 1, 25):datetime(2012, 2, 7)] = 50
    ts[datetime(2012, 1, 19):datetime(2012, 1, 27)] = 0

    sr = ts.sample_interval(sampling_period=timedelta(days=1), end=datetime(2012, 2, 1))

    assert list(sr.iteritems()) == [(pd.Timestamp('2012-01-01 00:00:00'), 400.0),
                                    (pd.Timestamp('2012-01-02 00:00:00'), 400.0),
                                    (pd.Timestamp('2012-01-03 00:00:00'), 400.0),
                                    (pd.Timestamp('2012-01-04 00:00:00'), 10.0),
                                    (pd.Timestamp('2012-01-05 00:00:00'), 10.0),
                                    (pd.Timestamp('2012-01-06 00:00:00'), 10.0),
                                    (pd.Timestamp('2012-01-07 00:00:00'), 10.0),
                                    (pd.Timestamp('2012-01-08 00:00:00'), 10.0),
                                    (pd.Timestamp('2012-01-09 00:00:00'), 10.0),
                                    (pd.Timestamp('2012-01-10 00:00:00'), 10.0),
                                    (pd.Timestamp('2012-01-11 00:00:00'), 10.0),
                                    (pd.Timestamp('2012-01-12 00:00:00'), 10.0),
                                    (pd.Timestamp('2012-01-13 00:00:00'), 10.0),
                                    (pd.Timestamp('2012-01-14 00:00:00'), 10.0),
                                    (pd.Timestamp('2012-01-15 00:00:00'), 10.0),
                                    (pd.Timestamp('2012-01-16 00:00:00'), 10.0),
                                    (pd.Timestamp('2012-01-17 00:00:00'), 10.0),
                                    (pd.Timestamp('2012-01-18 00:00:00'), 10.0),
                                    (pd.Timestamp('2012-01-19 00:00:00'), 0.0),
                                    (pd.Timestamp('2012-01-20 00:00:00'), 0.0),
                                    (pd.Timestamp('2012-01-21 00:00:00'), 0.0),
                                    (pd.Timestamp('2012-01-22 00:00:00'), 0.0),
                                    (pd.Timestamp('2012-01-23 00:00:00'), 0.0),
                                    (pd.Timestamp('2012-01-24 00:00:00'), 0.0),
                                    (pd.Timestamp('2012-01-25 00:00:00'), 0.0),
                                    (pd.Timestamp('2012-01-26 00:00:00'), 0.0),
                                    (pd.Timestamp('2012-01-27 00:00:00'), 50.0),
                                    (pd.Timestamp('2012-01-28 00:00:00'), 50.0),
                                    (pd.Timestamp('2012-01-29 00:00:00'), 50.0),
                                    (pd.Timestamp('2012-01-30 00:00:00'), 50.0),
                                    (pd.Timestamp('2012-01-31 00:00:00'), 50.0)]


def test_sample_interval_hours():
    import pandas as pd
    ts = TimeSeries(domain=(datetime(2012, 1, 1), datetime(2012, 1, 10)),
                    default=400)

    ts[datetime(2012, 1, 4, 12):datetime(2012, 1, 6, 20)] = 10
    ts[datetime(2012, 1, 7, 9):datetime(2012, 1, 10)] = 50

    sr = ts.sample_interval(sampling_period=timedelta(days=1))
    assert list(sr.items()) == [(pd.Timestamp('2012-01-01 00:00:00', offset='D'), 400.0),
                                (pd.Timestamp('2012-01-02 00:00:00', offset='D'), 400.0),
                                (pd.Timestamp('2012-01-03 00:00:00', offset='D'), 400.0),
                                (pd.Timestamp('2012-01-04 00:00:00', offset='D'), 205.0),
                                (pd.Timestamp('2012-01-05 00:00:00', offset='D'), 10.0),
                                (pd.Timestamp('2012-01-06 00:00:00', offset='D'), 75.0),
                                (pd.Timestamp('2012-01-07 00:00:00', offset='D'), 181.25),
                                (pd.Timestamp('2012-01-08 00:00:00', offset='D'), 50.0),
                                (pd.Timestamp('2012-01-09 00:00:00', offset='D'), 50.0)]

    sr = ts.sample_interval(sampling_period=timedelta(days=1), operation="max")
    assert list(sr.items()) == [(pd.Timestamp('2012-01-01 00:00:00', offset='D'), 400.0),
                                (pd.Timestamp('2012-01-02 00:00:00', offset='D'), 400.0),
                                (pd.Timestamp('2012-01-03 00:00:00', offset='D'), 400.0),
                                (pd.Timestamp('2012-01-04 00:00:00', offset='D'), 400.0),
                                (pd.Timestamp('2012-01-05 00:00:00', offset='D'), 10.0),
                                (pd.Timestamp('2012-01-06 00:00:00', offset='D'), 400.0),
                                (pd.Timestamp('2012-01-07 00:00:00', offset='D'), 400.0),
                                (pd.Timestamp('2012-01-08 00:00:00', offset='D'), 50.0),
                                (pd.Timestamp('2012-01-09 00:00:00', offset='D'), 50.0)]

    sr = ts.sample_interval(sampling_period=timedelta(days=1), operation="min")
    assert list(sr.items()) == [(pd.Timestamp('2012-01-01 00:00:00', offset='D'), 400.0),
                                (pd.Timestamp('2012-01-02 00:00:00', offset='D'), 400.0),
                                (pd.Timestamp('2012-01-03 00:00:00', offset='D'), 400.0),
                                (pd.Timestamp('2012-01-04 00:00:00', offset='D'), 10.0),
                                (pd.Timestamp('2012-01-05 00:00:00', offset='D'), 10.0),
                                (pd.Timestamp('2012-01-06 00:00:00', offset='D'), 10.0),
                                (pd.Timestamp('2012-01-07 00:00:00', offset='D'), 50.0),
                                (pd.Timestamp('2012-01-08 00:00:00', offset='D'), 50.0),
                                (pd.Timestamp('2012-01-09 00:00:00', offset='D'), 50.0)]
