import datetime
import nose
import traces
import pandas as pd
from sortedcontainers import SortedDict
from future.utils import listitems, iteritems

key_list = [
    datetime.datetime(2012, 1, 7),
    datetime.datetime(2012, 2, 13),
    datetime.datetime(2012, 3, 20),
    datetime.datetime(2012, 4, 10),
]
numeric_types = {
    int: [1, 2, 3, 0],
    float: [1.0, 2.0, 3.0, 0.0],
    bool: [True, False, True, False]
}
non_numeric_hashable_types = {
    str: ['a', 'b', 'c', ''],
    tuple: [('a', 1), ('b', 2), ('c', 3), ()],
}
unhashable_types = {
    list: [[1, 1], [2, 2], [3, 3], []],
    dict: [{'a': 1}, {'b': 2}, {'c': 3}, {}],
    set: [{1}, {1, 2}, {1, 2, 3}, set()],
}
all_types = dict(
    listitems(numeric_types) +
    listitems(non_numeric_hashable_types) +
    listitems(unhashable_types)
)


def _make_ts(type_, key_list, value_list):
    ts = traces.TimeSeries()
    for t, v in zip(key_list, value_list):
        ts[t] = v
    return ts


def frange(x, y, jump):
    while x < y:
        yield x
        x += jump


def test_mean():

    # numeric hashable types should work
    for type_, value_list in iteritems(numeric_types):
        ts = _make_ts(type_, key_list, value_list)
        ts.distribution(key_list[0], key_list[-1])
        ts.mean(key_list[0], key_list[-1])

    # non-numeric hashable types should raise type error on mean, but
    # distribution should work
    for type_, value_list in iteritems(non_numeric_hashable_types):
        ts = _make_ts(type_, key_list, value_list)
        ts.distribution(key_list[0], key_list[-1])
        nose.tools.assert_raises(TypeError, ts.mean, key_list[0], key_list[1])

    # non-numeric unhashable types should raise error on distribution
    # and mean
    for type_, value_list in iteritems(unhashable_types):
        ts = _make_ts(type_, key_list, value_list)
        nose.tools.assert_raises(TypeError, ts.distribution,
                                 key_list[0], key_list[1])
        nose.tools.assert_raises(TypeError, ts.mean,
                                 key_list[0], key_list[1])


def test_sample():
    time_list = [
        datetime.datetime(2016, 1, 1, 1, 1, 2),
        datetime.datetime(2016, 1, 1, 1, 1, 3),
        datetime.datetime(2016, 1, 1, 1, 1, 8),
        datetime.datetime(2016, 1, 1, 1, 1, 10)
    ]
    ts = _make_ts(int, time_list, [1, 2, 3, 0])

    def curr_time(i):
        return datetime.datetime(2016, 1, 1, 1, 1, i)

    # Check first arguments
    assert dict(ts.sample(1, time_list[0], time_list[-1])) == {
        curr_time(i): ts[curr_time(i)] for i in range(2, 11)}

    assert dict(ts.sample(2, time_list[0], time_list[-1])) == {
        curr_time(i): ts[curr_time(i)] for i in range(2, 11, 2)}

    nose.tools.assert_raises(
        ValueError, ts.sample, -1, time_list[0], time_list[-1])
    nose.tools.assert_raises(ValueError, ts.sample,
                             20, time_list[0], time_list[-1])

    # Check second and third arguments
    nose.tools.assert_raises(ValueError, ts.sample,
                             1, time_list[3], time_list[0])

    assert dict(ts.sample(1, curr_time(5), curr_time(10))) == {
        curr_time(i): ts[curr_time(i)] for i in range(5, 11)}

    assert dict(ts.sample(1, curr_time(2), curr_time(5))) == {
        curr_time(i): ts[curr_time(i)] for i in range(2, 6)}

    assert dict(ts.sample(1, curr_time(0), curr_time(13))) == {
        curr_time(i): ts[curr_time(i)] for i in range(0, 14)}

    # Check using int
    ts = traces.TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]])
    assert dict(ts.sample(1, 1, 8)) == {
        i: ts[i] for i in range(1, 9)}
    assert dict(ts.sample(0.5, 1, 8)) == {
        1 + i / 2.: ts[1 + i / 2.] for i in range(0, 15)}
    nose.tools.assert_raises(ValueError, ts.sample, 0.5, -traces.inf, 8)
    nose.tools.assert_raises(ValueError, ts.sample, 0.5, 1, traces.inf)

    # Test pandas compatibility
    pd_ts = pd.Series(dict(ts.sample(1, 1, 8)))
    assert all(pd_ts.index[i - 1] == i for i in range(1, 9))
    assert all(pd_ts.values[i - 1] == ts[i] for i in range(1, 9))


