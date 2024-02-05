import csv
import os
import pickle
from datetime import datetime, timedelta

import pandas as pd
import pytest
from pandas.testing import assert_series_equal

from traces import TimeSeries


def test_init_data():
    ts = TimeSeries([(1, 2), (2, 3), (6, 1), (8, 4)])

    assert ts[0] is None
    assert ts[1] == 2
    assert ts[1.5] == 2
    assert ts[6] == 1
    assert ts[7] == 1
    assert ts[8] == 4
    assert ts[10] == 4

    ts = TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]])

    assert ts[0] is None
    assert ts[1] == 2
    assert ts[1.5] == 2
    assert ts[6] == 1
    assert ts[7] == 1
    assert ts[8] == 4
    assert ts[10] == 4

    ts = TimeSeries({1: 2, 2: 3, 6: 1, 8: 4})

    assert ts[0] is None
    assert ts[1] == 2
    assert ts[1.5] == 2
    assert ts[6] == 1
    assert ts[7] == 1
    assert ts[8] == 4
    assert ts[10] == 4


def test_get():
    ts = TimeSeries()
    assert ts[0] is None

    ts[1.2] = 1
    ts[3] = 0
    ts[6] = 2

    assert ts[0] is None
    assert ts[5.5] == 0
    assert ts[7] == 2


def test_exists():
    ts = TimeSeries([(-5, 0), (0, 23), (5, None)])

    ts_exists = ts.exists()
    assert ts_exists[-10] is False
    assert ts_exists[-2] is True
    assert ts_exists[3] is True
    assert ts_exists[10] is False


def test_merge():
    ts_a = TimeSeries()
    ts_b = TimeSeries()
    # ts_a[0] = None
    ts_b[0] = True
    ts_merge = TimeSeries.merge([ts_a, ts_b])

    assert True in ts_merge[0]
    assert None in ts_merge[0]

    ts_c = TimeSeries.merge([])
    assert list(ts_c.items()) == []


def test_set_interval():
    ts = TimeSeries()

    assert ts[0] is None

    ts.set_interval(2, 4, 5)

    assert ts[0] is None
    assert ts[2] == 5
    assert ts[3] == 5
    assert ts[4] is None
    assert ts[5] is None

    ts = TimeSeries()
    ts[1.2] = 1
    ts[3] = 0
    ts[6] = 2

    assert ts[0] is None
    assert ts[5.5] == 0
    assert ts[7] == 2

    ts[2:4] = 5
    assert list(ts.items()) == [(1.2, 1), (2, 5), (4, 0), (6, 2)]

    ts[3:5] = 4
    assert list(ts.items()) == [(1.2, 1), (2, 5), (3, 4), (5, 0), (6, 2)]

    tsc = TimeSeries(ts)

    ts.set_interval(3, 4, 4)
    assert list(ts.items()) == [
        (1.2, 1),
        (2, 5),
        (3, 4),
        (4, 4),
        (5, 0),
        (6, 2),
    ]

    tsc.set_interval(3, 4, 4, compact=True)
    assert list(tsc.items()) == [(1.2, 1), (2, 5), (3, 4), (5, 0), (6, 2)]

    tsd = TimeSeries()
    pytest.raises(ValueError, tsd.set_interval, 4, 4, 4)

    tsd = TimeSeries()
    pytest.raises(ValueError, tsd.set_interval, 4, 3, 4)


def test_set_interval_datetime():
    ts = TimeSeries(default=400)
    ts[datetime(2012, 1, 4, 12)] = 5
    ts[datetime(2012, 1, 9, 18)] = 10
    ts[datetime(2012, 1, 8) : datetime(2012, 1, 10)] = 100

    assert list(ts.items()) == [
        (datetime(2012, 1, 4, 12, 0), 5),
        (datetime(2012, 1, 8, 0, 0), 100),
        (datetime(2012, 1, 10, 0, 0), 10),
    ]


