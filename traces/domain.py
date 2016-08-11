import datetime
from infinity import inf
from collections import Iterable

# Third party
import intervals

# Local
from .utils import convert_args_to_list

# Define infinity for traces
inf = inf


class Domain(object):
    """
    initialize with:
    Domain(1, 4)
    Domain([1, 4])
    Domain((1, 4))
    Domain([[1, 4]])
    Domain([(1, 4)])

    Domain((1, 4), (5, 8))
    Domain([1, 4], [5, 8])
    Domain([(1, 4), (5, 8)])
    Domain([[1, 4], [5, 8]])
    ...

    Domain has to be closed intervals. It can be open toward -inf or inf.
    For example,  Domain(-inf, 3) means a domain from -inf to 3 inclusive.

    """
    def __init__(self, *args):
        self._interval_list = []

        if len(args) is not 0:
            list_of_pairs = convert_args_to_list(args)
            first_item = list_of_pairs[0][0]

            if isinstance(first_item, datetime.datetime):
                for start, end in list_of_pairs:
                    if isinstance(start, datetime.datetime) and \
                            isinstance(end, datetime.datetime):
                        self._interval_list.append(intervals.DateTimeInterval([start, end]))
                    else:
                        msg = "Can't create a Domain with mixed types."
                        raise TypeError(msg)
            elif isinstance(first_item, (int, float)):
                for start, end in list_of_pairs:
                    if isinstance(start, (int, float)) and \
                            isinstance(end, (int, float)):
                        self._interval_list.append(intervals.FloatInterval([start, end]))
                    else:
                        msg = "Can't create a Domain with mixed types."
                        raise TypeError(msg)
            else:
                msg = "Can't create a Domain that is {}.".format(type(first_item))
                raise TypeError(msg)

    def __repr__(self):
        return '<Domain>\n{}\n</Domain>'.format(self._interval_list)

    @staticmethod
    def sort_intervals(interval_list):
        """Sort intervals"""
        return sorted(interval_list, key=lambda interval: (interval.lower, interval.upper))

    @staticmethod
    def union_intervals(interval_list):
        """Union a list of intervals"""
        if len(interval_list) == 0:
            return interval_list

        new_interval_list = []
        sorted_interval_list = Domain.sort_intervals(interval_list)
        curr = sorted_interval_list[0]
        for interval in sorted_interval_list:
            if curr.is_connected(interval):
                curr = curr | interval
            else:
                new_interval_list.append(curr)
                curr = interval
        new_interval_list.append(curr)

        return new_interval_list

    def union(self, *other):
        """Union of a list of Domains.
        Also, return the Domain that is the union of all Domains."""
        result = self
        for dom in other:
            result = Domain.union_intervals(result._interval_list + dom._interval_list)

        return result

    def intersection(self, other):
        pass

    def __contains__(self, item):
        pass

    def __or__(self, other):
        """Allow a | b syntax"""
        return self.union(other)