def test_moving_average():
    time_list = [
        datetime.datetime(2016, 1, 1, 1, 1, 2),
        datetime.datetime(2016, 1, 1, 1, 1, 3),
        datetime.datetime(2016, 1, 1, 1, 1, 8),
        datetime.datetime(2016, 1, 1, 1, 1, 10)
    ]
    ts = _make_ts(int, time_list, [1, 2, 3, 0])

    def curr_time(i):
        return datetime.datetime(2016, 1, 1, 1, 1, i)

    # Check first arguments
    assert dict(ts.moving_average(1, 2, time_list[0], time_list[-1])) == {
        curr_time(i):
        ts.mean(curr_time(i) - datetime.timedelta(seconds=1),
                curr_time(i) + datetime.timedelta(seconds=1)) for i in range(2, 11)}

    assert dict(ts.moving_average(1, 0.2, time_list[0], time_list[-1])) == {
        curr_time(i):
        ts.mean(curr_time(i) - datetime.timedelta(seconds=.1),
                curr_time(i) + datetime.timedelta(seconds=.1)) for i in range(2, 11)}

    nose.tools.assert_raises(
        ValueError, ts.moving_average, 1, -1, time_list[0], time_list[-1])

    # Check second arguments
    assert dict(ts.moving_average(2, 1, time_list[0], time_list[-1])) == {
        curr_time(i):
        ts.mean(curr_time(i) - datetime.timedelta(seconds=.5),
                curr_time(i) + datetime.timedelta(seconds=.5)) for i in range(2, 11, 2)}

    nose.tools.assert_raises(
        ValueError, ts.moving_average, -1, 1, time_list[0], time_list[-1])
    nose.tools.assert_raises(
        ValueError, ts.moving_average, 20, 1, time_list[0], time_list[-1])

    # Check third and fourth arguments
    nose.tools.assert_raises(
        ValueError, ts.moving_average, 1, 1, time_list[3], time_list[0])

    assert dict(ts.moving_average(1, 2, curr_time(5), curr_time(10))) == {
        curr_time(i):
        ts.mean(curr_time(i) - datetime.timedelta(seconds=1),
                curr_time(i) + datetime.timedelta(seconds=1)) for i in range(5, 11)}

    assert dict(ts.moving_average(1, 2, curr_time(2), curr_time(5))) == {
        curr_time(i):
        ts.mean(curr_time(i) - datetime.timedelta(seconds=1),
                curr_time(i) + datetime.timedelta(seconds=1)) for i in range(2, 6)}

    assert dict(ts.moving_average(1, 2, curr_time(0), curr_time(13))) == {
        curr_time(i):
        ts.mean(curr_time(i) - datetime.timedelta(seconds=1),
                curr_time(i) + datetime.timedelta(seconds=1)) for i in range(0, 14)}

    # Check using int
    ts = traces.TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]])
    assert dict(ts.moving_average(1, 2, 1, 8)) == {
        i: ts.mean(i - 1, i + 1) for i in range(1, 9)}
    assert dict(ts.moving_average(0.5, 2, 1, 8)) == {
        1 + i / 2.: ts.mean(1 + i / 2. - 1, 1 + i / 2. + 1) for i in range(0, 15)}

    # Test pandas compatibility
    pd_ts = pd.Series(dict(ts.moving_average(1, 2, 1, 8)))
    assert all(pd_ts.index[i - 1] == i for i in range(1, 9))
    assert all(pd_ts.values[i - 1] == ts.mean(i - 1, i + 1)
               for i in range(1, 9))


def test_to_bool():

    answer = {}
    for type_, value_list in iteritems(all_types):
        answer[type_] = [True if i else False for i in value_list]

    # numeric hashable types should work
    for type_, value_list in iteritems(all_types):
        ts = _make_ts(type_, key_list, value_list)
        result = ts.to_bool()
        values = [v for (k, v) in result.items()]
        assert answer[type_] == values
