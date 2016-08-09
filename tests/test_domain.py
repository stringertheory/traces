from traces import TimeSeries, DefaultTimeSeries
import nose


def test_default_time_series():
    ts = DefaultTimeSeries()
    assert ts[0] == None

    ts = DefaultTimeSeries(default_values=False)
    assert ts[0] == False

    ts[1] = True
    assert ts[2] == True
    assert ts[0] == False


def test_set_domain():

    ts = TimeSeries()
    assert ts.domain == None

    ts.set_domain(None)
    assert ts.domain == None

    ts.set_domain([None, 5])
    assert ts.domain[3] == True
    assert ts.domain[5] == False
    assert ts.domain[6.7] == False

    ts.set_domain([5, None])
    assert ts.domain[3] == False
    assert ts.domain[5] == True
    assert ts.domain[6.7] == True

    ts.set_domain([None, None])
    assert ts.domain == None

    ts.set_domain([2, 5])
    assert ts.domain[0] == False
    assert ts.domain[2] == True
    assert ts.domain[3] == True
    assert ts.domain[5] == False
    assert ts.domain[6.7] == False

    ts.set_domain([[2, 5], [9, 10]])
    assert ts.domain[0] == False
    assert ts.domain[2] == True
    assert ts.domain[3] == True
    assert ts.domain[5] == False
    assert ts.domain[6.7] == False
    assert ts.domain[9] == True
    assert ts.domain[9.6] == True
    assert ts.domain[10] == False
    assert ts.domain[21.2] == False

    # TODO: check when time series is not empty


def test_time_series():
    ts = TimeSeries(data=[(1, 2), (2, 3), (6, 1), (8, 4)])
    nose.tools.assert_raises(ValueError, ts.set_domain, [1.5, 7])

    ts = TimeSeries(data=[(1, 2), (2, 3), (6, 1), (8, 4)])
    ts.set_domain([1, 8.5])
    nose.tools.assert_raises(ValueError, ts.get, 0)
    assert ts[1.5] == 2
    assert ts[2.4] == 3
    assert ts[6] == 1
    nose.tools.assert_raises(ValueError, ts.get, 8.5)
    nose.tools.assert_raises(ValueError, ts.get, 9)

    ts[5] = 7
    nose.tools.assert_raises(ValueError, ts.set, 9, 10)
    nose.tools.assert_raises(ValueError, ts.set, 0, 10)

    nose.tools.assert_raises(ValueError, TimeSeries,
                             data=[(1, 2), (2, 3), (6, 1), (8, 4)],
                             domain=[1.5, 7])