def test_remove_points_from_interval():
    ts = TimeSeries(default=0)
    ts[0] = 0
    ts[1] = 2
    ts[3] = 1
    ts[4] = 0

    assert ts[5] == 0

    del ts[3.5:4.5]

    assert ts[5] == 1

    ts[4] = 0

    del ts[3:4.5]

    assert ts[5] == 2

    ts[3] = 1
    ts[4] = 0

    del ts[3.5:4]

    assert ts[5] == 0


def test_sample_interval_days():
    ts = TimeSeries([(datetime(2012, 1, 1), 400), (datetime(2012, 3, 1), 400)])
    ts[datetime(2012, 1, 4) : datetime(2012, 1, 20)] = 10
    ts[datetime(2012, 1, 25) : datetime(2012, 2, 7)] = 50
    ts[datetime(2012, 1, 19) : datetime(2012, 1, 27)] = 0

    sr = ts.sample_interval(
        sampling_period=timedelta(days=1), end=datetime(2012, 2, 1)
    )
    assert list(sr.items()) == [
        (pd.Timestamp("2012-01-01 00:00:00"), 400.0),
        (pd.Timestamp("2012-01-02 00:00:00"), 400.0),
        (pd.Timestamp("2012-01-03 00:00:00"), 400.0),
        (pd.Timestamp("2012-01-04 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-05 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-06 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-07 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-08 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-09 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-10 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-11 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-12 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-13 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-14 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-15 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-16 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-17 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-18 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-19 00:00:00"), 0.0),
        (pd.Timestamp("2012-01-20 00:00:00"), 0.0),
        (pd.Timestamp("2012-01-21 00:00:00"), 0.0),
        (pd.Timestamp("2012-01-22 00:00:00"), 0.0),
        (pd.Timestamp("2012-01-23 00:00:00"), 0.0),
        (pd.Timestamp("2012-01-24 00:00:00"), 0.0),
        (pd.Timestamp("2012-01-25 00:00:00"), 0.0),
        (pd.Timestamp("2012-01-26 00:00:00"), 0.0),
        (pd.Timestamp("2012-01-27 00:00:00"), 50.0),
        (pd.Timestamp("2012-01-28 00:00:00"), 50.0),
        (pd.Timestamp("2012-01-29 00:00:00"), 50.0),
        (pd.Timestamp("2012-01-30 00:00:00"), 50.0),
        (pd.Timestamp("2012-01-31 00:00:00"), 50.0),
    ]


def test_sample_interval_hours():
    ts = TimeSeries([(datetime(2012, 1, 1), 400), (datetime(2012, 1, 10), 400)])

    ts[datetime(2012, 1, 4, 12) : datetime(2012, 1, 6, 20)] = 10
    ts[datetime(2012, 1, 7, 9) : datetime(2012, 1, 10)] = 50

    sr = ts.sample_interval(sampling_period=timedelta(days=1))
    assert list(sr.items()) == [
        (pd.Timestamp("2012-01-01 00:00:00"), 400.0),
        (pd.Timestamp("2012-01-02 00:00:00"), 400.0),
        (pd.Timestamp("2012-01-03 00:00:00"), 400.0),
        (pd.Timestamp("2012-01-04 00:00:00"), 205.0),
        (pd.Timestamp("2012-01-05 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-06 00:00:00"), 75.0),
        (pd.Timestamp("2012-01-07 00:00:00"), 181.25),
        (pd.Timestamp("2012-01-08 00:00:00"), 50.0),
        (pd.Timestamp("2012-01-09 00:00:00"), 50.0),
    ]

    sr = ts.sample_interval(sampling_period=timedelta(days=1), operation="max")
    assert list(sr.items()) == [
        (pd.Timestamp("2012-01-01 00:00:00"), 400.0),
        (pd.Timestamp("2012-01-02 00:00:00"), 400.0),
        (pd.Timestamp("2012-01-03 00:00:00"), 400.0),
        (pd.Timestamp("2012-01-04 00:00:00"), 400.0),
        (pd.Timestamp("2012-01-05 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-06 00:00:00"), 400.0),
        (pd.Timestamp("2012-01-07 00:00:00"), 400.0),
        (pd.Timestamp("2012-01-08 00:00:00"), 50.0),
        (pd.Timestamp("2012-01-09 00:00:00"), 50.0),
    ]

    sr = ts.sample_interval(sampling_period=timedelta(days=1), operation="min")
    assert list(sr.items()) == [
        (pd.Timestamp("2012-01-01 00:00:00"), 400.0),
        (pd.Timestamp("2012-01-02 00:00:00"), 400.0),
        (pd.Timestamp("2012-01-03 00:00:00"), 400.0),
        (pd.Timestamp("2012-01-04 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-05 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-06 00:00:00"), 10.0),
        (pd.Timestamp("2012-01-07 00:00:00"), 50.0),
        (pd.Timestamp("2012-01-08 00:00:00"), 50.0),
        (pd.Timestamp("2012-01-09 00:00:00"), 50.0),
    ]


