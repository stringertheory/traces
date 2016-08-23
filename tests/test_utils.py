from datetime import timedelta
from six import iteritems
import nose

import traces.utils as utils
from traces.domain import Domain, inf


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
        nose.tools.assert_raises(NotImplementedError, utils.duration_to_number, tdelta, 'hours')

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
