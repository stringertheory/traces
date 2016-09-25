from traces import TimeSeries, inf, Domain

import nose

from datetime import datetime
from intervals import FloatInterval, DateTimeInterval
import warnings


# def check_warning(warn, fun, *args):
#     with warnings.catch_warnings(record=True) as w:
#         fun(*args)
#         assert len(w) == 1
#         assert issubclass(w[-1].category, warn)

def test_construct_domain():
    iterable_inputs = [
        [-inf, 3],
        [1, inf],
        [1, 2],
        [(1, 2), (4, 5)],
        [datetime(2011, 1, 1, 1), datetime(2011, 1, 2, 1)],
        [[datetime(2011, 1, 1, 1), datetime(2011, 1, 2, 1)],
         [datetime(2011, 1, 1, 1), datetime(2011, 1, 2, 1)]]
    ]

    iterable_inputs_answers = [
        [(-inf, 3)],
        [(1, inf)],
        [(1, 2)],
        [(1, 2), (4, 5)],
        [(datetime(2011, 1, 1, 1), datetime(2011, 1, 2, 1))],
        [(datetime(2011, 1, 1, 1), datetime(2011, 1, 2, 1))]
    ]

    bad_inputs = [
        ['a', 'b'],
        [1, datetime(2011, 1, 2, 1)],
        [[datetime(2011, 1, 1, 1), datetime(2011, 1, 2, 1)], [2, 3]]
    ]

    for inputs, answers in zip(iterable_inputs, iterable_inputs_answers):
        result = Domain(*inputs)._interval_list
        assert result == answers

    for inputs in bad_inputs:
        nose.tools.assert_raises(ValueError, Domain, *inputs)


def test_equal():
    dom = Domain([1, 2], [3, 4], [5, 6])
    assert dom == dom
    assert not (dom == Domain([1, 2]))
    assert not (dom == Domain([1, 2], [3, 6]))
    assert not (dom == Domain([1, 2], [3, 6], [7, 8]))

    dom = Domain([-inf, 2], [5, inf])
    assert dom == dom
    assert not (dom == Domain([-inf, inf]))
    assert not (dom == Domain([-inf, 1], [2, inf]))


def test_contain():
    dom = Domain([1, 2], [4, inf])
    assert (0 in dom) == False
    assert (1 in dom) == True
    assert (1.5 in dom) == True
    assert (2 in dom) == True
    assert (3 in dom) == False
    assert (4 in dom) == True
    assert (100 in dom) == True

    
def test_union():
    dom1 = Domain(1, 2)
    dom2 = Domain(3, 4)
    assert dom1.union(dom2)._interval_list == [(1, 2), (3, 4)]
    assert dom1._interval_list == [(1, 2)]
    assert dom2._interval_list == [(3, 4)]
    assert (dom1 | dom2)._interval_list == [(1, 2), (3, 4)]

    dom_list = [
        Domain(1, 2),
        Domain(3, 4),
        Domain(2, 5),
        Domain([1, 2], [9, 10])
    ]
    assert dom_list[0].union(*dom_list[1:])._interval_list == [(1, 5), (9, 10)]
    assert (dom_list[0] | dom_list[1] | dom_list[2] | dom_list[3])._interval_list == [(1, 5), (9, 10)]
    assert dom_list[0]._interval_list == [(1, 2)]
    assert dom_list[1]._interval_list == [(3, 4)]
    assert dom_list[2]._interval_list == [(2, 5)]
    assert dom_list[3]._interval_list == [(1, 2), (9, 10)]


def test_intersection():

    dom1 = Domain(1, 2)
    dom2 = Domain(3, 4)
    assert dom1.intersection(dom2)._interval_list == []
    assert (dom1 & dom2)._interval_list == []

    dom1 = Domain(1, 2)
    dom2 = Domain(2, 5)
    dom3 = Domain(6, 10)
    assert dom1.intersection(dom2, dom3)._interval_list == []
    assert (dom1 & dom2 & dom3)._interval_list == []

    dom1 = Domain(1, 3)
    dom2 = Domain(2, 4)
    assert dom1.intersection(dom2)._interval_list == [(2, 3)]
    assert (dom1 & dom2)._interval_list == [(2, 3)]
    

