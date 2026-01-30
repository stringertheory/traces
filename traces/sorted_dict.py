"""Lightweight sorted dictionary using dict + sorted list + bisect.

This provides the subset of the sortedcontainers.SortedDict API used by
TimeSeries and Histogram, without the external dependency.
"""

import bisect


class SortedDict:
    """A dictionary that maintains keys in sorted order.

    Uses a plain dict for O(1) key/value access and a sorted list of
    keys for ordered iteration and bisect operations.

    Args:
        key: Optional key function for sorting (e.g. hash for
            unorderable elements). Mirrors sortedcontainers API.
        data: Optional initial data (dict, iterable of pairs, or
            another SortedDict).
    """

    def __init__(self, *args):
        # Match sortedcontainers.SortedDict constructor:
        # SortedDict() -> empty
        # SortedDict(data) -> from dict or iterable of pairs
        # SortedDict(key_func) -> empty with key function
        # SortedDict(key_func, data) -> from data with key function
        self._key = None
        self._dict = {}
        self._keys = []
        data = None
        for arg in args:
            if callable(arg):
                self._key = arg
            else:
                data = arg
        if data is not None:
            self.update(data)

    def _sort_keys(self):
        if self._key is not None:
            self._keys = sorted(self._dict, key=self._key)
        else:
            self._keys = sorted(self._dict)

    def _insort(self, key):
        if self._key is not None:
            bisect.insort_left(self._keys, key, key=self._key)
        else:
            bisect.insort(self._keys, key)

    def _bisect_left(self, key):
        if self._key is not None:
            return bisect.bisect_left(self._keys, self._key(key), key=self._key)
        return bisect.bisect_left(self._keys, key)

    def _bisect_right(self, key):
        if self._key is not None:
            return bisect.bisect_right(
                self._keys, self._key(key), key=self._key
            )
        return bisect.bisect_right(self._keys, key)

    def update(self, data):
        if isinstance(data, dict):
            self._dict.update(data)
        elif isinstance(data, SortedDict):
            self._dict.update(data._dict)
        else:
            for k, v in data:
                self._dict[k] = v
        self._sort_keys()

    # -- dict-like access ---------------------------------------------------

    def __setitem__(self, key, value):
        if key not in self._dict:
            self._insort(key)
        self._dict[key] = value

    def __getitem__(self, key):
        return self._dict[key]

    def __delitem__(self, key):
        del self._dict[key]
        idx = self._bisect_left(key)
        self._keys.pop(idx)

    def __contains__(self, key):
        return key in self._dict

    def __len__(self):
        return len(self._dict)

    def __bool__(self):
        return bool(self._dict)

    def __iter__(self):
        return iter(self._keys)

    def __eq__(self, other):
        if isinstance(other, SortedDict):
            return self._dict == other._dict
        return NotImplemented

    def __repr__(self):
        items = ", ".join(f"{k!r}: {v!r}" for k, v in self.items())
        return f"SortedDict({{{items}}})"

    # -- ordered access -----------------------------------------------------

    def keys(self):
        """Return the sorted keys list (supports indexing)."""
        return self._keys

    def values(self):
        return [self._dict[k] for k in self._keys]

    def items(self):
        """Return a list of (key, value) pairs in sorted order.

        The returned list supports slicing (e.g. items()[:10]).
        """
        return [(k, self._dict[k]) for k in self._keys]

    def peekitem(self, index=-1):
        """Return the (key, value) pair at the given index."""
        k = self._keys[index]
        return (k, self._dict[k])

    # -- bisect operations --------------------------------------------------

    def bisect_left(self, key):
        return self._bisect_left(key)

    def bisect_right(self, key):
        return self._bisect_right(key)

    # -- iteration helpers --------------------------------------------------

    def islice(self, start=None, stop=None):
        """Iterate over keys from index start to stop."""
        return iter(self._keys[start:stop])

    def delete_range(self, minimum, maximum, inclusive=(True, True)):
        """Delete all keys in the range [minimum, maximum].

        Uses a single list slice deletion instead of per-key deletion,
        avoiding O(n) list shifts for each key.

        Args:
            minimum: Lower bound.
            maximum: Upper bound.
            inclusive: Tuple of (include_min, include_max).
        """
        inc_min, inc_max = inclusive
        if inc_min:
            lo = self._bisect_left(minimum)
        else:
            lo = self._bisect_right(minimum)
        if inc_max:
            hi = self._bisect_right(maximum)
        else:
            hi = self._bisect_left(maximum)
        for k in self._keys[lo:hi]:
            del self._dict[k]
        del self._keys[lo:hi]

    def irange(self, minimum, maximum, inclusive=(True, True)):
        """Iterate over keys in the range [minimum, maximum].

        Args:
            minimum: Lower bound.
            maximum: Upper bound.
            inclusive: Tuple of (include_min, include_max).
        """
        inc_min, inc_max = inclusive
        if inc_min:
            lo = self._bisect_left(minimum)
        else:
            lo = self._bisect_right(minimum)
        if inc_max:
            hi = self._bisect_right(maximum)
        else:
            hi = self._bisect_left(maximum)
        return iter(self._keys[lo:hi])