def test_sample_interval_index():
    start = datetime(2012, 1, 1)
    end = datetime(2012, 1, 10)

    ts = TimeSeries([(start, 400), (end, 400)])

    ts[datetime(2012, 1, 4, 12) : datetime(2012, 1, 6, 20)] = 10
    ts[datetime(2012, 1, 7, 9) : datetime(2012, 1, 10)] = 50

    idx = pd.date_range(start, end, freq="D")
    sr = ts.sample_interval(sampling_period=timedelta(days=1))
    sr2 = ts.sample_interval(idx=idx)

    assert_series_equal(sr, sr2)


def test_pickle():
    ts = TimeSeries(default=False)
    ts[1] = True
    ts[2] = False
    dump_string = pickle.dumps(ts)
    unpickled = pickle.loads(dump_string)  # noqa: S301
    assert unpickled == ts

    unpickled[3] = unpickled[1]
    assert unpickled[3] is True


def test_csv():
    def time_parse(value):
        return int(value)

    def value_parse(value):
        try:
            return int(value)
        except ValueError:
            return None

    filename = "sample.csv"
    with open(filename, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["hour", "value"])
        writer.writerow(["10", "15"])
        writer.writerow(["11", "34"])
        writer.writerow(["12", "19"])
        writer.writerow(["13", "nan"])
        writer.writerow(["14", "18"])
        writer.writerow(["15", "nan"])

    ts = TimeSeries.from_csv(
        filename,
        time_column=0,
        time_transform=time_parse,
        value_column=1,
        value_transform=value_parse,
        default=None,
    )
    os.remove(filename)

    assert ts[9] is None
    assert ts[20] is None
    assert ts[13.5] is None

    histogram = ts.distribution()
    assert histogram.mean() == pytest.approx((15 + 34 + 19 + 18) / 4.0)

    filename = "sample.csv"
    with open(filename, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["hour", "value"])
        writer.writerow(["2000-01-01 10:00:00", "15"])
        writer.writerow(["2000-01-01 11:00:00", "34"])
        writer.writerow(["2000-01-01 12:00:00", "19"])
        writer.writerow(["2000-01-01 13:00:00", "nan"])
        writer.writerow(["2000-01-01 14:00:00", "18"])
        writer.writerow(["2000-01-01 15:00:00", "nan"])

    ts = TimeSeries.from_csv(filename)
    os.remove(filename)

    assert ts[datetime(2000, 1, 1, 9)] is None
    assert ts[datetime(2000, 1, 1, 10, 30)] == "15"
    assert ts[datetime(2000, 1, 1, 20)] == "nan"


def test_set_same_interval_twice():
    tr = TimeSeries({0: 10, 100: 10})

    tr[17:42] = 0
    assert list(tr.items()) == [(0, 10), (17, 0), (42, 10), (100, 10)]

    tr[17:42] = 0
    assert list(tr.items()) == [(0, 10), (17, 0), (42, 10), (100, 10)]


def test_convenience_access_methods():
    ts = TimeSeries([(1, 2), (2, 3), (6, 1), (8, 4)])
    assert ts.first_key() == 1
    assert ts.first_value() == 2
    assert ts.first_item() == (1, 2)
    assert ts.last_key() == 8
    assert ts.last_value() == 4
    assert ts.last_item() == (8, 4)
    assert ts.get_item_by_index(0) == (1, 2)
    assert ts.get_item_by_index(-1) == (8, 4)
