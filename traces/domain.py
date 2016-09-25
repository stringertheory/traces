import datetime
from infinity import inf
from collections import Iterable

import intervals
import sortedcontainers

from . import utils
from .base import Booga


class Domain(object):
    """Initialize with:

    >>> Domain(1, 4)
    >>> Domain([1, 4])
    >>> Domain((1, 4))
    >>> Domain([[1, 4]])
    >>> Domain([(1, 4)])
    >>> Domain((1, 4), (5, 8))
    >>> Domain([1, 4], [5, 8])
    >>> Domain([(1, 4), (5, 8)])
    >>> Domain([[1, 4], [5, 8]])

    Domain has to be closed intervals. It can be open toward -inf or
    inf.  For example, Domain(-inf, 3) means a domain from -inf to 3
    inclusive.

    """
    @staticmethod
    def _is_empty(args):
        if len(args) == 0:
            return [(-inf, inf)]

    @staticmethod
    def _is_none(args):
        if len(args) == 1 and args[0] is None:
            return [(-inf, inf)]

    @staticmethod
    def _is_empty_list(args):
        if len(args) == 1 and args[0] == []:
            return []

    @staticmethod
    def _hashable(value):
        try:
            hash(value)
        except TypeError:
            return None
        else:
            return True

    @staticmethod
    def _iterable(value):
        try:
            iter(value)
        except TypeError:
            return None
        else:
            return True

    def _valid(self, value):
        return self._hashable(value) and not self._iterable(value)

    def _is_pair(self, args):
        try:
            length = len(args)
        except TypeError:
            return None
        else:
            if length == 2:
                start, end = args
                if self._valid(start) and self._valid(end):
                    return (start, end)

    def _is_single_pair(self, args):
        pair = self._is_pair(args)
        if pair:
            return [pair]

    def _is_unpacked_pair_list(self, args):
        pair_list = [self._is_pair(arg) for arg in args]
        if all(pair_list):
            return pair_list

    def _is_pair_list(self, args):
        if len(args) == 1 and isinstance(args[0], (list, tuple)):
            return self._is_unpacked_pair_list(args[0])

    def __init__(self, *args):

        validation_function_list = [
            self._is_empty,
            self._is_none,
            self._is_empty_list,
            self._is_single_pair,
            self._is_unpacked_pair_list,
            self._is_pair_list,
        ]
        for function in validation_function_list:
            interval_list = function(args)
            if interval_list is not None:
                break

        if not interval_list and not self._is_empty_list(args) == []:
            msg = (
                'invalid arguments to Domain {}. Must be one of:\n'
                ' - empty or None, e.g. Domain() or Domain(None)'
                ' - a start and end, e.g. Domain(1, 2)\n'
                ' - a (start, end) pair, e.g. Domain([1, 2])\n'
                ' - multiple (start, end) pairs, e.g.'
                ' e.g. Domain([1, 2], [3, 4])\n'
                ' - a list of (start, end) pairs,'
                ' e.g. Domain([(1, 2), (3, 4)])'
            ).format(str(args))
            raise ValueError(msg)

        for start, end in interval_list:
            try:
                bad_order = (start >= end)
            except TypeError as error:
                raise ValueError(error)
            else:
                if bad_order:
                    msg = (
                        "start of interval can't be greater or equal "
                        "to end ({} >= {})"
                    ).format(start, end)
                    raise ValueError(msg)

        try:
            sorted(interval_list)
        except TypeError:
            msg = "Can't mix types"
            raise ValueError(msg)

        self._start = inf
        self._end = -inf
        ts_list = []
        for start, end in interval_list:
            ts = Booga()
            ts[-inf] = False
            ts[start] = True
            ts[end] = False
            ts_list.append(ts)
            if start < self._start:
                self._start = start
            if end > self._end:
                self._end = end

        if ts_list:
            self.ts = Booga.merge(ts_list, operation=any)
        else:
            self.ts = Booga()
            self.ts[-inf] = False

    def start(self):
        return self._start

    def end(self):
        return self._end

    @property
    def lower(self):
        return self._start

    @property
    def upper(self):
        return self._end

    def intervals(self):
        for t0, t1, value in self.ts.iterperiods(value=True):
            yield t0, t1

    @property
    def _interval_list(self):
        return list(self.intervals())

    def get_interval(self, value):

        # value is on the boundary of an interval
        if value in self.ts:
            is_left_value = self.ts[value]
            if is_left_value:
                left_index = self.ts._d.index(value)
                right_index = left_index + 1
            else:
                right_index = self.ts._d.index(value)
                left_index = right_index - 1
            return self.ts._d.iloc[left_index], self.ts._d.iloc[right_index]

        # value is inside of an interval
        elif self.ts[value]:
            right_index = self.ts._d.bisect_right(value)
            left_index = right_index - 1
            return self.ts._d.iloc[left_index], self.ts._d.iloc[right_index]

        # value is not in an interval
        else:
            raise KeyError(value)

    def n_intervals(self):
        return len(list(self.intervals()))

    def __contains__(self, value):
        if value in self.ts:
            return True
        else:
            return self.ts[value]

    def __repr__(self):
        output = '\n'.join('{}'.format(i) for i in self.intervals())
        return '<Domain>\n{}\n</Domain>'.format(output)

    def union(self, *others):
        """Union of a list of Domains.  Return the Domain that is the union of
        all Domains.

        """
        ts_list = [self.ts]
        ts_list.extend([d.ts for d in others])
        on = Booga.merge(ts_list, operation=any)
        return Domain([(t0, t1) for (t0, t1, v) in on.iterperiods(value=True)])

    def intersection(self, *others):
        """Union of a list of Domains.  Return the Domain that is the union of
        all Domains.

        """
        ts_list = [self.ts]
        ts_list.extend([d.ts for d in others])
        on = Booga.merge(ts_list, operation=all)
        return Domain([(t0, t1) for (t0, t1, v) in on.iterperiods(value=True)])

    def slice(self, start, end):
        """Return a segment of Domain within start and end"""

        if end <= start:
            message = (
                "Can't slice a Domain when end <= start. "
                "Received start={} and end={}."
            ).format(start, end)
            raise ValueError(message)

        if start > self.end():
            msg = "Start time is larger than the end of the Domain."
            raise ValueError(msg)

        if end < self.start():
            msg = "End time is smaller than the start of the Domain."
            raise ValueError(msg)

        intervals = []
        for t0, t1, value in self.ts.iterperiods(
                start=start,
                end=end,
                value=True,
        ):
            intervals.append((t0, t1))

        return Domain(intervals)

    def __eq__(self, other):
        return list(self.intervals()) == list(other.intervals())

    def __ne__(self, other):
        return not(self == other)

    def __or__(self, other):
        """Allow a | b syntax"""
        return self.union(other)

    def __and__(self, other):
        """Allow a & b syntax"""
        return self.intersection(other)
