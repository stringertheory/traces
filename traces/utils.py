import datetime


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
