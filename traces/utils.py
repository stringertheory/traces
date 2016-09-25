import datetime
from past.builtins import long
from collections import Iterable
from infinity import inf


def duration_to_number(duration, units='seconds'):
    """If duration is already a numeric type, then just return
    duration. If duration is a timedelta, return a duration in
    seconds.

    TODO: allow for multiple types of units.

    """
    if isinstance(duration, (int, float, long)):
        return duration
    elif isinstance(duration, (datetime.timedelta,)):
        if units == 'seconds':
            return duration.total_seconds()
        else:
            msg = 'unit "%s" is not supported' % units
            raise NotImplementedError(msg)
    elif duration == inf or duration == -inf:
        msg = "Can't convert infinite duration to number"
        raise ValueError(msg)
    else:
        msg = 'duration is an unknown type (%s)' % duration
        raise TypeError(msg)


def convert_args_to_list(args):
    """Convert all iterable pairs of inputs into a list of list"""
    list_of_pairs = []
    if len(args) == 0:
        return []

    if any(isinstance(arg, (list, tuple)) for arg in args):
        # Domain([[1, 4]])
        # Domain([(1, 4)])
        # Domain([(1, 4), (5, 8)])
        # Domain([[1, 4], [5, 8]])
        if len(args) == 1 and \
                any(isinstance(arg, (list, tuple)) for arg in args[0]):
            for item in args[0]:
                list_of_pairs.append(list(item))
        else:
            # Domain([1, 4])
            # Domain((1, 4))
            # Domain((1, 4), (5, 8))
            # Domain([1, 4], [5, 8])
            for item in args:
                list_of_pairs.append(list(item))
    else:
        # Domain(1, 2)
        if len(args) == 2:
            list_of_pairs.append(list(args))
        else:
            msg = "The argument type is invalid. ".format(args)
            raise TypeError(msg)

    return list_of_pairs


def datetime_range(start_dt, end_dt, unit,
                   unit_increment=1, inclusive_end=False):
    """A range of datetimes/dates."""

    def done(a, b, inclusive_end):
        if inclusive_end:
            return a <= b
        else:
            return a < b

    current = start_dt
    while done(current, end_dt, inclusive_end):
        yield current
        current += datetime.timedelta(**{unit: unit_increment})


def datetime_floor(value):
    if isinstance(value, datetime.datetime):
        return datetime.datetime.combine(value.date(), datetime.time())
    elif isinstance(value, datetime.date):
        return datetime.datetime.combine(value, datetime.time())
    else:
        msg = 'must be date or datetime, got {}'.format(value)
        raise ValueError(msg)

WEEKDAY_LOOKUP = {
    'monday': 0,
    'tuesday': 1,
    'wednesday': 2,
    'thursday': 3,
    'friday': 4,
    'saturday': 5,
    'sunday': 6,
}


def weekday_number(value):

    if isinstance(value, int):
        if 0 <= value < 7:
            return value
        else:
            msg = 'must be value from 0-6'
            raise ValueError(msg)

    elif isinstance(value, str):
        result = WEEKDAY_NUMBER.get(value.lower())
        if result is None:
            msg = 'must be a valid weekday, got {}'.format(value)
            raise ValueError(msg)
