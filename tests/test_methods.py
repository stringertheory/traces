import datetime
import nose
import traces
from future.utils import listitems, iteritems


def _make_ts(type_, key_list, value_list):
    ts = traces.TimeSeries(default_type=type_)
    for t, v in zip(key_list, value_list):
        ts[t] = v
    return ts

key_list = [
    datetime.datetime(2012, 1, 7),
    datetime.datetime(2012, 2, 13),
    datetime.datetime(2012, 3, 20),
    datetime.datetime(2012, 4, 10),
]
numeric_types = {
    int: [1, 2, 3, 0],
    float: [1.0, 2.0, 3.0, 0.0],
    bool: [True, False, True, False],
    # complex: [complex(1, 0), complex(1, 1), complex(0, 1)],
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
all_types = dict(listitems(numeric_types)+
                 listitems(non_numeric_hashable_types) + listitems(unhashable_types))


def test_mean():

    # numberic hashable types should work
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


def test_to_bool():

    answer = {}
    for type_, value_list in iteritems(all_types):
        answer[type_] = [True if i else False for i in value_list]

    # numberic hashable types should work
    for type_, value_list in iteritems(all_types):
        ts = _make_ts(type_, key_list, value_list)
        result = ts.to_bool()
        values = [v for (k, v) in result.items()]
        assert answer[type_] == values
