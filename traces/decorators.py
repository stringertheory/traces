from functools import wraps
from itertools import filterfalse


def _is_none(obj):
    return bool(obj is None)


def ignorant(func):
    @wraps(func)
    def wrapper(iterable, *args, **kwargs):
        filtered = filterfalse(_is_none, iterable)
        return func(filtered, *args, **kwargs)

    return wrapper


def strict(func):
    @wraps(func)
    def wrapper(iterable, *args, **kwargs):
        if None in iterable:
            return None
        else:
            return func(iterable, *args, **kwargs)

    return wrapper
