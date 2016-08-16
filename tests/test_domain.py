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
        [],
        [-inf, 3],
        [1, inf],
        [1, 2],
        [(1, 2), (4, 5)],
        [datetime(2011, 1, 1, 1), datetime(2011, 1, 2, 1)],
        [[datetime(2011, 1, 1, 1), datetime(2011, 1, 2, 1)],
         [datetime(2011, 1, 1, 1), datetime(2011, 1, 2, 1)]]
    ]

    iterable_inputs_answers = [
        [],
        [FloatInterval([-inf, 3])],
        [FloatInterval([1, inf])],
        [FloatInterval([1, 2])],
        [FloatInterval([1, 2]), FloatInterval([4, 5])],
        [DateTimeInterval([datetime(2011, 1, 1, 1), datetime(2011, 1, 2, 1)])],
        [DateTimeInterval([datetime(2011, 1, 1, 1), datetime(2011, 1, 2, 1)])]
    ]

    bad_inputs = [
        ['a', 'b'],
        [1, datetime(2011, 1, 2, 1)],
        [[datetime(2011, 1, 1, 1), datetime(2011, 1, 2, 1)], [2, 3]]
    ]

    dom = Domain()
    assert dom._interval_list == []

    for inputs, answers in zip(iterable_inputs, iterable_inputs_answers):
        assert Domain(*inputs)._interval_list == answers

    for inputs in bad_inputs:
        nose.tools.assert_raises(TypeError, Domain, *inputs)


def test_contain():
    dom = Domain([1, 2], [4, inf])
    assert (0 in dom) == False
    assert (1 in dom) == True
    assert (1.5 in dom) == True
    assert (2 in dom) == True
    assert (3 in dom) == False
    assert (4 in dom) == True
    assert (100 in dom) == True


def test_sort_interval():
    interval_list = [FloatInterval([1, 2]), FloatInterval([4, 5])]
    interval_list_2 = [FloatInterval([1, 4]),
                       FloatInterval([1, 2]),
                       FloatInterval([6, 8]),
                       FloatInterval([9, 10]),
                       FloatInterval([4, 5])
                       ]
    interval_list_2_answer = [FloatInterval([1, 2]),
                       FloatInterval([1, 4]),
                       FloatInterval([4, 5]),
                       FloatInterval([6, 8]),
                       FloatInterval([9, 10])
                       ]
    dom = Domain((1, 2), (4, 5))
    assert dom.sort_intervals(interval_list) == interval_list
    assert dom.sort_intervals(interval_list_2) == interval_list_2_answer


def test_union_intervals():
    interval_list = [FloatInterval([1, 2]), FloatInterval([4, 5])]
    interval_list_2 = [FloatInterval([1, 4]),
                       FloatInterval([1, 2]),
                       FloatInterval([6, 8]),
                       FloatInterval([9, 10]),
                       FloatInterval([4, 5])
                       ]
    interval_list_2_answer = [FloatInterval([1, 5]),
                              FloatInterval([6, 8]),
                              FloatInterval([9, 10])
                              ]

    dom = Domain((1, 2), (4, 5))
    assert dom.union_intervals(interval_list) == interval_list
    assert dom.union_intervals(interval_list_2) == interval_list_2_answer


def test_intersection_intervals():
    dom = Domain((1, 2), (4, 5))

    assert dom.intersection_intervals([], []) == []

    interval_list = [FloatInterval([1, 2]), FloatInterval([4, 5])]
    interval_list_2 = [FloatInterval([1, 4]),
                       FloatInterval([1, 2]),
                       FloatInterval([6, 8]),
                       FloatInterval([9, 10]),
                       FloatInterval([4, 5])
                       ]
    interval_list_2_answer = [FloatInterval([1, 2]),
                              FloatInterval([4, 5])
                              ]

    assert dom.intersection_intervals(interval_list, interval_list_2) == interval_list_2_answer

    interval_list = [FloatInterval([1, 2]), FloatInterval([4, 10])]
    interval_list_2 = [FloatInterval([6, 8]),
                       FloatInterval([9, 10]),
                       FloatInterval([4, 5])
                       ]
    interval_list_2_answer = [FloatInterval([4, 5]),
                              FloatInterval([6, 8]),
                              FloatInterval([9, 10])
                              ]

    assert dom.intersection_intervals(interval_list, interval_list_2) == interval_list_2_answer
    assert dom.intersection_intervals(interval_list_2, interval_list) == interval_list_2_answer

    interval_list = [FloatInterval([1, 2]), FloatInterval([4, inf])]
    interval_list_2 = [FloatInterval([6, 8]),
                       FloatInterval([9, 10]),
                       FloatInterval([-inf, 5])
                       ]
    interval_list_2_answer = [FloatInterval([1, 2]),
                              FloatInterval([4, 5]),
                              FloatInterval([6, 8]),
                              FloatInterval([9, 10])
                              ]

    assert dom.intersection_intervals(interval_list, interval_list_2) == interval_list_2_answer
    assert dom.intersection_intervals(interval_list_2, interval_list) == interval_list_2_answer

    interval_list = [FloatInterval([1, 2])]
    interval_list_2 = [FloatInterval([6, 8]),
                       FloatInterval([9, 10]),
                       FloatInterval([4, 5])
                       ]
    interval_list_2_answer = []

    assert dom.intersection_intervals(interval_list, interval_list_2) == interval_list_2_answer
    assert dom.intersection_intervals(interval_list_2, interval_list) == interval_list_2_answer


