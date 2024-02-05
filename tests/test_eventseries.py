import pandas as pd

from traces import EventSeries


def test_init_data():
    es = EventSeries([0, 0, 6, 8.7, 10])

    assert es[0] == 0
    assert es[1] == 0
    assert es[2] == 6
    assert es[3] == 8.7
    assert es[4] == 10

    data = [
        "2018-10-15T16:45:01",
        "2019-04-16T13:08:26",
    ]
    es = EventSeries(pd.to_datetime(data))
    assert es[0] == es[0]


def test_count_active():
    es_open = EventSeries(
        ["08:00", "09:00", "13:00", "07:00", "06:30", "13:00"]
    )
    es_closed = EventSeries(["08:00", "08:30", "12:00", "12:00", "12:00"])
    ts = EventSeries.count_active(es_open, es_closed)

    assert ts["06:30"] == 1
    assert ts["07:00"] == 2
    assert ts["08:00"] == 2
    assert ts["12:00"] == -1
    assert ts["13:00"] == 1


def test_cumulative_sum():
    es = EventSeries([1, 1, 4, 5, 9, 6, 3, 9, 15])
    result = [(1, 2), (3, 3), (4, 4), (5, 5), (6, 6), (9, 8), (15, 9)]
    assert list(es.cumulative_sum().items()) == result


def test_events_between():
    es = EventSeries([1, 1, 4, 5, 9, 6, 3, 9, 15])
    assert es.events_between(1, 3) == 3
    assert es.events_between(1, 2.5) == 2
    assert es.events_between(16, 20) == 0
    assert es.events_between(-10, 0) == 0
    assert es.events_between(-10, 1) == 2
    assert es.events_between(-10, 100) == len(es)
