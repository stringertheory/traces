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

        # TODO: get domain intervals in a list
        temp_interval_list = []

        if len(args) is not 0:
            if args[0] is None:
                temp_interval_list.append(intervals.FloatInterval(None))

            else:
                list_of_pairs = convert_args_to_list(args)

                if list_of_pairs[0] == [-inf, inf]:
                    temp_interval_list.append(intervals.FloatInterval([-inf, inf]))

                else:
                    first_item = list_of_pairs[0]
                    if any(isinstance(item, datetime.datetime) for item in first_item):
                        data_type = datetime.datetime
                    elif any(isinstance(item,  (int, float)) for item in first_item):
                        data_type = float
                    else:
                        msg = "Can't create a Domain with {}.".format(type(first_item))
                        raise TypeError(msg)

                    if data_type == datetime.datetime:
                        for start, end in list_of_pairs:
                            if (isinstance(start, (datetime.datetime)) or start == -inf or start is None) and \
                                    (isinstance(end, (datetime.datetime, inf)) or end == inf or end is None):
                                temp_interval_list.append(intervals.DateTimeInterval([start, end]))
                            else:
                                msg = "Can't create a Domain with mixed types."
                                raise TypeError(msg)
                    elif data_type == float:
                        for start, end in list_of_pairs:
                            if (isinstance(start, (int, float)) or start == -inf or start is None) and \
                                    (isinstance(end, (int, float)) or end == inf or end is None):
                                temp_interval_list.append(intervals.FloatInterval([start, end]))
                            else:
                                msg = "Can't create a Domain with mixed types."
                                raise TypeError(msg)

        self._interval_list = self.union_intervals(temp_interval_list)

    def __repr__(self):
        output = '\n'.join('{}'.format([interval.lower, interval.upper]) for interval in self._interval_list)
        return '<Domain>\n{}\n</Domain>'.format(output)

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

    @staticmethod
    def intersection_intervals(interval_list1, interval_list2):
        """Intersection of two lists of intervals"""
        if len(interval_list1) == 0 or len(interval_list2) == 0:
            return []

        new_interval_list = []
        sorted_interval_list1 = Domain.union_intervals(interval_list1)
        sorted_interval_list2 = Domain.union_intervals(interval_list2)

        first1 = sorted_interval_list1[0]
        first2 = sorted_interval_list2[0]

        if first1.lower <= first2.lower:
            curr = sorted_interval_list1
            other = sorted_interval_list2
        else:
            curr = sorted_interval_list2
            other = sorted_interval_list1

        curr_node = curr.pop(0)
        other_node = other.pop(0)

        while True:
            if curr_node.is_connected(other_node):
                new_interval_list.append(curr_node & other_node)
                if curr_node.upper > other_node.upper:
                    if len(other) == 0:
                        break
                    else:
                        other_node = other.pop(0)
                else:
                    if len(curr) == 0:
                        break
                    else:
                        curr_node = curr.pop(0)
            else:
                if len(curr) == 0:
                    break
                else:
                    curr_node = curr.pop(0)

        return new_interval_list

    def union(self, *other):
        """Union of a list of Domains.
        Return the Domain that is the union of all Domains."""
        result = Domain()
        result._interval_list = self._interval_list
        for dom in other:
            result._interval_list = self.union_intervals(result._interval_list + dom._interval_list)

        return result

    def intersection(self, other):  # TODO
        pass

    def start(self):  # TODO
        pass

    def end(self):  # TODO
        pass

    def __contains__(self, item):
        if (self._interval_list is None) or (len(self._interval_list) == 0):
            return False

        for interval in self._interval_list:
            if interval.lower <= item <= interval.upper:
                return True

        return False

    def __eq__(self, other):
        if len(self._interval_list) != len(other._interval_list):
            return False
        else:
            for self_interval, other_interval in zip(self._interval_list, other._interval_list):
                return (self_interval.lower == other_interval.lower) and (self_interval.upper == other_interval.upper)

        return True

    def __or__(self, other):
        """Allow a | b syntax"""
        return self.union(other)