def test_union():
    dom1 = Domain(1, 2)
    dom2 = Domain(3, 4)
    assert dom1.union(dom2)._interval_list == [
        FloatInterval([1, 2]),
        FloatInterval([3, 4])
    ]
    assert dom1._interval_list == [
        FloatInterval([1, 2])
    ]
    assert dom2._interval_list == [
        FloatInterval([3, 4])
    ]
    assert (dom1 | dom2)._interval_list == [
        FloatInterval([1, 2]),
        FloatInterval([3, 4])
    ]

    dom_list = [
        Domain(1, 2),
        Domain(3, 4),
        Domain(2, 5),
        Domain([1, 2], [9, 10])
    ]
    assert dom_list[0].union(*dom_list[1:])._interval_list == [
        FloatInterval([1, 5]),
        FloatInterval([9, 10])
    ]
    assert (dom_list[0] | dom_list[1] | dom_list[2] | dom_list[3])._interval_list == [
        FloatInterval([1, 5]),
        FloatInterval([9, 10])
    ]
    assert dom_list[0]._interval_list == [
        FloatInterval([1, 2])
    ]
    assert dom_list[1]._interval_list == [
        FloatInterval([3, 4])
    ]
    assert dom_list[2]._interval_list == [
        FloatInterval([2, 5])
    ]
    assert dom_list[3]._interval_list == [
        FloatInterval([1, 2]),
        FloatInterval([9, 10])
    ]


def test_intersection():
    dom1 = Domain(1, 2)
    dom2 = Domain(3, 4)
    assert dom1.intersection(dom2)._interval_list == []
    assert dom1._interval_list == [
        FloatInterval([1, 2])
    ]
    assert dom2._interval_list == [
        FloatInterval([3, 4])
    ]
    assert (dom1 & dom2)._interval_list == []

    dom_list = [
        Domain(1, 2),
        Domain(2, 5),
        Domain([1, 2], [9, 10])
    ]
    assert dom_list[0].intersection(*dom_list[1:])._interval_list == [
        FloatInterval([2, 2])
    ]
    assert (dom_list[1] & dom_list[2] & dom_list[0])._interval_list == [
        FloatInterval([2, 2])
    ]
    assert dom_list[0]._interval_list == [
        FloatInterval([1, 2])
    ]
    assert dom_list[1]._interval_list == [
        FloatInterval([2, 5])
    ]
    assert dom_list[2]._interval_list == [
        FloatInterval([1, 2]),
        FloatInterval([9, 10])
    ]


def test_start_end():
    dom = Domain([])
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


def test_slice():
    dom = Domain([-1, 2], [4, 5], [6, 10])
    assert dom.slice(-3, 12) == Domain([-1, 2], [4, 5], [6, 10])
    assert dom.slice(-1, 10) == Domain([-1, 2], [4, 5], [6, 10])
    assert dom.slice(1, 9) == Domain([1, 2], [4, 5], [6, 9])
    assert dom.slice(4.5, 9) == Domain([4.5, 5], [6, 9])

    nose.tools.assert_raises(ValueError, dom.slice, 12, 3)


