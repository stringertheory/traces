import numpy
import pytest
from scipy import stats

import traces


def test_quantiles():
    data = [15, 15, 20, 20, 20, 35, 35, 40, 40, 50, 50]

    histogram = traces.Histogram(data)

    alpha = 0.5
    q_list = [0.05, 0.25, 0.5, 0.75, 0.95]
    q_values = histogram.quantiles(q_list, alpha=alpha, smallest_count=1)
    reference = stats.mstats.mquantiles(
        data, prob=q_list, alphap=0.5, betap=0.5
    )

    for i, j in zip(q_values, reference, strict=False):
        assert i == j


def _test_statistics(normalized):
    data_list = [
        [1, 2, 3, 5, 6, 7],
        [1, 2, 3, 5, 6],
        [1, 1],
        [1, 1, 1, 1, 1, 1, 1, 2],
        [i + 0.25 for i in [1, 1, 1, 1, 1, 1, 1, 2]],
    ]

    for data in data_list:
        histogram = traces.Histogram(data)
        if normalized:
            histogram = histogram.normalized()
            n = 1
        else:
            n = len(data)

        assert histogram.total() == pytest.approx(n)
        assert histogram.mean() == pytest.approx(numpy.mean(data))
        assert histogram.variance() == pytest.approx(numpy.var(data))
        assert histogram.standard_deviation() == pytest.approx(numpy.std(data))
        assert histogram.max() == pytest.approx(numpy.max(data))
        assert histogram.min() == pytest.approx(numpy.min(data))
        assert histogram.quantile(0.5) == pytest.approx(numpy.median(data))
        q_list = [0.001, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 0.999]

        # linear interpolation
        result = histogram.quantiles(q_list)
        reference = stats.mstats.mquantiles(
            data,
            prob=q_list,
            alphap=0.5,
            betap=0.5,
        )
        for i, j in zip(result, reference, strict=False):
            assert i == pytest.approx(j)

        # make sure ot throw an error for bad quantile value
        pytest.raises(ValueError, histogram.quantile, -1)


def test_statistics():
    return _test_statistics(True)


def test_normalized_statistics():
    return _test_statistics(False)


def test_quantile_interpolation():
    data = [1, 1, 1, 2, 3, 5, 6, 7]
    histogram = traces.Histogram(data)
    normalized = histogram.normalized()

    q_list = [0.001, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 0.999]

    # just do the inverse of the emperical cdf
    result = histogram.quantiles(q_list, alpha=0, smallest_count=1)
    answer = [1.0, 1.0, 1.0, 1.0, 2.5, 5.5, 7.0, 7.0, 7.0]
    for i, j in zip(result, answer, strict=False):
        assert i == pytest.approx(j)

    # same thing with normalized
    result = normalized.quantiles(
        q_list, alpha=0, smallest_count=1.0 / len(data)
    )
    for i, j in zip(result, answer, strict=False):
        assert i == pytest.approx(j)

    # now do the linear interpolation method
    result = histogram.quantiles(q_list, alpha=0.5, smallest_count=1)
    answer = stats.mstats.mquantiles(
        data,
        prob=q_list,
        alphap=0.5,
        betap=0.5,
    )
    for i, j in zip(result, answer, strict=False):
        assert i == pytest.approx(j)

    # same thing with normalized
    result = normalized.quantiles(
        q_list,
        alpha=0.5,
        smallest_count=1.0 / len(data),
    )
    for i, j in zip(result, answer, strict=False):
        assert i == pytest.approx(j)
