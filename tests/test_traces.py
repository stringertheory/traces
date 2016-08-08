from traces import TimeSeries


def test_get():
    ts = TimeSeries()
    ts[1.2] = 1
    ts[3] = 0
    ts[6] = 2

    assert ts[0] == 1
    assert ts[5.5] == 0
    assert ts[7] == 2
