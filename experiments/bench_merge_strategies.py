"""Benchmark three merge implementation strategies.

This script compares the performance characteristics of three
approaches to merging multiple TimeSeries:

1. Naive (collect-keys): Collect all unique times, query each
   TimeSeries at each time. Simple but O(T * K * log N) where T is
   unique times, K is number of series, N is points per series.

2. Priority queue (heapq): Online merge using a min-heap. O(N log K)
   time. Each transition yields from the heap. Was the default in
   traces until the flat-sort approach replaced it.

3. Flat sort: Extract all (time, index, value) triples, sort once.
   O(N log N) time via timsort. Cache-friendly, no per-element
   function call overhead.

Results are used in docs/merge_strategies.rst.

Usage:
    poetry run python experiments/bench_merge_strategies.py
"""

import heapq
import random
import time
import tracemalloc

from traces import TimeSeries

# ── Strategy 1: Naive (collect-keys) ──────────────────────────────


def naive_iter_merge(timeseries_list):
    """Collect all unique times, query each series at every time."""
    timeseries_list = list(timeseries_list)
    if not timeseries_list:
        return

    # Collect all unique measurement times across all series
    all_times = set()
    for ts in timeseries_list:
        for t, _v in ts:
            all_times.add(t)

    # At each unique time, query every series
    for t in sorted(all_times):
        yield t, [ts[t] for ts in timeseries_list]


def naive_merge(ts_list, operation=None):
    """Merge using the naive collect-keys approach."""
    default = [ts.default for ts in ts_list]
    if operation:
        default = operation(default)
    result = TimeSeries(default=default)
    for t, merged in naive_iter_merge(ts_list):
        value = merged if operation is None else operation(merged)
        result.set(t, value, compact=True)
    return result


# ── Strategy 2: Priority queue (heapq) ───────────────────────────


def heapq_iter_merge_transitions(timeseries_list):
    """Priority queue merge yielding transitions."""
    timeseries_list = list(timeseries_list)

    heap = []
    for index, ts in enumerate(timeseries_list):
        iterator = iter(ts)
        try:
            t, value = next(iterator)
        except StopIteration:
            pass
        else:
            heapq.heappush(heap, (t, index, value, iterator))

    state = [ts.default for ts in timeseries_list]
    while heap:
        t, index, next_value, iterator = heapq.heappop(heap)
        previous_value = state[index]
        state[index] = next_value
        yield t, index, previous_value, next_value

        try:
            t, value = next(iterator)
        except StopIteration:
            pass
        else:
            heapq.heappush(heap, (t, index, value, iterator))


def heapq_iter_merge(timeseries_list):
    """Deduplicated merge from heapq transitions."""
    timeseries_list = list(timeseries_list)
    if not timeseries_list:
        return

    state = [ts.default for ts in timeseries_list]
    previous_t = object()
    first = True
    for t, index, _prev, value in heapq_iter_merge_transitions(timeseries_list):
        if not first and t != previous_t:
            yield previous_t, list(state)
        state[index] = value
        previous_t = t
        first = False

    if not first:
        yield previous_t, list(state)


def heapq_merge(ts_list, operation=None):
    """Merge using the priority queue approach."""
    default = [ts.default for ts in ts_list]
    if operation:
        default = operation(default)
    result = TimeSeries(default=default)
    for t, merged in heapq_iter_merge(ts_list):
        value = merged if operation is None else operation(merged)
        result.set(t, value, compact=True)
    return result


# ── Strategy 3: Flat sort (current implementation) ────────────────
# Just uses TimeSeries.merge directly.


# ── Benchmark harness ─────────────────────────────────────────────


def make_boolean_ts_list(k, n_per_series=2):
    """K boolean timeseries, each with n_per_series transitions."""
    ts_list = []
    for _ in range(k):
        ts = TimeSeries(default=0)
        t = random.uniform(0, 1000)
        for j in range(n_per_series):
            ts[t] = j % 2
            t += random.uniform(1, 50)
        ts_list.append(ts)
    return ts_list


def make_int_ts_list(k, n_per_series=100):
    """K integer timeseries, each with n_per_series transitions."""
    ts_list = []
    for _ in range(k):
        ts = TimeSeries(default=0)
        t = 0
        for _ in range(n_per_series):
            t += random.uniform(0, 5)
            ts[t] = random.randint(0, 10)
        ts_list.append(ts)
    return ts_list


def bench(label, func, repeat=3):
    """Return (min_time, peak_memory_kb)."""
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
    return best, peak_mem / 1024


def print_row(label, time_s, mem_kb):
    print(f"  {label:40s}  {time_s:8.4f}s  {mem_kb:8.1f} KB")


