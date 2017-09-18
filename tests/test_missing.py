import nose
import traces

"""example code for dealing with missing datapoints"""

router_a = traces.TimeSeries([
    (-10, 0), (-7, 1), (-5, traces.nan), (0, 3), (1, 3), (5, traces.nan)
])

assert router_a[-15] is traces.nan
assert not router_a[15]

router_b = traces.TimeSeries([
    (-8, 0), (-5, 0), (-2, 1), (5, 0), (10, traces.nan)
])

# a separate signal tells us that the router went down at -1 and 10
# we have no extra data about when it came online (other than the readings)
for start, stop, value in router_b.iterintervals():
    for timestamp in [-1, 10]:
        if timestamp >= start and timestamp < end:
            router_b.set_interval(timestamp, stop, traces.nan)

assert router_b[-5] is 0
assert router_b[0] is traces.nan
assert router_b[7] is 0

router_list = [router_a, router_b]

def count_merge(iterable):
    output = traces.nan
    for value in iterable:
        if value is not traces.nan:
            output += value
    return output

# the default here should be the element returned by `count_merge([])`
clients = traces.merge(router_list, operation=count_merge)
assert clients[-15] is traces.nan
assert clients[-6] is 1
assert clients[-0.5] is traces.nan
assert clients[3] is 3
assert clients[15] is traces.nan

system_uptime = clients.exists()
assert sysmtem_uptime[-15] is False
assert system_uptime[-5] is True
assert system_uptime[-1] is False
