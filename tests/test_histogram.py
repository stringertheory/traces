import traces


def test_normalize():
    data = [15, 15, 20, 20, 20, 35, 35, 40, 40, 50, 50]
    histogram = traces.Histogram(data)
    normalized = histogram.normalized()

    assert sum(normalized.values()) == 1.0


def test_addition():
    hist_a = traces.Histogram([1, 1, 1, 2, 3, 5])
    hist_b = traces.Histogram([0, 0, 1, 2, 2])

    together = hist_a.add(hist_b)
    assert list(together.items()) == [(0, 2), (1, 4), (2, 3), (3, 1), (5, 1)]


def test_minmax_with_zeros():
    histogram = traces.Histogram()

    histogram[0] += 0
    histogram[1] += 1
    histogram[2] += 1
    histogram[3] += 0

    assert histogram.min() == 1
    assert histogram.max() == 2


def test_histogram_stats_with_nones():
    histogram = traces.Histogram()

    assert histogram.mean() is None
    assert histogram.variance() is None
    assert histogram.standard_deviation() is None
    assert histogram.min() is None
    assert histogram.max() is None
    assert histogram.median() is None

    histogram = traces.Histogram.from_dict({None: 1})

    assert histogram.mean() is None
    assert histogram.variance() is None
    assert histogram.standard_deviation() is None
    assert histogram.min() is None
    assert histogram.max() is None
    assert histogram.median() is None

    ts = traces.TimeSeries()
    ts[0] = None
    ts[1] = 5
    ts[2] = 6
    ts[3] = None
    ts[9] = 7
    ts[10] = None

    histogram = ts.distribution(start=0, end=10)
    assert histogram.mean() == 6
    assert histogram.max() == 7
    assert histogram.min() == 5
