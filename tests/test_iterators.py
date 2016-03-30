import datetime
import random
import sys
import pprint

import nose

from traces import TimeSeries


def test_iterintervals():

    ts = TimeSeries()
    ts.set(datetime.datetime(2015, 3, 1), 1)
    ts.set(datetime.datetime(2015, 3, 2), 0)
    ts.set(datetime.datetime(2015, 3, 3), 1)
    ts.set(datetime.datetime(2015, 3, 4), 2)

    answer = [(1, 0), (0, 1), (1, 2)]
    result = []
    for (t0, v0), (t1, v1) in ts.iterintervals():
        result.append((v0, v1))
    assert answer == result

    answer = [(1, 0), (1, 2)]
    result = []
    for (t0, v0), (t1, v1) in ts.iterintervals(value=1):
        result.append((v0, v1))
    assert answer == result

    def filter(args):
        (t0, v0), (t1, v1) = args
        return True if not v0 else False

    answer = [(0, 1)]
    result = []
    for (t0, v0), (t1, v1) in ts.iterintervals(value=filter):
        result.append((v0, v1))
    assert answer == result


def test_slice():

    ts = TimeSeries(int)
    ts[0] = 1
    ts[1] = 5
    ts[4] = 0
    ts[6] = 2

    assert ts.slice(0.5, 2.5).items() == [(0.5, 1), (1, 5), (2.5, 5)]
    assert ts.slice(1.0, 2.5).items() == [(1.0, 5), (2.5, 5)]
    assert ts.slice(-1, 1).items() == [(-1, 0), (0, 1), (1, 5)]
    assert ts.slice(-1, 0.5).items() == [(-1, 0), (0, 1), (0.5, 1)]

def make_random_timeseries():
    length = random.randint(0, 10)
    result = TimeSeries()
    t = 0
    for i in range(length):
        t += random.randint(0, 5)
        x = random.randint(0, 5)
        result[t] = x
    return result
    
def test_merge():

    # since this is random, do it a bunch of times
    for n_trial in range(1000):

        # make a list of TimeSeries that is anywhere from 0 to 5
        # long. Each TimeSeries is of random length between 0 and 20,
        # with random time points and random values.
        ts_list = []
        for i in range(random.randint(0, 5)):
            ts_list.append(make_random_timeseries())

        method_a = list(TimeSeries.merge(ts_list))
        method_b = list(TimeSeries.iter_merge(ts_list))
        
        msg = '%s != %s' % (pprint.pformat(method_a), pprint.pformat(method_b))
        assert method_a == method_b, msg

