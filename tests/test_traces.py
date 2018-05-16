from datetime import datetime
import pickle
import nose

from traces import TimeSeries
import csv
import os


def test_init_data():
    ts = TimeSeries([(1, 2), (2, 3), (6, 1), (8, 4)])

    assert ts[0] is None
    assert ts[1] == 2
    assert ts[1.5] == 2
    assert ts[6] == 1
    assert ts[7] == 1
    assert ts[8] == 4
    assert ts[10] == 4

    ts = TimeSeries([[1, 2], [2, 3], [6, 1], [8, 4]])

    assert ts[0] is None
    assert ts[1] == 2
    assert ts[1.5] == 2
    assert ts[6] == 1
    assert ts[7] == 1
    assert ts[8] == 4
    assert ts[10] == 4

    ts = TimeSeries({1: 2, 2: 3, 6: 1, 8: 4})

    assert ts[0] is None
    assert ts[1] == 2
    assert ts[1.5] == 2
    assert ts[6] == 1
    assert ts[7] == 1
    assert ts[8] == 4
    assert ts[10] == 4


def test_get():
    ts = TimeSeries()
    # nose.tools.assert_raises(KeyError, ts.get, 0)
    assert ts[0] is None

    ts[1.2] = 1
    ts[3] = 0
    ts[6] = 2

    assert ts[0] is None
    assert ts[5.5] == 0
    assert ts[7] == 2


def test_exists():
    ts = TimeSeries([
        (-5, 0), (0, 23), (5, None)
    ])

    ts_exists = ts.exists()
    assert ts_exists[-10] is False
    assert ts_exists[-2] is True
    assert ts_exists[3] is True
    assert ts_exists[10] is False


def test_merge():
    ts_a = TimeSeries()
    ts_b = TimeSeries()
    # ts_a[0] = None
    ts_b[0] = True
    ts_merge = TimeSeries.merge([ts_a, ts_b])

    assert True in ts_merge[0]
    assert None in ts_merge[0]


def test_set_interval():
    ts = TimeSeries()
    # nose.tools.assert_raises(KeyError, ts.get, 0)
    assert ts[0] is None

    ts.set_interval(2, 4, 5)

    assert ts[0] is None
    assert ts[2] == 5
    assert ts[3] == 5
    assert ts[4] is None
    assert ts[5] is None

    ts = TimeSeries()
    ts[1.2] = 1
    ts[3] = 0
    ts[6] = 2

    assert ts[0] is None
    assert ts[5.5] == 0
    assert ts[7] == 2

    ts[2:4] = 5
    assert ts.items() == [(1.2, 1), (2, 5), (4, 0), (6, 2)]

    ts[3:5] = 4
    assert ts.items() == [(1.2, 1), (2, 5), (3, 4), (5, 0), (6, 2)]

    tsc = TimeSeries(ts)

    ts.set_interval(3, 4, 4)
    assert ts.items() == [(1.2, 1), (2, 5), (3, 4), (4, 4), (5, 0), (6, 2)]

    tsc.set_interval(3, 4, 4, compact=True)
    assert tsc.items() == [(1.2, 1), (2, 5), (3, 4), (5, 0), (6, 2)]


def test_set_interval_datetime():
    ts = TimeSeries(default=400)
    ts[datetime(2012, 1, 4, 12)] = 5
    ts[datetime(2012, 1, 9, 18)] = 10
    ts[datetime(2012, 1, 8):datetime(2012, 1, 10)] = 100

    assert ts.items() == [(datetime(2012, 1, 4, 12, 0), 5),
                          (datetime(2012, 1, 8, 0, 0), 100),
                          (datetime(2012, 1, 10, 0, 0), 10)]


def test_remove_points_from_interval():
    ts = TimeSeries(default=0)
    ts[0] = 0
    ts[1] = 2
    ts[3] = 1
    ts[4] = 0

    assert ts[5] == 0

    del ts[3.5:4.5]

    assert ts[5] == 1

    ts[4] = 0

    del ts[3:4.5]

    assert ts[5] == 2

    ts[3] = 1
    ts[4] = 0

    del ts[3.5:4]

    assert ts[5] == 0


def test_pickle():
    ts = TimeSeries(default=False)
    ts[1] = True
    ts[2] = False
    dump_string = pickle.dumps(ts)
    unpickled = pickle.loads(dump_string)
    assert unpickled == ts

    unpickled[3] = unpickled[1]
    assert unpickled[3] is True


def test_csv():
    def time_parse(value):
        return int(value)

    def value_parse(value):
        try:
            return int(value)
        except ValueError:
            return None

    filename = 'sample.csv'
    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['hour', 'value'])
        writer.writerow(['10', '15'])
        writer.writerow(['11', '34'])
        writer.writerow(['12', '19'])
        writer.writerow(['13', 'nan'])
        writer.writerow(['14', '18'])
        writer.writerow(['15', 'nan'])

    ts = TimeSeries.from_csv(
        filename,
        time_column=0,
        time_transform=time_parse,
        value_column=1,
        value_transform=value_parse,
        default=None
    )
    os.remove(filename)

    assert ts[9] is None
    assert ts[20] is None
    assert ts[13.5] is None

    histogram = ts.distribution()
    nose.tools.assert_almost_equal(histogram.mean(), (15 + 34 + 19 + 18) / 4.0)
