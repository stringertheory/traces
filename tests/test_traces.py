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
