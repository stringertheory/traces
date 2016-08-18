from traces import TimeSeries
import nose


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
    nose.tools.assert_raises(ValueError, ts.get, 0)

    ts[1.2] = 1
    ts[3] = 0
    ts[6] = 2

    assert ts[0] == 1
    assert ts[5.5] == 0
    assert ts[7] == 2


def test_update():
    ts = TimeSeries([(1, 2), (2, 3), (6, 1), (8, 4)])
    ts.update([(9, 1), (12, 4)])

    assert ts[8.5] == 4
    assert ts[9] == 1
    assert ts[10] == 1
    assert ts[12] == 4
    assert ts[15] == 4

    ts = TimeSeries([(1, 2), (2, 3), (6, 1), (8, 4)])
    ts.update([(4, 2), (7, 3)])

    assert ts[3] == 3
    assert ts[4] == 2
    assert ts[5] == 2
    assert ts[6] == 1
    assert ts[6.5] == 1
    assert ts[7] == 3
    assert ts[7.5] == 3
    assert ts[8] == 4

    ts = TimeSeries([(1, 2), (2, 3), (6, 1), (8, 4)])
    ts.update([(0, 1)])

    assert ts[-1] == 1
    assert ts[0] == 1
    assert ts[0.5] == 1
    assert ts[1] == 2

    ts = TimeSeries([(1, 2), (2, 3), (6, 1), (8, 4)])
    ts.update([(4, 1), (7, 4)], compact=True)

    assert ts.items() == [(1, 2), (2, 3), (4, 1), (7, 4)]

