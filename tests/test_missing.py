import nose
import traces
import unittest

# @unittest.skip("not fully fleshed out yet")
def test_missing():
    """example code for dealing with missing datapoints"""
    router_a = traces.TimeSeries([
        (-10, 0), (-7, 1), (-5, None), (0, 3), (1, 3), (5, None)
    ])

    assert router_a[-6] == 1
    assert router_a[-15] is None
    assert not router_a[15]

    router_b = traces.TimeSeries([
        (-8, 0), (-5, 0), (-2, 1), (5, 3)
    ], default=0)

    assert router_b[7] == 3

    # a separate signal tells us that the router went down at -10, -1 and 10
    # we have no extra data about when it came online (other than the readings)
    for timestamp in [-10, -1, 10]:
        if timestamp < router_b.first_key():
            router_b.default = None
        for start, end, value in router_b.iterperiods():
            if timestamp >= start and timestamp < end:
                router_b[timestamp] = None
        if timestamp >= router_b.last_key():
            router_b[timestamp] = None

    assert router_b[-15] is None
    assert router_b[-6] == 0
    assert router_b[0] is None
    assert router_b[7] == 3

    router_list = [router_a, router_b]

    # the default here should be the element returned by `count_merge([])`


    clients = traces.TimeSeries.merge(
        router_list,
        operation=traces.operations.strict_sum
    )
    assert clients[-15] is None
    assert clients[-6] is 1
    assert clients[-0.5] is None
    assert clients[3] is None
    assert clients[15] is None

    system_uptime = clients.exists()
    assert system_uptime[-15] is False
    assert system_uptime[-6] is True
    assert system_uptime[-1] is False

    clients = traces.TimeSeries.merge(
        router_list,
        operation=traces.operations.ignorant_sum
    )
    assert clients[-15] is 0
    assert clients[-6] is 1
    assert clients[-0.5] is 0
    assert clients[3] is 3
    assert clients[15] is 0

    system_uptime = clients.exists()
    assert system_uptime[-15] is True
    assert system_uptime[-5] is True
    assert system_uptime[-1] is True
