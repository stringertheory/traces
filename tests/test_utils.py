from datetime import timedelta
import traces.utils as utils
from six import iteritems
import nose


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

