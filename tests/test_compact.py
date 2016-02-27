import nose

import traces

import random


def test_compact():

    # since this is random, do it a bunch of times
    for n_trial in range(100):

        # make two time series, one compact and one not
        test_ts = traces.TimeSeries()
        compact_ts = traces.TimeSeries()
        for t in range(100):
            value = random.randint(0, 2)
            test_ts.set(t, value)
            compact_ts.set(t, value, compact=True)

        # make test_ts compact
        test_ts.compact()

        # items should be exactly the same
        assert test_ts.items() == compact_ts.items()
