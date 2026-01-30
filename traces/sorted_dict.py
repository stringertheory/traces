"""Lightweight sorted dictionary using dict + sorted list + bisect.

This is a very lightweight alternative to sortedcontainers.SortedDict,
but is a little faster for read operations on TimeSeries.

"""

import bisect


class SortedDict:
    """A dictionary that maintains keys in sorted order.

    Uses a plain dict for O(1) key-value access and a sorted list of
    keys for ordered iteration and bisect operations.
    """

    def __init__(self, data=None):
        self._dict = {}
        self._keys = []
        if data is not None:
            self.update(data)

    def update(self, data):
        if isinstance(data, SortedDict):
            self._dict.update(data._dict)
        else:
            self._dict.update(data)
        self._keys = sorted(self._dict)

    def __setitem__(self, key, value):
        if key not in self._dict:
            bisect.insort(self._keys, key)
        self._dict[key] = value

    def __getitem__(self, key):
        return self._dict[key]

    def __delitem__(self, key):
        del self._dict[key]
        idx = bisect.bisect_left(self._keys, key)
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

    def bisect_left(self, key):
        return bisect.bisect_left(self._keys, key)

    def bisect_right(self, key):
        return bisect.bisect_right(self._keys, key)

    def islice(self, start=None, stop=None):
        """Iterate over keys from index start to stop."""
        return iter(self._keys[start:stop])

    def _range_indices(self, minimum, maximum, inclusive=(True, True)):
        """Return (lo, hi) slice indices for keys in the given range."""
        inc_min, inc_max = inclusive
        if inc_min:
            lo = bisect.bisect_left(self._keys, minimum)
        else:
            lo = bisect.bisect_right(self._keys, minimum)
        if inc_max:
            hi = bisect.bisect_right(self._keys, maximum)
        else:
            hi = bisect.bisect_left(self._keys, maximum)
        return lo, hi

    def delete_range(self, minimum, maximum, inclusive=(True, True)):
        """Delete all keys in the range [minimum, maximum].

        Uses a single list slice deletion instead of per-key deletion,
        avoiding O(n) list shifts for each key.

        Args:
            minimum: Lower bound.
            maximum: Upper bound.
            inclusive: Tuple of (include_min, include_max).
        """
        lo, hi = self._range_indices(minimum, maximum, inclusive)
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
        lo, hi = self._range_indices(minimum, maximum, inclusive)
        return self.islice(lo, hi)
