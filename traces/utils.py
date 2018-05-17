import datetime
from past.builtins import long
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
                   n_units=1, inclusive_end=False):
    """A range of datetimes/dates."""

    def done(a, b, inclusive_end):
        if inclusive_end:
            return a <= b
        else:
            return a < b

    current = start_dt
    while done(current, end_dt, inclusive_end):
        yield current
        current += datetime.timedelta(**{unit: n_units})


def floor_datetime(dt, unit, n_units=1):
    """Floor a datetime to nearest n units. For example, if we want to
    floor to nearest three months, starting with 2016-05-06-yadda, it
    will go to 2016-04-01. Or, if starting with 2016-05-06-11:45:06
    and rounding to nearest fifteen minutes, it will result in
    2016-05-06-11:45:00.
    """
    if unit == 'years':
        new_year = dt.year - (dt.year - 1) % n_units
        return datetime.datetime(new_year, 1, 1, 0, 0, 0)
    elif unit == 'months':
        new_month = dt.month - (dt.month - 1) % n_units
        return datetime.datetime(dt.year, new_month, 1, 0, 0, 0)
    elif unit == 'weeks':
        _, isoweek, _ = dt.isocalendar()
        new_week = isoweek - (isoweek - 1) % n_units
        return datetime.datetime.strptime(
            "%d %02d 1" % (dt.year, new_week), "%Y %W %w")
    elif unit == 'days':
        new_day = dt.day - dt.day % n_units
        return datetime.datetime(dt.year, dt.month, new_day, 0, 0, 0)
    elif unit == 'hours':
        new_hour = dt.hour - dt.hour % n_units
        return datetime.datetime(dt.year, dt.month, dt.day, new_hour, 0, 0)
    elif unit == 'minutes':
        new_minute = dt.minute - dt.minute % n_units
        return datetime.datetime(dt.year, dt.month, dt.day,
                                 dt.hour, new_minute, 0)
    elif unit == 'seconds':
        new_second = dt.second - dt.second % n_units
        return datetime.datetime(dt.year, dt.month, dt.day,
                                 dt.hour, dt.minute, new_second)
    else:
        msg = 'Unknown unit type {}'.format(unit)
        raise ValueError(msg)


def datetime_floor(value, unit='days', n_units=1):

    # if it's a date, convert to datetime at start of day
    if type(value) is datetime.date:
        value = datetime.datetime.combine(value, datetime.time())

    if isinstance(value, datetime.datetime):
        return floor_datetime(value, unit, n_units)
    elif value == -inf:
        return -inf
    elif value == inf:
        return inf
    else:
        msg = 'must be date, datetime, or inf; got {}'.format(value)
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

    else:
        result = WEEKDAY_LOOKUP.get(value)
        if result:
            return result
        else:
            try:
                result = WEEKDAY_LOOKUP.get(value.lower())
            except TypeError:
                pass
            if result:
                return result
            msg = 'must be a valid weekday, got {}'.format(value)
            raise ValueError(msg)
