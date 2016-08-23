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

        temp_interval_list = []

        # TODO: there might be better way to do all these checks
        if len(args) is not 0:
            if not args[0] and len(args) != 2:
                temp_interval_list.append(intervals.FloatInterval(None))

            else:
                list_of_pairs = convert_args_to_list(args)

                if list_of_pairs[0] == [-inf, inf]:
                    temp_interval_list.append(
                        intervals.FloatInterval([-inf, inf]))

                else:
                    first_item = list_of_pairs[0]
                    if any(isinstance(item, datetime.datetime)
                           for item in first_item):
                        data_type = datetime.datetime
                    elif any(isinstance(item,  (int, float))
                             for item in first_item):
                        data_type = float
                    else:
                        msg = "Can't create a Domain with {}.".format(
                            type(first_item))
                        raise TypeError(msg)

                    if data_type == datetime.datetime:
                        for start, end in list_of_pairs:
                            if (isinstance(start, (datetime.datetime)) or
                                start == -inf or
                                start is None) and \
                                (isinstance(end, (datetime.datetime, inf)) or
                                 end == inf or
                                 end is None):
                                temp_interval_list.append(
                                    intervals.DateTimeInterval([start, end]))
                            else:
                                msg = "Can't create a Domain with mixed types."
                                raise TypeError(msg)
                    elif data_type == float:
                        for start, end in list_of_pairs:
                            if (isinstance(start, (int, float)) or
                                start == -inf or
                                start is None) and \
                                    (isinstance(end, (int, float)) or
                                     end == inf or
                                     end is None):
                                temp_interval_list.append(
                                    intervals.FloatInterval([start, end]))
                            else:
                                msg = "Can't create a Domain with mixed types."
                                raise TypeError(msg)

        self._interval_list = self.union_intervals(temp_interval_list)

    def __repr__(self):
        output = '\n'.join('{}'.format(
            [interval.lower, interval.upper])
                           for interval in self._interval_list)
        return '<Domain>\n{}\n</Domain>'.format(output)

    def n_intervals(self):
        """Number of disconnected domain"""
        return len(self._interval_list)

    @staticmethod
    def sort_intervals(interval_list):
        """Sort intervals"""
        return sorted(interval_list,
                      key=lambda interval: (interval.lower, interval.upper))

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

        if self._interval_list == [intervals.FloatInterval([-inf, inf])]:
            return result

        for dom in other:
            if dom == Domain(-inf, inf):
                result._interval_list = [intervals.FloatInterval([-inf, inf])]
                return result

            result._interval_list = self.union_intervals(
                result._interval_list + dom._interval_list)

        return result

    def intersection(self, *other):
        """Intersection of a list of Domains.
        Return the Domain that is the intersection of all Domains."""
        result = Domain()
        result._interval_list = self._interval_list

        if self._interval_list == [intervals.FloatInterval([-inf, inf])]:
            result._interval_list = [type(other[0]._interval_list[0])(None)]

        for dom in other:
            if dom == Domain([-inf, inf]):
                temp_interval_list = [type(self._interval_list[0])(None)]
            else:
                temp_interval_list = dom._interval_list

            result._interval_list = self.intersection_intervals(
                result._interval_list, temp_interval_list)
        return result

    def start(self):
        """Return the start time of the domain."""
        if len(self._interval_list) == 0:
            return None
        else:
            return self._interval_list[0].lower

    def end(self):
        """Return the end time of the domain."""
        if len(self._interval_list) == 0:
            return None
        else:
            return self._interval_list[-1].upper

    def intervals(self):
        """Return domain as a list of tuple (start, end)"""
        if len(self._interval_list) == 0:
            return []

        output = []
        for interval in self._interval_list:
            output.append((interval.lower, interval.upper))
        return output

    def slice(self, start_time, end_time):
        """Return a segment of Domain within start and end"""

        if end_time <= start_time:
            message = (
                "Can't slice a Domain when end_time <= start_time. "
                "Received start_time={} and end_time={}."
            ).format(start_time, end_time)
            raise ValueError(message)

        if start_time > self.end():
            raise ValueError(
                "Start time is larger than the end of the Domain.")

        if end_time < self.start():
            raise ValueError(
                "End time is smaller than the start of the Domain.")

        results = []
        for interval in self._interval_list:
            curr_start = interval.lower
            curr_end = interval.upper
            if curr_start <= end_time and curr_end >= start_time:
                if curr_start >= start_time:
                    temp_start = curr_start
                else:
                    temp_start = start_time

                if curr_end <= end_time:
                    temp_end = curr_end
                else:
                    temp_end = end_time

                results.append([temp_start, temp_end])

        sliced_domain = Domain(results)

        return sliced_domain

    def get_duration(self, start=None, end=None):
        """Return the duration between start and end"""

        if start is None:
            start = self.start()

        if end is None:
            end = self.end()

        if start > self.end() or end < self.start():
            return 0

        sliced_domain = self.slice(start, end)

        duration = datetime.timedelta(0) if isinstance(
            start, datetime.datetime) else 0
        for interval in sliced_domain._interval_list:
            duration += interval.upper - interval.lower

        return duration

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
            for self_interval, other_interval \
                    in zip(self._interval_list, other._interval_list):
                if not ((self_interval.lower == other_interval.lower) and
                        (self_interval.upper == other_interval.upper)):
                    return False

        return True

    def __ne__(self, other):
        return not(self == other)

    def __or__(self, other):
        """Allow a | b syntax"""
        return self.union(other)

    def __and__(self, other):
        """Allow a & b syntax"""
        return self.intersection(other)
