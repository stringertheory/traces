import math
import sortedcontainers
from six import itervalues, iteritems


class UnorderableElements(TypeError):
    pass


class UnhashableType(TypeError):
    pass


class Histogram(sortedcontainers.SortedDict):

    @classmethod
    def from_dict(cls, in_dict, *args, **kwargs):
        self = cls(*args, **kwargs)
        for key, value in iteritems(in_dict):
            self[key] = value
        return self

    def __init__(self, data=(), **kwargs):
        if 'key' in kwargs:
            super(Histogram, self).__init__(kwargs['key'])
        else:
            super(Histogram, self).__init__()

        for datum in data:
            self[datum] += 1

    def __getitem__(self, key):
        try:
            result = super(Histogram, self).__getitem__(key)
        except KeyError:
            result = 0
        except TypeError as e:

            if "unorderable" in str(e):
                raise UnorderableElements(e)

            if "unhashable" in str(e):
                msg = "Can't make histogram of unhashable type (%s)" % type(
                    key)
                raise UnhashableType(msg)

            raise e
        return result

    def __setitem__(self, key, value):
        try:
            result = super(Histogram, self).__setitem__(key, value)
        except TypeError as e:

            if "unorderable" in str(e):
                raise UnorderableElements(e)

            if "not supported between instances of" in str(e):
                raise UnorderableElements(e)

            if "unhashable" in str(e):
                msg = "Can't make histogram of unhashable type (%s)" % type(
                    key)
                raise UnhashableType(msg)

            raise e
        return result

    def total(self):
        """Sum of values."""
        return sum(itervalues(self))

    def mean(self):
        """Mean of the distribution."""
        _self = self._discard_value(None)
        if not _self.total():
            return None
        weighted_sum = sum(
            key * value for key, value in iteritems(_self)
        )
        return weighted_sum / float(_self.total())

    def variance(self):
        """Variance of the distribution."""
        _self = self._discard_value(None)
        if not _self.total():
            return 0.0
        mean = _self.mean()
        weighted_central_moment = sum(
            count * (value - mean)**2 for value, count in iteritems(_self)
        )
        return weighted_central_moment / float(_self.total())

    def standard_deviation(self):
        """Standard deviation of the distribution."""
        return math.sqrt(self.variance())

    def normalized(self):
        """Return a normalized version of the histogram where the values sum
        to one.

        """
        total = self.total()
        result = Histogram()
        for value, count in iteritems(self):
            try:
                result[value] = count / float(total)
            except UnorderableElements as e:
                result = Histogram.from_dict(dict(result), key=hash)
                result[value] = count / float(total)
        return result

    def _discard_value(self, value):
        if value not in self:
            return self
        else:
            return self.__class__.from_dict(
                {k: v for k, v in iteritems(self) if k is not value}
            )

    def max(self):
        """Maximum observed value."""
        return self.iloc[-1]

    def min(self):
        """Minimum observed value."""
        return self.iloc[0]

    def _quantile_function(self, alpha=0.5, smallest_count=None):
        """Return a function that returns the quantile values for this
        histogram.

        """
        total = float(self.total())

        smallest_observed_count = min(itervalues(self))
        if smallest_count is None:
            smallest_count = smallest_observed_count
        else:
            smallest_count = min(smallest_count, smallest_observed_count)

        beta = alpha * smallest_count

        debug_plot = []
        cumulative_sum = 0.0
        inverse = sortedcontainers.SortedDict()
        for value, count in iteritems(self):
            debug_plot.append((cumulative_sum / total, value))
            inverse[(cumulative_sum + beta) / total] = value
            cumulative_sum += count
            inverse[(cumulative_sum - beta) / total] = value
            debug_plot.append((cumulative_sum / total, value))

        # get maximum and minumum q values
        q_min = inverse.iloc[0]
        q_max = inverse.iloc[-1]

        # this stuff if helpful for debugging -- keep it in here
        # for i, j in debug_plot:
        #     print i, j
        # print ''
        # for i, j in inverse.iteritems():
        #     print i, j
        # print ''

        def function(q):

            if q < 0.0 or q > 1.0:
                msg = 'invalid quantile %s, need `0 <= q <= 1`' % q
                raise ValueError(msg)
            elif q < q_min:
                q = q_min
            elif q > q_max:
                q = q_max

            # if beta is
            if beta > 0:
                if q in inverse:
                    result = inverse[q]
                else:
                    previous_index = inverse.bisect_left(q) - 1
                    x1 = inverse.iloc[previous_index]
                    x2 = inverse.iloc[previous_index + 1]
                    y1 = inverse[x1]
                    y2 = inverse[x2]
                    result = (y2 - y1) * (q - x1) / float(x2 - x1) + y1

            else:
                if q in inverse:
                    previous_index = inverse.bisect_left(q) - 1
                    x1 = inverse.iloc[previous_index]
                    x2 = inverse.iloc[previous_index + 1]
                    y1 = inverse[x1]
                    y2 = inverse[x2]
                    result = 0.5 * (y1 + y2)
                else:
                    previous_index = inverse.bisect_left(q) - 1
                    x1 = inverse.iloc[previous_index]
                    result = inverse[x1]

            return float(result)

        return function

    def median(self, alpha=0.5, smallest_count=None):
        return self.quantile(0.5, alpha=alpha, smallest_count=smallest_count)

    def quantiles(self, q_list, alpha=0.5, smallest_count=None):
        f = self._quantile_function(alpha=alpha, smallest_count=smallest_count)
        return [f(q) for q in q_list]

    def quantile(self, q, alpha=0.5, smallest_count=None):
        return \
            self.quantiles([q], alpha=alpha, smallest_count=smallest_count)[0]

    def add(self, other):
        result = Histogram()
        for key, value in iteritems(self):
            result[key] += value
        for key, value in iteritems(other):
            result[key] += value
        return result

    __add__ = add
