"""Benchmark iter_merge and merge performance.

Run before and after optimization to compare.

Usage:
    poetry run python experiments/bench_merge.py
"""

import random
import time
import tracemalloc

from traces import TimeSeries


def make_boolean_timeseries_list(k, n_transitions=2):
    """Create K boolean timeseries each with N transitions."""
    ts_list = []
    for _i in range(k):
        ts = TimeSeries(default=False)
        t = random.uniform(0, 100)
        for j in range(n_transitions):
            ts[t] = j % 2 == 0
            t += random.uniform(1, 10)
        ts_list.append(ts)
    return ts_list


def make_int_timeseries_list(k, n_transitions=100):
    """Create K integer timeseries each with N transitions."""
    ts_list = []
    for _i in range(k):
        ts = TimeSeries(default=0)
        t = 0
        for _j in range(n_transitions):
            t += random.uniform(0, 5)
            ts[t] = random.randint(0, 10)
        ts_list.append(ts)
    return ts_list


def bench(label, func, repeat=3):
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
    print(f"  {label:45s}  {best:8.4f}s  {peak_mem / 1024:8.1f} KB")


def run_benchmarks():
    random.seed(42)
    print(f"{'Benchmark':47s}  {'Time':>8s}  {'Peak Mem':>10s}")
    print("-" * 72)

    # Many series, few transitions (light-switch use case)
    for k in [10, 50, 100, 500, 1000]:
        ts_list = make_boolean_timeseries_list(k, n_transitions=2)
        bench(
            f"iter_merge K={k} N=2",
            lambda tl=ts_list: list(TimeSeries.iter_merge(tl)),
        )
        bench(
            f"merge(sum) K={k} N=2",
            lambda tl=ts_list: TimeSeries.merge(tl, operation=sum),
        )
        if hasattr(TimeSeries, "count_by_value"):
            bench(
                f"count_by_value K={k} N=2",
                lambda tl=ts_list: TimeSeries.count_by_value(tl),
            )

    print()

    # Fewer series, many transitions
    for k, n in [(2, 100), (2, 1000), (5, 100), (5, 1000)]:
        ts_list = make_int_timeseries_list(k, n_transitions=n)
        bench(
            f"iter_merge K={k} N={n}",
            lambda tl=ts_list: list(TimeSeries.iter_merge(tl)),
        )
        bench(
            f"merge(sum) K={k} N={n}",
            lambda tl=ts_list: TimeSeries.merge(tl, operation=sum),
        )


if __name__ == "__main__":
    run_benchmarks()
