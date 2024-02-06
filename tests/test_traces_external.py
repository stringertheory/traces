import csv
import os
from datetime import datetime, timedelta

import pandas as pd
from dateutil.parser import parse as date_parse
from pandas.testing import assert_series_equal

from traces import TimeSeries


def test_csv():
    filename = "sample.csv"
    with open(filename, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["hour", "value"])
        writer.writerow(["2000-01-01 10:00am", "15"])
        writer.writerow(["2000-01-01 11:00am", "34"])
        writer.writerow(["2000-01-01 12:00pm", "19"])
        writer.writerow(["2000-01-01 1:00pm", "nan"])
        writer.writerow(["2000-01-01 2:00pm", "18"])
        writer.writerow(["2000-01-01 3:00pm", "nan"])

    ts = TimeSeries.from_csv(filename, time_transform=date_parse)
    os.remove(filename)

    assert ts[datetime(2000, 1, 1, 9)] is None
    assert ts[datetime(2000, 1, 1, 10, 30)] == "15"
    assert ts[datetime(2000, 1, 1, 20)] == "nan"


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
