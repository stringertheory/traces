import numpy as np
import pandas as pd

import traces


def test_sample_pandas_compatibility():
    ts = traces.TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]])
    pd_ts = pd.Series(dict(ts.sample(1, 1, 8)))
    assert all(pd_ts.index[i - 1] == i for i in range(1, 9))
    assert all(pd_ts.values[i - 1] == ts[i] for i in range(1, 9))


def test_moving_average_pandas_compatibility():
    ts = traces.TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]])
    pd_ts = pd.Series(dict(ts.moving_average(1, 2, 0, 8)))
    assert all(pd_ts.index[i] == i for i in range(1, 9))
    assert np.isnan(pd_ts.values[0])
    assert all(pd_ts.values[i] == ts.mean(i - 1, i + 1) for i in range(2, 9))


def test_moving_average_pandas_flag():
    ts = traces.TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]], default=0)
    ma = ts.moving_average(1, 2, -1, 11, pandas=True)
    assert list(zip(ma.index, ma)) == [
        (-1, 0.0),
        (0, 0.0),
        (1, 1.0),
        (2, 2.5),
        (3, 3.0),
        (4, 3.0),
        (5, 3.0),
        (6, 2.0),
        (7, 1.0),
        (8, 2.5),
        (9, 4.0),
        (10, 4.0),
        (11, 4.0),
    ]
