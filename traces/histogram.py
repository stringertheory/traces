import math
import sortedcontainers
import warnings


class UnorderableElements(TypeError):
    pass


class UnhashableType(TypeError):
    pass


class Histogram(sortedcontainers.SortedDict):

    @classmethod
    def from_dict(cls, in_dict, *args, **kwargs):
        self = cls(*args, **kwargs)
        for key, value in in_dict.items():
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
        return sum(self.values())

    def _prepare_for_stats(self):
        """Removes None values and calculates total."""
        clean = self._discard_value(None)
        total = float(clean.total())
        return clean, total

    def mean(self):
        """Mean of the distribution."""
        clean, total = self._prepare_for_stats()
        if not total:
            return None

        weighted_sum = sum(key * value for key, value in clean.items())
        return weighted_sum / total

    def variance(self):
        """Variance of the distribution."""
        clean, total = self._prepare_for_stats()
        if not total:
            return None

        mean = self.mean()
        weighted_central_moment = sum(
            count * (value - mean)**2 for value, count in clean.items()
        )
        return weighted_central_moment / total

    def standard_deviation(self):
        """Standard deviation of the distribution."""
        clean, total = self._prepare_for_stats()
        if not total:
            return None

        return math.sqrt(clean.variance())

    def normalized(self):
        """Return a normalized version of the histogram where the values sum
        to one.

        """
        total = self.total()
        result = Histogram()
        for value, count in self.items():
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
                {k: v for k, v in self.items() if k is not value}
            )

    def max(self, include_zero=False):
        """Maximum observed value with non-zero count."""
        for key, value in reversed(self.items()):
            if value > 0 or include_zero:
                return key

    def min(self, include_zero=False):
        """Minimum observed value with non-zero count."""
        for key, value in self.items():
            if value > 0 or include_zero:
                return key

    def _quantile_function(self, alpha=0.5, smallest_count=None):
        """Return a function that returns the quantile values for this
        histogram.

        """
        clean, total = self._prepare_for_stats()
        if not total:
            def function(q):
                return None
            return function

        smallest_observed_count = min(clean.values())
        if smallest_count is None:
            smallest_count = smallest_observed_count
        else:
            smallest_count = min(smallest_count, smallest_observed_count)

        beta = alpha * smallest_count

        debug_plot = []
        cumulative_sum = 0.0
        inverse = sortedcontainers.SortedDict()
        for value, count in clean.items():
            debug_plot.append((cumulative_sum / total, value))
            inverse[(cumulative_sum + beta) / total] = value
            cumulative_sum += count
            inverse[(cumulative_sum - beta) / total] = value
            debug_plot.append((cumulative_sum / total, value))

        # get maximum and minumum q values
        q_min = inverse.keys()[0]
        q_max = inverse.keys()[-1]

        # this stuff if helpful for debugging -- keep it in here
        # for i, j in debug_plot:
        #     print i, j
        # print ''
        # for i, j in inverse.items():
        #     print i, j
        # print ''

        def function(q):

            if q < 0.0 or q > 1.0:
                msg = 'invalid quantile {}, need `0 <= q <= 1`'.format(q)
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
                    x1 = inverse.keys()[previous_index]
                    x2 = inverse.keys()[previous_index + 1]
                    y1 = inverse[x1]
                    y2 = inverse[x2]
                    result = (y2 - y1) * (q - x1) / float(x2 - x1) + y1

            else:
                if q in inverse:
                    previous_index = inverse.bisect_left(q) - 1
                    x1 = inverse.keys()[previous_index]
                    x2 = inverse.keys()[previous_index + 1]
                    y1 = inverse[x1]
                    y2 = inverse[x2]
                    result = 0.5 * (y1 + y2)
                else:
                    previous_index = inverse.bisect_left(q) - 1
                    x1 = inverse.keys()[previous_index]
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
        for key, value in self.items():
            result[key] += value
        for key, value in other.items():
            result[key] += value
        return result

    __add__ = add
