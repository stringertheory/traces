import pandas as pd

from traces import EventSeries, TimeSeries


def test_cumsum():
    # Test with basic timestamp data
    data = [
        "2018-10-15T16:45:01",
        "2019-04-16T13:08:26",
        "2019-02-22T12:05:08",
        "2019-04-16T13:09:06",
        "2019-04-16T13:09:13",
        "2019-04-16T13:09:28",
        "2019-04-16T13:09:29",
        "2019-04-16T13:10:20",
        "2019-04-16T13:10:30",
        "2019-03-08T16:46:48",
        "2019-04-16T13:09:29",
        "2019-04-16T13:10:20",
    ]
    es = EventSeries(pd.to_datetime(data))

    ref = {
        pd.Timestamp("2018-10-15 16:45:01"): 1,
        pd.Timestamp("2019-02-22 12:05:08"): 2,
        pd.Timestamp("2019-03-08 16:46:48"): 3,
        pd.Timestamp("2019-04-16 13:08:26"): 4,
        pd.Timestamp("2019-04-16 13:09:06"): 5,
        pd.Timestamp("2019-04-16 13:09:13"): 6,
        pd.Timestamp("2019-04-16 13:09:28"): 7,
        pd.Timestamp("2019-04-16 13:09:29"): 9,
        pd.Timestamp("2019-04-16 13:10:20"): 11,
        pd.Timestamp("2019-04-16 13:10:30"): 12,
    }

    reference = TimeSeries(ref, default=0)

    assert es.cumsum() == reference

    # check default is 0
    assert es.cumsum()[pd.Timestamp("2015-01-01")] == 0

    # Test Empty Series
    es = EventSeries()
    assert es.cumsum() == TimeSeries(default=0)


def test_events_between():
    data = [
        "2018-10-15T16:45:01",
        "2019-04-16T13:08:26",
        "2019-02-22T12:05:08",
        "2019-04-16T13:09:06",
        "2019-04-16T13:09:13",
        "2019-04-16T13:09:28",
        "2019-04-16T13:09:29",
        "2019-04-16T13:10:20",
        "2019-04-16T13:10:30",
        "2019-03-08T16:46:48",
        "2019-04-16T13:09:29",
        "2019-04-16T13:10:20",
    ]
    es = EventSeries(pd.to_datetime(data))

    assert (
        es.events_between(
            pd.Timestamp("2018-01-01"), pd.Timestamp("2020-01-01")
        )
        == 12
    )
    assert (
        es.events_between(
            pd.Timestamp("2018-01-01"), pd.Timestamp("2019-01-01")
        )
        == 1
    )
    assert (
        es.events_between(
            pd.Timestamp("2020-01-01"), pd.Timestamp("2020-02-01")
        )
        == 0
    )
    assert (
        es.events_between(
            pd.Timestamp("2016-01-01"), pd.Timestamp("2017-02-01")
        )
        == 0
    )

    # Test closed boundaries on end points
    # left
    assert (
        es.events_between(
            pd.Timestamp("2018-10-15 16:45:01"),
            pd.Timestamp("2019-04-15 12:00:00"),
        )
        == 3
    )
    # right
    assert (
        es.events_between(
            pd.Timestamp("2019-02-28 12:00:00"),
            pd.Timestamp("2019-04-16 13:10:20"),
        )
        == 9
    )
    # both
    assert (
        es.events_between(
            pd.Timestamp("2019-02-22 12:05:08"),
            pd.Timestamp("2019-04-16 13:10:20"),
        )
        == 10
    )


def test_time_lag():
    data = [
        "2019-02-01",
        "2019-02-28",
        "2019-02-22",
        "2019-02-16",
        "2019-02-26",
        "2019-02-16",
        "2019-02-16",
    ]
    es = EventSeries(pd.to_datetime(data))

    time_lag = list(es.iter_interevent_times())
    assert time_lag[0] == pd.Timedelta(days=15)
    assert time_lag[1] == pd.Timedelta(days=0)

    # Make sure we got the right shape
    assert len(time_lag) == len(data) - 1
    print(time_lag)
