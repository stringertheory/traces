import traces
import random
import datetime
from infinity import inf


def average(values):
    sum_ = 0
    n = 0
    for i in values:
        if i is not None:
            sum_ += i
            n += 1
    return float(sum_) / n


class Test(traces.TimeSeries):

    def stack(self, duration, start_times, operation):
        ts_list = []
        for start in start_times:
            end = start + duration
            ts = traces.TimeSeries()
            for t0, dur, value in self.iterperiods(start, end):
                offset = t0 - start
                if isinstance(offset, datetime.timedelta):
                    offset = offset.total_seconds()
                ts.set(offset, value, compact=True)
            ts_list.append(ts)
        return traces.TimeSeries.merge(ts_list, operation=operation)


def xmprint(ts):
    for t, v in ts:
        # print t.isoformat(), v
        print(t, v)


def generate_ts(n_days):
    start_time = datetime.datetime(2016, 1, 1)
    state = 1
    ts = Test(default_value=0)
    ts[start_time] = state
    for offset in range(24 * 60 * n_days):
        if random.random() < 0.1:
            if random.random() < 0.5:
                state += 1
            else:
                state -= 1
            t = start_time + datetime.timedelta(minutes=offset)
            ts.set(t, state % 5, compact=True)
    ts[start_time + datetime.timedelta(days=n_days)] = 0
    return ts


def hour_mask(n_days, hours):
    start_time = datetime.datetime(2016, 1, 1)
    domain = TimeSeries(default=False)
    for day in range(n_days):
        start = start_time + datetime.timedelta(days=day, hours=hours)
        end = start + datetime.timedelta(hours=1)
        domain[start] = True
        domain[end] = False
    return domain


n_days = 5
ts = generate_ts(n_days)

# for t0, t1 in ts.to_TimeSeries(default=False).intervals():
#     print t0.isoformat(), -1
#     print t1.isoformat(), -1

# print ''

# for t, v in ts:
#     print t.isoformat(), v
# raise 'STOP'


start_times = []
start_time = datetime.datetime(2016, 1, 1)
for i in range(n_days):
    t = start_time + datetime.timedelta(days=i)
    start_times.append(t)

stack = ts.stack(datetime.timedelta(days=1), start_times, average)
xmprint(stack)

print ''

for hour in range(24):
    mask = hour_mask(n_days, hour)
    print hour * 60 * 60, ts.distribution(mask=mask).mean()
print (hour + 1) * 60 * 60, ts.distribution(mask=mask).mean()

print ''

unit = 60 * 60
start = 0
end = start + unit
while end <= 24 * 60 * 60:
    value = stack.mean(start, end)
    print start, value
    start += unit
    end += unit
print start, value

print ''

for t, v in sorted(stack.moving_average(60 * 60, 60 * 60, 0, 24 * 60 * 60).items()):
    print t, v
