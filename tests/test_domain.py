from traces import TimeSeries, DefaultTimeSeries
import nose
import warnings


def check_warning(warn, fun, *args):
    with warnings.catch_warnings(record=True) as w:
        fun(*args)
        assert len(w) == 1
        assert issubclass(w[-1].category, warn)


def test_is_time_in_domain():
    ts = TimeSeries(domain=[0, 8])
    assert ts.is_time_in_domain(-2) == False
    assert ts.is_time_in_domain(0) == True
    assert ts.is_time_in_domain(6) == True
    assert ts.is_time_in_domain(8) == False
    assert ts.is_time_in_domain(10) == False


def test_is_data_in_domain():
    ts = TimeSeries(domain=[0, 8])
    data1 = [(1, 2), (2, 3), (6, 1), (7, 4)]
    data2 = [(-1, 2), (1, 2), (2, 3)]
    data3 = [(1, 2), (2, 3), (6, 1), (9, 4)]

    ts_domain = DefaultTimeSeries(default_values=False)
    ts_domain[1] = True
    ts_domain[9] = False

    assert ts.is_data_in_domain(data1, ts_domain) == True
    assert ts.is_data_in_domain(data2, ts_domain) == False
    assert ts.is_data_in_domain(data3, ts_domain) == False


def test_default_time_series():
    ts = DefaultTimeSeries()
    assert ts[0] == None
    assert ts.default() == None

    ts = DefaultTimeSeries(default_values=False)
    assert ts[0] == False
    assert ts.default() == False

    ts[1] = True
    assert ts[2] == True
    assert ts[0] == False
    assert ts.default() == False


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

    ts.set_domain([[None, 1], [2, 5]])
    assert ts.domain[0] == True
    assert ts.domain[1] == False
    assert ts.domain[1.5] == False
    assert ts.domain[2] == True
    assert ts.domain[3] == True
    assert ts.domain[5] == False
    assert ts.domain[6.7] == False

    ts.set_domain([[2, 5], [9, None]])
    assert ts.domain[0] == False
    assert ts.domain[2] == True
    assert ts.domain[3] == True
    assert ts.domain[5] == False
    assert ts.domain[6.7] == False
    assert ts.domain[9] == True
    assert ts.domain[9.6] == True

    ts = TimeSeries(data=[(1, 2), (2, 3), (6, 1), (8, 4)])
    nose.tools.assert_raises(ValueError, ts.set_domain, [1.5, 7])
    nose.tools.assert_raises(ValueError, ts.set_domain, [0, 7])
    nose.tools.assert_raises(ValueError, ts.set_domain, [1.5, 9])


def test_get_domain():
    ts = TimeSeries()
    assert ts.get_domain() == None

    ts.set_domain(None)
    assert ts.get_domain() == None

    ts.set_domain([None, 5])
    assert ts.get_domain() == [None, 5]

    ts.set_domain([5, None])
    assert ts.get_domain() == [5, None]

    ts.set_domain([None, None])
    assert ts.get_domain() == None

    ts.set_domain([2, 5])
    assert ts.get_domain() == [2, 5]

    ts.set_domain([[2, 5], [9, 10]])
    assert ts.get_domain() == [[2, 5], [9, 10]]

    ts.set_domain([[None, 1], [2, 5], [9, 10]])
    assert ts.get_domain() == [[None, 1], [2, 5], [9, 10]]

    ts.set_domain([[2, 5], [9, 10], [11, None]])
    assert ts.get_domain() == [[2, 5], [9, 10], [11, None]]

    ts.set_domain([[None, 1], [2, 5], [9, 10], [11, None]])
    assert ts.get_domain() == [[None, 1], [2, 5], [9, 10], [11, None]]


def test_time_series():

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


def test_slice():
    ts = TimeSeries(data=[(1, 2), (2, 3), (6, 1), (8, 4)])
    ts.set_domain([0, 8.5])

    nose.tools.assert_raises(ValueError, ts.slice, -1, 4)
    nose.tools.assert_raises(ValueError, ts.slice, 0, 9)
