"""Compare two approaches for counting open tickets over time.

Approach 1 (TimeSeries + merge(sum)):
    One integer TimeSeries per ticket (1=open, 0=closed),
    then merge with operation=sum to get a count over time.

Approach 2 (TimeSeries + count_by_value):
    One boolean TimeSeries per ticket (True=open, False=closed),
    then count_by_value to get a count of open tickets over time.

Approach 3 (EventSeries + count_active):
    Two EventSeries (opened_events, closed_events),
    then count_active to get a TimeSeries of open ticket count.

Usage:
    poetry run python experiments/bench_tickets.py
"""

import random
import time
import tracemalloc

from traces import TimeSeries
from traces.eventseries import EventSeries


def make_ticket_data(n_tickets):
    """Generate n_tickets, each with an open time and a close time."""
    tickets = []
    for _ in range(n_tickets):
        open_time = random.uniform(0, 1000)
        close_time = open_time + random.uniform(1, 100)
        tickets.append((open_time, close_time))
    return tickets


def approach_timeseries_merge_sum(tickets):
    """One integer TimeSeries per ticket, then merge(sum)."""
    ts_list = []
    for open_time, close_time in tickets:
        ts = TimeSeries(default=0)
        ts[open_time] = 1
        ts[close_time] = 0
        ts_list.append(ts)
    return TimeSeries.merge(ts_list, operation=sum)


def approach_timeseries_count_by_value(tickets):
    """One boolean TimeSeries per ticket, then count_by_value."""
    ts_list = []
    for open_time, close_time in tickets:
        ts = TimeSeries(default=False)
        ts[open_time] = True
        ts[close_time] = False
        ts_list.append(ts)
    result = TimeSeries.count_by_value(ts_list)
    return result[True]


def approach_eventseries_count_active(tickets):
    """Two EventSeries, then count_active."""
    opened = EventSeries([t[0] for t in tickets])
    closed = EventSeries([t[1] for t in tickets])
    return EventSeries.count_active(opened, closed)


def bench(label, func, repeat=5):
    """Run func, report min time and peak memory."""
    times = []
    peak_mem = 0
    for _ in range(repeat):
        tracemalloc.start()
        t0 = time.perf_counter()
        func()
        elapsed = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        times.append(elapsed)
        peak_mem = max(peak_mem, peak)

    best = min(times)
    print(f"  {label:55s}  {best:8.4f}s  {peak_mem / 1024:8.1f} KB")


def run():
    random.seed(42)
    print(f"{'Benchmark':57s}  {'Time':>8s}  {'Peak Mem':>10s}")
    print("-" * 82)

    for n in [100, 500, 1000, 5000, 10000]:
        tickets = make_ticket_data(n)
        print(f"\n  n_tickets = {n}")
        bench(
            "TimeSeries + merge(sum)",
            lambda t=tickets: approach_timeseries_merge_sum(t),
        )
        bench(
            "TimeSeries + count_by_value",
            lambda t=tickets: approach_timeseries_count_by_value(t),
        )
        bench(
            "EventSeries + count_active",
            lambda t=tickets: approach_eventseries_count_active(t),
        )


if __name__ == "__main__":
    run()
