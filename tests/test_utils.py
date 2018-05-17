from datetime import timedelta, datetime, date
from six import iteritems
import nose
from infinity import inf

import traces.utils as utils


timedelta_list = [
    timedelta(hours=1),
    timedelta(minutes=2),
    timedelta(seconds=5),
    timedelta(milliseconds=5)
]

numeric_types = {
    int: [1, 2, 3, 0],
    float: [1.0, 2.0, 3.0, 0.0]
}

non_numeric_types = [
    [2], {'a': 4}, (2, 4), 'df', 'a'
]


def test_duration_to_number():
    for tdelta in timedelta_list:
        assert utils.duration_to_number(tdelta) == tdelta.total_seconds()
        nose.tools.assert_raises(
            NotImplementedError, utils.duration_to_number, tdelta, 'hours')

    for _type, item in iteritems(numeric_types):
        for num in item:
            assert utils.duration_to_number(num) == num

    for item in non_numeric_types:
        nose.tools.assert_raises(TypeError, utils.duration_to_number, item)


def test_convert_args_to_list():
    iterable_inputs = [
        [],
        [1, 2],
        [[1, 2]],
        [(1, 2)],
        [[(1, 2)]],
        [[[1, 2]]],
        [[[1, 2], [4, 5]]],
        [[(1, 2), (4, 5)]],
        [([1, 2], [4, 5])],
        [((1, 2), (4, 5))],
        [[[1, 2], [4, 5], [6, 7]]],
        [[(1, 2), (4, 5), (6, 7)]],
        [([1, 2], [4, 5], [6, 7])],
        [((1, 2), (4, 5), (6, 7))]
    ]

    iterable_inputs_answers = [
        [],
        [[1, 2]],
        [[1, 2]],
        [[1, 2]],
        [[1, 2]],
        [[1, 2]],
        [[1, 2], [4, 5]],
        [[1, 2], [4, 5]],
        [[1, 2], [4, 5]],
        [[1, 2], [4, 5]],
        [[1, 2], [4, 5], [6, 7]],
        [[1, 2], [4, 5], [6, 7]],
        [[1, 2], [4, 5], [6, 7]],
        [[1, 2], [4, 5], [6, 7]]
    ]

    for inputs, answers in zip(iterable_inputs, iterable_inputs_answers):
        assert utils.convert_args_to_list(inputs) == answers

    nose.tools.assert_raises(TypeError, utils.convert_args_to_list, [2, 3, 4])
    nose.tools.assert_raises(TypeError, utils.convert_args_to_list, [2])


def test_datetime_range():
    # test default options
    dt_range = list(utils.datetime_range(
        datetime(2016, 1, 1), datetime(2016, 2, 1), 'days'))
    assert dt_range[0] == datetime(2016, 1, 1)
    assert dt_range[-1] == datetime(2016, 1, 31)
    assert dt_range[10] == datetime(2016, 1, 11)

    # test non-default options
    dt_range = list(utils.datetime_range(
        datetime(2016, 1, 2),
        datetime(2016, 2, 1),
        'days', n_units=2, inclusive_end=True))
    assert dt_range[0] == datetime(2016, 1, 2)
    assert dt_range[-1] == datetime(2016, 2, 1)
    assert dt_range[10] == datetime(2016, 1, 22)

    # test units
    dt_range = list(utils.datetime_range(
        datetime(2016, 1, 1), datetime(2016, 2, 1), 'hours'))
    assert dt_range[1] - dt_range[0] == timedelta(hours=1)
    dt_range = list(utils.datetime_range(datetime(2016, 1, 1),
                                         datetime(2016, 2, 1), 'minutes', n_units=10))
    assert dt_range[1] - dt_range[0] == timedelta(minutes=10)

    # test end < start
    dt_range = list(utils.datetime_range(
        datetime(2016, 2, 1), datetime(2016, 1, 1), 'days'
    ))
    assert dt_range == []


def test_datetime_floor():
    # the date here is May 6th, 2016 (week 18)

    assert utils.datetime_floor(date(2016, 5, 6), 'years') == datetime(2016, 1, 1)
    assert utils.datetime_floor(inf) == inf
    assert utils.datetime_floor(
        datetime(2016, 5, 6, 11, 45, 6), 'months', n_units=3) == datetime(2016, 4, 1)
    assert utils.datetime_floor(
        datetime(2016, 5, 6, 11, 45, 6), 'weeks', n_units=3) == datetime(2016, 4, 18)
    assert utils.datetime_floor(datetime(
        2016, 5, 6, 11, 45, 6), 'hours', n_units=10) == datetime(2016, 5, 6, 10)
    assert utils.datetime_floor(datetime(
        2016, 5, 6, 11, 45, 6), 'minutes', n_units=15) == datetime(2016, 5, 6, 11, 45)
    assert utils.datetime_floor(datetime(
        2016, 5, 6, 11, 45, 6), 'seconds', n_units=30) == datetime(2016, 5, 6, 11, 45)

    nose.tools.assert_raises(
        ValueError, utils.datetime_floor, "2016-6-7"
    )

    nose.tools.assert_raises(
        ValueError, utils.datetime_floor,
        datetime(2016, 5, 6, 11, 45, 6), 'sleconds', n_units=3
    )

def test_weekday_number():
    assert utils.weekday_number(5) == 5
    nose.tools.assert_raises(ValueError, utils.weekday_number, 7)
    print(utils.weekday_number("Tuesday"))
    assert utils.weekday_number("Tuesday") == 1
    nose.tools.assert_raises(ValueError, utils.weekday_number, 'Mooday')
