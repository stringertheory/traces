import datetime
from past.builtins import long
from collections import Iterable


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
