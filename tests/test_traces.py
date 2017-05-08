from datetime import datetime, timedelta
import pickle

import nose
from traces import Histogram, TimeSeries


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


def test_merge():
    ts_a = TimeSeries(default=None)
    ts_b = TimeSeries(default=None)
    ts_a[0] = None
    ts_b[0] = True
    ts_merge = TimeSeries.merge([ts_a, ts_b])

    assert True in ts_merge[0]
    assert None in ts_merge[0]


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
    ts = TimeSeries(default=400)
    ts[datetime(2012, 1, 4, 12)] = 5
    ts[datetime(2012, 1, 9, 18)] = 10
    ts[datetime(2012, 1, 8):datetime(2012, 1, 10)] = 100

    assert ts.items() == [(datetime(2012, 1, 4, 12, 0), 5),
                          (datetime(2012, 1, 8, 0, 0), 100),
                          (datetime(2012, 1, 10, 0, 0), 10)]

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

def test_pickle():
    ts = TimeSeries(default=False)
    ts[1] = True
    ts[2] = False
    dump_string = pickle.dumps(ts)
    unpickled = pickle.loads(dump_string)
    assert unpickled == ts