def test_start_end():
    dom = Domain()
    assert dom.start() == -inf
    assert dom.end() == inf

    dom = Domain([-1, 2])
    assert dom.start() == -1
    assert dom.end() == 2

    dom = Domain([-1, 2], [4, 5], [6, 10])
    assert dom.start() == -1
    assert dom.end() == 10

    dom = Domain([-inf, 2], [4, 5], [6, inf])
    assert dom.start() == -inf
    assert dom.end() == inf


def test_intervals():
    dom = Domain()
    assert list(dom.intervals()) == [(-inf, inf)]

    dom = Domain([-inf, 2], [6, inf])
    assert list(dom.intervals()) == [(-inf, 2), (6, inf)]

    dom = Domain([-1, 2], [4, 5], [6, 10])
    assert list(dom.intervals()) == [(-1, 2), (4, 5), (6, 10)]


def test_slice():
    dom = Domain([-1, 2], [4, 5], [6, 10])
    assert dom.slice(-3, 12) == Domain([-1, 2], [4, 5], [6, 10])
    assert dom.slice(-1, 10) == Domain([-1, 2], [4, 5], [6, 10])
    assert dom.slice(1, 9) == Domain([1, 2], [4, 5], [6, 9])
    assert dom.slice(4.5, 9) == Domain([4.5, 5], [6, 9])

    nose.tools.assert_raises(ValueError, dom.slice, 12, 3)


def test_is_data_in_domain():
    data1 = [(1, 2), (2, 3), (6, 1), (7, 4)]
    ts = TimeSeries(data=data1)

    # this shouldn't work
    nose.tools.assert_raises(ValueError, setattr, ts, 'domain', [3, 4])

    # this should work
    ts.domain = [0, 8]


def test_set_domain():

    ts = TimeSeries()
    assert ts.domain == Domain([-inf, inf])

    ts.domain = None
    assert ts.domain == Domain([-inf, inf])

    ts.domain = [-inf, 5]
    assert ts.domain == Domain([-inf, 5])

    ts.domain = [5, inf]
    assert ts.domain == Domain([5, inf])

    ts.domain = [-inf, inf]
    assert ts.domain == Domain([-inf, inf])

    ts.domain = [2, 5]
    assert ts.domain == Domain([2, 5])

    ts.domain = [[2, 5], [9, 10]]
    assert ts.domain == Domain([2, 5], [9, 10])

    ts = TimeSeries(data=[(1, 2), (2, 3), (6, 1), (8, 4)])

    nose.tools.assert_raises(ValueError, setattr, ts, 'domain', [1.5, 7])
    nose.tools.assert_raises(ValueError, setattr, ts, 'domain', [0, 7])
    nose.tools.assert_raises(ValueError, setattr, ts, 'domain', [1.5, 9])


def test_domain():

    ts = TimeSeries()
    assert ts.domain == Domain([-inf, inf])

    ts.domain = None
    assert ts.domain == Domain([-inf, inf])

    ts.domain = [-inf, 5]
    assert ts.domain == Domain([-inf, 5])

    ts.domain = [5, inf]
    assert ts.domain == Domain([5, inf])

    ts.domain = [-inf, inf]
    assert ts.domain == Domain(-inf, inf)

    ts.domain = [2, 5]
    assert ts.domain == Domain([2, 5])

    ts.domain = [[2, 5], [9, 10]]
    assert ts.domain == Domain([[2, 5], [9, 10]])

    ts.domain = [[-inf, 1], [2, 5], [9, 10]]
    assert ts.domain == Domain([[-inf, 1], [2, 5], [9, 10]])

    ts.domain = [[2, 5], [9, 10], [11, inf]]
    assert ts.domain == Domain([[2, 5], [9, 10], [11, inf]])

    ts.domain = [[-inf, 1], [2, 5], [9, 10], [11, inf]]
    assert ts.domain == Domain([[-inf, 1], [2, 5], [9, 10], [11, inf]])


def test_time_series():

    ts = TimeSeries(data=[(1, 2), (2, 3), (6, 1), (8, 4)])
    ts.domain = [1, 8.5]
    nose.tools.assert_raises(KeyError, ts.get, 0)
    assert ts[1.5] == 2
    assert ts[2.4] == 3
    assert ts[6] == 1
    assert ts[8.5] == 4
    nose.tools.assert_raises(KeyError, ts.get, 9)

    ts[5] = 7
    nose.tools.assert_raises(KeyError, ts.set, 9, 10)
    nose.tools.assert_raises(KeyError, ts.set, 0, 10)

    nose.tools.assert_raises(ValueError, TimeSeries,
                             data=[(1, 2), (2, 3), (6, 1), (8, 4)],
                             domain=[1.5, 7])