def run():
    random.seed(42)
    header = f"{'':42s}  {'Time':>8s}  {'Peak Mem':>10s}"
    sep = "-" * 66

    # ── Scenario A: Many series, few transitions ──────────────────
    print("=" * 66)
    print("Scenario A: Many series, few transitions per series (K x N=2)")
    print(sep)
    print(header)
    print(sep)

    for k in [10, 50, 100, 500, 1000]:
        ts_list = make_boolean_ts_list(k, n_per_series=2)
        print(f"\n  K = {k} ({k * 2} total transitions)")

        t, m = bench("naive", lambda tl=ts_list: naive_merge(tl, operation=sum))
        print_row("naive (collect-keys)", t, m)

        t, m = bench("heapq", lambda tl=ts_list: heapq_merge(tl, operation=sum))
        print_row("priority queue (heapq)", t, m)

        t, m = bench(
            "flat",
            lambda tl=ts_list: TimeSeries.merge(tl, operation=sum),
        )
        print_row("flat sort (current)", t, m)

    # ── Scenario B: Few series, many transitions ──────────────────
    print()
    print("=" * 66)
    print("Scenario B: Few series, many transitions per series")
    print(sep)
    print(header)
    print(sep)

    for k, n in [(2, 100), (2, 1000), (5, 100), (5, 1000)]:
        ts_list = make_int_ts_list(k, n_per_series=n)
        print(f"\n  K = {k}, N = {n} ({k * n} total transitions)")

        t, m = bench("naive", lambda tl=ts_list: naive_merge(tl, operation=sum))
        print_row("naive (collect-keys)", t, m)

        t, m = bench("heapq", lambda tl=ts_list: heapq_merge(tl, operation=sum))
        print_row("priority queue (heapq)", t, m)

        t, m = bench(
            "flat",
            lambda tl=ts_list: TimeSeries.merge(tl, operation=sum),
        )
        print_row("flat sort (current)", t, m)

    # ── Scenario C: iter_merge (full state lists) ─────────────────
    print()
    print("=" * 66)
    print("Scenario C: iter_merge memory (yielding full state lists)")
    print(sep)
    print(header)
    print(sep)

    for k in [100, 500, 1000]:
        ts_list = make_boolean_ts_list(k, n_per_series=2)
        print(f"\n  K = {k} ({k * 2} total transitions)")

        t, m = bench(
            "naive",
            lambda tl=ts_list: list(naive_iter_merge(tl)),
        )
        print_row("naive (collect-keys)", t, m)

        t, m = bench(
            "heapq",
            lambda tl=ts_list: list(heapq_iter_merge(tl)),
        )
        print_row("priority queue (heapq)", t, m)

        t, m = bench(
            "flat",
            lambda tl=ts_list: list(TimeSeries.iter_merge(tl)),
        )
        print_row("flat sort (current)", t, m)

    # ── Scenario D: Consuming transitions directly ─────────────────
    # This isolates the sort-vs-heap difference without the O(K)
    # list copy overhead of iter_merge/merge. Mirrors what
    # count_by_value does internally.
    print()
    print("=" * 66)
    print("Scenario D: Consuming transitions directly (no K-element copies)")
    print(sep)
    print(header)
    print(sep)

    for k in [100, 500, 1000, 5000]:
        ts_list = make_boolean_ts_list(k, n_per_series=2)
        print(f"\n  K = {k} ({k * 2} total transitions)")

        def consume_heapq(tl=ts_list):
            for _t, _i, _p, _v in heapq_iter_merge_transitions(tl):
                pass

        def consume_flat(tl=ts_list):
            for _t, _i, _p, _v in TimeSeries.iter_merge_transitions(tl):
                pass

        t, m = bench("heapq", consume_heapq)
        print_row("priority queue (heapq)", t, m)

        t, m = bench("flat", consume_flat)
        print_row("flat sort (current)", t, m)

    # ── Scenario E: Where the heap should win ──────────────────────
    # Few series with very many transitions: K is small so log K is
    # tiny, but N is large so flat sort pays O(N log N) vs the heap's
    # O(N log K). Tests whether the heap's asymptotic advantage
    # overcomes timsort's lower constant factor.
    print()
    print("=" * 66)
    print("Scenario E: Few series, very many transitions (heap advantage?)")
    print(sep)
    print(header)
    print(sep)

    for k, n in [
        (2, 10000),
        (2, 50000),
        (2, 100000),
        (2, 500000),
        (3, 50000),
    ]:
        ts_list = make_int_ts_list(k, n_per_series=n)
        total = k * n
        print(f"\n  K = {k}, N/series = {n:,} (N total = {total:,})")

        def consume_heapq(tl=ts_list):
            for _t, _i, _p, _v in heapq_iter_merge_transitions(tl):
                pass

        def consume_flat(tl=ts_list):
            for _t, _i, _p, _v in TimeSeries.iter_merge_transitions(tl):
                pass

        t, m = bench("heapq", consume_heapq)
        print_row("priority queue (heapq)", t, m)

        t, m = bench("flat", consume_flat)
        print_row("flat sort (current)", t, m)


if __name__ == "__main__":
    run()
