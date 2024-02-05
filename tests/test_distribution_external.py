from pandas import Timestamp

from traces import TimeSeries


def test_pandas_timestamp_range():
    ts = TimeSeries(
        {
            Timestamp("2022-10-09 08:48:47"): 5.5,
            Timestamp("2022-10-09 10:36:47"): 51.4,
            Timestamp("2022-10-09 10:38:47"): 15.2,
            Timestamp("2022-10-09 10:38:56"): 0.1,
            Timestamp("2022-10-09 10:41:25"): 4.5,
        }
    )
    assert ts.distribution().max() == 51.4
    print(ts.distribution())

    with_start_end = ts.distribution(
        start=Timestamp("2022-10-09 07:55:10"),
        end=Timestamp("2022-10-09 10:56:32"),
    )
    assert with_start_end.max() == 51.4
    assert with_start_end.min() == 0.1