def test_is_data_in_domain():
    ts = TimeSeries(domain=[0, 8])
    data1 = [(1, 2), (2, 3), (6, 1), (7, 4)]
    data2 = [(-1, 2), (1, 2), (2, 3)]
    data3 = [(1, 2), (2, 3), (6, 1), (9, 4)]

    assert ts.is_data_in_domain(data1) == True
    assert ts.is_data_in_domain(data2) == False
    assert ts.is_data_in_domain(data3) == False

    ts_domain = Domain([1, 7])
    assert ts.is_data_in_domain(data1, ts_domain) == True
    assert ts.is_data_in_domain(data2, ts_domain) == False
    assert ts.is_data_in_domain(data3, ts_domain) == False

    ts_domain = Domain(-inf, inf)
    assert ts.is_data_in_domain(data1, ts_domain) == True
    assert ts.is_data_in_domain(data2, ts_domain) == True
    assert ts.is_data_in_domain(data3, ts_domain) == True


def test_set_domain():

    ts = TimeSeries()
    assert ts.domain == Domain([-inf, inf])

    ts.set_domain(None)
    assert ts.domain == Domain([-inf, inf])

    ts.set_domain([-inf, 5])
    assert ts.domain == Domain([-inf, 5])

    ts.set_domain([5, inf])
    assert ts.domain == Domain([5, inf])

    ts.set_domain([-inf, inf])
    assert ts.domain == Domain([-inf, inf])

    ts.set_domain([2, 5])
    assert ts.domain == Domain([2, 5])

    ts.set_domain([[2, 5], [9, 10]])
    assert ts.domain == Domain([2, 5], [9, 10])

    ts = TimeSeries(data=[(1, 2), (2, 3), (6, 1), (8, 4)])
    nose.tools.assert_raises(ValueError, ts.set_domain, [1.5, 7])
    nose.tools.assert_raises(ValueError, ts.set_domain, [0, 7])
    nose.tools.assert_raises(ValueError, ts.set_domain, [1.5, 9])


def test_get_domain():
    ts = TimeSeries()
    assert ts.get_domain() == Domain([-inf, inf])

    ts.set_domain(None)
    assert ts.get_domain() == Domain([-inf, inf])

    ts.set_domain([-inf, 5])
    assert ts.get_domain() == Domain([-inf, 5])

    ts.set_domain([5, inf])
    assert ts.get_domain() == Domain([5, inf])

    ts.set_domain([-inf, inf])
    assert ts.get_domain() == Domain(-inf, inf)

    ts.set_domain([2, 5])
    assert ts.get_domain() == Domain([2, 5])

    ts.set_domain([[2, 5], [9, 10]])
    assert ts.get_domain() == Domain([[2, 5], [9, 10]])

    ts.set_domain([[-inf, 1], [2, 5], [9, 10]])
    assert ts.get_domain() == Domain([[-inf, 1], [2, 5], [9, 10]])

    ts.set_domain([[2, 5], [9, 10], [11, None]])
    assert ts.get_domain() == Domain([[2, 5], [9, 10], [11, None]])

    ts.set_domain([[None, 1], [2, 5], [9, 10], [11, None]])
    assert ts.get_domain() == Domain([[None, 1], [2, 5], [9, 10], [11, None]])


def test_time_series():

    ts = TimeSeries(data=[(1, 2), (2, 3), (6, 1), (8, 4)])
    ts.set_domain([1, 8.5])
    nose.tools.assert_raises(ValueError, ts.get, 0)
    assert ts[1.5] == 2
    assert ts[2.4] == 3
    assert ts[6] == 1
    assert ts[8.5] == 4
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


def test_regularize():
    # Check using int
    ts = TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]], domain=Domain(1, 9))
    assert ts.regularize(1) == {
        i: ts[i] for i in range(1, 10)}
    assert ts.regularize(0.5) == {
        1 + i / 2.: ts[1 + i / 2.] for i in range(0, 17)}

    ts = TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]])
    nose.tools.assert_raises(ValueError, ts.regularize, 0.5)


def test_moving_average():
    # Check using int
    ts = TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]], domain=Domain(1, 9))

    ts2 = TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]], domain=Domain(1 - 1, 9 + 1))
    assert ts.moving_average(2, 1) == {
        i: ts2.mean(i - 1, i + 1) for i in range(1, 10)}
    assert ts.moving_average(2, 0.5) == {
        1 + i / 2.: ts2.mean(1 + i / 2. - 1, 1 + i / 2. + 1) for i in range(0, 17)}

    ts = TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]])
    nose.tools.assert_raises(ValueError, ts.moving_average, 0.5, 1)


def test_mean():
    ts = TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]], domain=Domain(0, 9))
    assert ts.mean() == 22./9

    ts = TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]])
    nose.tools.assert_raises(ValueError, ts.mean)