def test_ts_slice():
    ts = TimeSeries(data=[(1, 2), (2, 3), (6, 1), (8, 4)])

    new = ts.slice(1.5, 8.5)
    assert new.domain == Domain(1.5, 8.5)
    assert new._d == TimeSeries(data=[(1.5, 2), (2, 3), (6, 1), (8, 4)])._d

    new = ts.slice(1.5, 8.5, slice_domain=False)
    assert new.domain == Domain(-inf, inf)
    assert new._d == TimeSeries(data=[(1.5, 2), (2, 3), (6, 1), (8, 4)])._d

    ts.domain = [0, 8.5]
    nose.tools.assert_raises(ValueError, ts.slice, -1, -.5)
    nose.tools.assert_raises(ValueError, ts.slice, 8.8, 9)

    new = ts.slice(1.5, 8.5)
    assert new.domain == Domain(1.5, 8.5)
    assert new._d == TimeSeries(data=[(1.5, 2), (2, 3), (6, 1), (8, 4)])._d

    new = ts.slice(-1, 9)
    assert new.domain == Domain(0, 8.5)
    assert new._d == TimeSeries(data=[(1, 2), (2, 3), (6, 1), (8, 4)])._d

    args = [[0, 1.5], [2, 5], [5.5, 7], [8, 9]]
    ts.domain = args
    new = ts.slice(1.1, 6)
    assert new.domain == Domain([[1.1, 1.5], [2, 5], [5.5, 6]])
    assert new._d == TimeSeries(data=[(1.1, 2), (2, 3), (6, 1)])._d


def test_iterperiods():
    ts = TimeSeries(
        [[1, 2], [2, 3], [6, 1], [8, 4]],
        domain=Domain([1, 2], [3, 5], [6, 8])
    )

    answers = [
        (1, 2, 2),
        (3, 5, 3),
        (6, 8, 1)
    ]
    i = 0
    for t0, t1, value in ts.iterperiods():
        match = (t0, t1, value) == answers[i]
        assert match
        i += 1

    answers = [
        (1, 2, 2),
        (3, 5, 3),
        (6, 8, 1)
    ]
    i = 0
    for t0, t1, value in ts.iterperiods(0, 9):
        match = (t0, t1, value) == answers[i]
        assert match
        i += 1


def test_sample():
    # Check using int
    ts = TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]], domain=Domain(1, 9))
    assert dict(ts.sample(1)) == {
        i: ts[i] for i in range(1, 10)}
    assert dict(ts.sample(0.5)) == {
        1 + i / 2.: ts[1 + i / 2.] for i in range(0, 17)}

    ts = TimeSeries(
        [[1, 2], [2, 3], [6, 1], [8, 4]],
        domain=Domain([1, 2], [3, 5], [6, 8]),
    )
    nose.tools.assert_raises(NotImplementedError, ts.sample, 0.5)


def test_moving_average():

    ts = TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]], domain=Domain(1, 9))
    ts2 = TimeSeries(
        [[1, 2], [2, 3], [6, 1], [8, 4]],
        domain=Domain(1 - 1, 9 + 1),
    )
    assert dict(ts.moving_average(1, 2)) == {
        i: ts2.mean(i - 1, i + 1) for i in range(1, 10)}
    assert dict(ts.moving_average(0.5, 2)) == {
        1 + i / 2.: ts2.mean(1 + i / 2. - 1, 1 + i / 2. + 1) for i in range(0, 17)}

    ts = TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]], domain=Domain([1, 2], [3, 5], [6, 8]))
    nose.tools.assert_raises(NotImplementedError, ts.moving_average, 1, 0.5)


def test_mean():
    ts = TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]], domain=Domain(0, 9))
    assert ts.mean() == 22./9

    ts = TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]], domain=Domain([1, 2], [3, 5], [6, 8]))
    nose.tools.assert_raises(NotImplementedError, ts.mean)


def test_distribution():
    ts = TimeSeries([[1, 1], [2, 0], [6, 1], [8, 0]], domain=Domain([1, 2], [3, 5], [6, 8]))

    distribution = ts.distribution()
    assert distribution[0] == 2./5
    assert distribution[1] == 3./5

    distribution = ts.distribution(0, 9)
    assert distribution[0] == 2. / 5
    assert distribution[1] == 3. / 5
