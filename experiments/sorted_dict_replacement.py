"""Prototype: dict + sorted list as a replacement for SortedDict in TimeSeries.

This file implements a DictTimeSeries class using plain dict + sorted list +
bisect, then benchmarks it against the current SortedDict-based TimeSeries.

Run standalone:
    python experiments/sorted_dict_replacement.py
"""

import bisect
import random
import timeit
from collections import defaultdict

from sortedcontainers import SortedDict

# ---------------------------------------------------------------------------
# Prototype: DictTimeSeries
# ---------------------------------------------------------------------------


class DictTimeSeries:
    """TimeSeries core reimplemented with dict + sorted keys list."""

    def __init__(self, data=None, default=None):
        self.default = default
        self._dict = {}
        self._keys = []
        if data is not None:
            self.set_many(data)

    def set_many(self, data):
        """Bulk insert: update dict, then rebuild sorted keys with Timsort."""
        self._dict.update(data)
        self._keys = sorted(self._dict)

    # -- basic access -------------------------------------------------------

    def set(self, time, value):
        if time in self._dict:
            self._dict[time] = value
        else:
            bisect.insort(self._keys, time)
            self._dict[time] = value

    def __setitem__(self, time, value):
        self.set(time, value)

    def get(self, time):
        """Previous-value interpolation (step function)."""
        if time in self._dict:
            return self._dict[time]
        idx = bisect.bisect_right(self._keys, time)
        if idx > 0:
            return self._dict[self._keys[idx - 1]]
        return self.default

    def __getitem__(self, time):
        return self.get(time)

    def __delitem__(self, time):
        del self._dict[time]
        idx = bisect.bisect_left(self._keys, time)
        if idx < len(self._keys) and self._keys[idx] == time:
            self._keys.pop(idx)
        else:
            raise KeyError(time)

    def __len__(self):
        return len(self._dict)

    def __bool__(self):
        return bool(self._dict)

    def __iter__(self):
        return iter(self.items())

    def items(self):
        return [(k, self._dict[k]) for k in self._keys]

    def first_key(self):
        return self._keys[0]

    def last_key(self):
        return self._keys[-1]

    def get_item_by_index(self, index):
        k = self._keys[index]
        return (k, self._dict[k])

    # -- iterperiods --------------------------------------------------------

    def iterperiods(self, start=None, end=None):
        if start is None:
            start = self._keys[0]
        if end is None:
            end = self._keys[-1]

        start_index = bisect.bisect_right(self._keys, start)
        if start_index > 0:
            start_value = self._dict[self._keys[start_index - 1]]
        else:
            start_value = self.default

        end_index = bisect.bisect_right(self._keys, end)

        interval_t0 = start
        interval_value = start_value

        for i in range(start_index, end_index):
            interval_t1 = self._keys[i]
            yield interval_t0, interval_t1, interval_value
            interval_t0 = interval_t1
            interval_value = self._dict[interval_t1]

        if interval_t0 < end:
            yield interval_t0, end, interval_value

    # -- distribution -------------------------------------------------------

    def distribution(self, start=None, end=None):
        counter = defaultdict(float)
        for t0, t1, value in self.iterperiods(start, end):
            duration = t1 - t0
            counter[value] += duration
        return dict(counter)

    # -- set_interval -------------------------------------------------------

    def set_interval(self, start, end, value):
        end_value = self.get(end)

        # find keys strictly between start and end
        lo = bisect.bisect_right(self._keys, start)
        hi = bisect.bisect_left(self._keys, end)
        to_delete = self._keys[lo:hi]
        for k in to_delete:
            del self._dict[k]
        del self._keys[lo:hi]

        self.set(start, value)
        self.set(end, end_value)

    # -- n_points -----------------------------------------------------------

    def n_points(self, start=None, end=None):
        if start is None and end is None:
            return len(self._keys)
        lo = bisect.bisect_left(self._keys, start) if start is not None else 0
        hi = (
            bisect.bisect_left(self._keys, end)
            if end is not None
            else len(self._keys)
        )
        return hi - lo

    # -- compact ------------------------------------------------------------

    def compact(self):
        previous_value = object()
        redundant = []
        for k in self._keys:
            v = self._dict[k]
            if v == previous_value:
                redundant.append(k)
            previous_value = v
        for k in redundant:
            del self[k]


# ---------------------------------------------------------------------------
# Reference: SortedDictTimeSeries (wraps SortedDict, same interface)
# ---------------------------------------------------------------------------


class SortedDictTimeSeries:
    """Minimal TimeSeries using SortedDict (mirrors DictTimeSeries API)."""

    def __init__(self, data=None, default=None):
        self.default = default
        self._d = SortedDict(data) if data else SortedDict()

    def set_many(self, data):
        """Bulk insert using individual SortedDict sets."""
        self._d.update(data)

    def set(self, time, value):
        self._d[time] = value

    def __setitem__(self, time, value):
        self.set(time, value)

    def get(self, time):
        if time in self._d:
            return self._d[time]
        idx = self._d.bisect_right(time)
        if idx > 0:
            _, v = self._d.peekitem(idx - 1)
            return v
        return self.default

    def __getitem__(self, time):
        return self.get(time)

    def __delitem__(self, time):
        del self._d[time]

    def __len__(self):
        return len(self._d)

    def __bool__(self):
        return bool(self._d)

    def __iter__(self):
        return iter(self.items())

    def items(self):
        return list(self._d.items())

    def first_key(self):
        return self._d.keys()[0]

    def last_key(self):
        return self._d.keys()[-1]

    def get_item_by_index(self, index):
        return self._d.peekitem(index)

    def iterperiods(self, start=None, end=None):
        if start is None:
            start = self.first_key()
        if end is None:
            end = self.last_key()

        start_index = self._d.bisect_right(start)
        if start_index > 0:
            _, start_value = self._d.peekitem(start_index - 1)
        else:
            start_value = self.default

        end_index = self._d.bisect_right(end)

        interval_t0 = start
        interval_value = start_value

        for interval_t1 in self._d.islice(start_index, end_index):
            yield interval_t0, interval_t1, interval_value
            interval_t0 = interval_t1
            interval_value = self._d[interval_t0]

        if interval_t0 < end:
            yield interval_t0, end, interval_value

    def distribution(self, start=None, end=None):
        counter = defaultdict(float)
        for t0, t1, value in self.iterperiods(start, end):
            duration = t1 - t0
            counter[value] += duration
        return dict(counter)

    def set_interval(self, start, end, value):
        end_value = self.get(end)
        for t in list(self._d.irange(start, end, (False, False))):
            del self._d[t]
        self.set(start, value)
        self.set(end, end_value)

    def n_points(self, start=None, end=None):
        if start is None and end is None:
            return len(self._d)
        lo = self._d.bisect_left(start) if start is not None else 0
        hi = self._d.bisect_left(end) if end is not None else len(self._d)
        return hi - lo

    def compact(self):
        previous_value = object()
        redundant = []
        for k, v in self._d.items():
            if v == previous_value:
                redundant.append(k)
            previous_value = v
        for k in redundant:
            del self._d[k]


# ---------------------------------------------------------------------------
# Merge implementations
# ---------------------------------------------------------------------------


def merge_simple(ts_list, operation=None):
    """Simple merge: collect all keys, look up each ts at each key."""
    keys = set()
    for ts in ts_list:
        keys.update(ts._keys if hasattr(ts, "_keys") else ts._d.keys())

    default = [ts.default for ts in ts_list]
    if operation:
        default = operation(default)

    result = type(ts_list[0])(default=default)
    for k in sorted(keys):
        values = [ts.get(k) for ts in ts_list]
        value = operation(values) if operation else values
        result.set(k, value)
    return result


def merge_pq(ts_list, operation=None):
    """Priority-queue merge: mirrors current TimeSeries._iter_merge."""
    from queue import PriorityQueue

    default = [ts.default for ts in ts_list]
    if operation:
        default = operation(default)

    # _iter_merge
    queue = PriorityQueue()
    for index, ts in enumerate(ts_list):
        iterator = iter(ts)
        try:
            t, value = next(iterator)
        except StopIteration:
            pass
        else:
            queue.put((t, index, value, iterator))

    state = [ts.default for ts in ts_list]

    # iter_merge (deduplicate tied times)
    merged = []
    previous_t = object()
    while not queue.empty():
        t, index, next_value, iterator = queue.get()
        state = list(state)
        state[index] = next_value

        if merged and t != previous_t:
            yield_t, yield_state = merged[-1]
            merged[-1] = (yield_t, yield_state)
        merged.append((t, list(state)))
        previous_t = t

        try:
            t2, value2 = next(iterator)
        except StopIteration:
            pass
        else:
            queue.put((t2, index, value2, iterator))

    # deduplicate and build result
    result = type(ts_list[0])(default=default)

    # simpler: just deduplicate
    deduped = []
    for i, (t, state) in enumerate(merged):
        if i + 1 < len(merged) and merged[i + 1][0] == t:
            continue
        deduped.append((t, state))

    for t, state in deduped:
        value = operation(state) if operation else state
        result.set(t, value)
    return result


# ---------------------------------------------------------------------------
# Correctness checks
# ---------------------------------------------------------------------------


def verify_correctness():
    """Compare outputs of both implementations on identical inputs."""
    random.seed(42)
    data = [(i, random.choice([0, 1, 2, 3])) for i in range(200)]

    a = DictTimeSeries(data, default=0)
    b = SortedDictTimeSeries(data, default=0)

    # check items
    assert a.items() == b.items(), "items() mismatch"

    # check get at various points
    for t in [-10, 0, 50, 99.5, 150, 199, 250]:
        va, vb = a.get(t), b.get(t)
        assert va == vb, f"get({t}) mismatch: {va} vs {vb}"

    # check iterperiods
    periods_a = list(a.iterperiods(10, 50))
    periods_b = list(b.iterperiods(10, 50))
    assert periods_a == periods_b, "iterperiods mismatch"

    # check distribution
    dist_a = a.distribution(10, 100)
    dist_b = b.distribution(10, 100)
    assert dist_a == dist_b, f"distribution mismatch: {dist_a} vs {dist_b}"

    # check set_interval
    a.set_interval(20, 40, 99)
    b.set_interval(20, 40, 99)
    assert a.items() == b.items(), "set_interval mismatch"

    # check n_points
    assert a.n_points(10, 50) == b.n_points(10, 50), "n_points mismatch"

    # check compact
    data2 = [(0, 1), (1, 1), (2, 1), (3, 2), (4, 2), (5, 3)]
    c = DictTimeSeries(data2)
    d = SortedDictTimeSeries(data2)
    c.compact()
    d.compact()
    assert c.items() == d.items(), "compact mismatch"

    # check delete
    e = DictTimeSeries([(0, 0), (1, 1), (2, 2)])
    f = SortedDictTimeSeries([(0, 0), (1, 1), (2, 2)])
    del e[1]
    del f[1]
    assert e.items() == f.items(), "delete mismatch"

    # check set_many (bulk insert into existing series)
    g = DictTimeSeries([(0, 0), (10, 10)], default=0)
    h = SortedDictTimeSeries([(0, 0), (10, 10)], default=0)
    new_data = [(5, 5), (3, 3), (7, 7), (10, 99)]
    g.set_many(new_data)
    h.set_many(new_data)
    assert g.items() == h.items(), "set_many mismatch"

    # check merge (simple vs priority-queue)
    op = sum
    for Cls in [DictTimeSeries, SortedDictTimeSeries]:
        ts1 = Cls([(0, 1), (5, 2), (10, 3)], default=0)
        ts2 = Cls([(0, 10), (3, 20), (7, 30)], default=0)
        ts3 = Cls([(2, 100), (8, 200)], default=0)
        r_simple = merge_simple([ts1, ts2, ts3], operation=op)
        r_pq = merge_pq([ts1, ts2, ts3], operation=op)
        assert r_simple.items() == r_pq.items(), (
            f"merge mismatch for {Cls.__name__}: "
            f"{r_simple.items()} vs {r_pq.items()}"
        )

    print("All correctness checks passed.")


# ---------------------------------------------------------------------------
# Benchmark harness
# ---------------------------------------------------------------------------


def bench(description, setup, stmt_dict, stmt_sorted, number=None, repeat=3):
    """Run a benchmark comparing dict vs SortedDict implementations.

    Returns (dict_time, sorted_time) in seconds (best of `repeat`).
    """
    # auto-calibrate number of iterations if not given
    if number is None:
        # try to get ~0.1s per run
        for trial_number in [1, 10, 100, 1000, 10000]:
            t = timeit.timeit(stmt_dict, setup, number=trial_number)
            if t > 0.05:
                number = trial_number
                break
        else:
            number = trial_number

    times_dict = timeit.repeat(stmt_dict, setup, number=number, repeat=repeat)
    times_sorted = timeit.repeat(
        stmt_sorted, setup, number=number, repeat=repeat
    )

    best_dict = min(times_dict) / number
    best_sorted = min(times_sorted) / number
    return best_dict, best_sorted


def run_benchmarks():
    sizes = [10, 100, 1_000, 10_000, 100_000]

    benchmarks = []

    for n in sizes:
        print(f"\n{'='*60}")
        print(f"  N = {n:,}")
        print(f"{'='*60}")

        results = []

        # --- Build incrementally ---
        setup = f"""
import random
from __main__ import DictTimeSeries, SortedDictTimeSeries
random.seed(0)
times = [random.random() * {n} for _ in range({n})]
values = [random.randint(0, 10) for _ in range({n})]
"""
        stmt_dict = """
ts = DictTimeSeries(default=0)
for t, v in zip(times, values):
    ts.set(t, v)
"""
        stmt_sorted = """
ts = SortedDictTimeSeries(default=0)
for t, v in zip(times, values):
    ts.set(t, v)
"""
        d, s = bench("Build incrementally", setup, stmt_dict, stmt_sorted)
        results.append(("Build incrementally", d, s))

        # --- Build with set_many ---
        setup_set_many = f"""
import random
from __main__ import DictTimeSeries, SortedDictTimeSeries
random.seed(0)
times = [random.random() * {n} for _ in range({n})]
values = [random.randint(0, 10) for _ in range({n})]
pairs = list(zip(times, values))
"""
        stmt_dict = """
ts = DictTimeSeries(default=0)
ts.set_many(pairs)
"""
        stmt_sorted = """
ts = SortedDictTimeSeries(default=0)
ts.set_many(pairs)
"""
        d, s = bench(
            "Build w/ set_many", setup_set_many, stmt_dict, stmt_sorted
        )
        results.append(("Build w/ set_many", d, s))

        # --- Build from data ---
        setup = f"""
import random
from __main__ import DictTimeSeries, SortedDictTimeSeries
random.seed(0)
data = [(random.random() * {n}, random.randint(0, 10)) for _ in range({n})]
"""
        stmt_dict = "ts = DictTimeSeries(data, default=0)"
        stmt_sorted = "ts = SortedDictTimeSeries(data, default=0)"
        d, s = bench("Build from data", setup, stmt_dict, stmt_sorted)
        results.append(("Build from data", d, s))

        # --- Random lookups ---
        setup = f"""
import random
from __main__ import DictTimeSeries, SortedDictTimeSeries
random.seed(0)
data = [(i, random.randint(0, 10)) for i in range({n})]
ts_dict = DictTimeSeries(data, default=0)
ts_sorted = SortedDictTimeSeries(data, default=0)
lookup_times = [random.random() * {n} for _ in range({n})]
"""
        stmt_dict = """
for t in lookup_times:
    ts_dict.get(t)
"""
        stmt_sorted = """
for t in lookup_times:
    ts_sorted.get(t)
"""
        d, s = bench("Random lookups", setup, stmt_dict, stmt_sorted)
        results.append(("Random lookups", d, s))

        # --- Iterate all periods ---
        setup = f"""
import random
from __main__ import DictTimeSeries, SortedDictTimeSeries
random.seed(0)
data = [(i, random.randint(0, 10)) for i in range({n})]
ts_dict = DictTimeSeries(data, default=0)
ts_sorted = SortedDictTimeSeries(data, default=0)
"""
        stmt_dict = "list(ts_dict.iterperiods(0, %d))" % (n - 1)
        stmt_sorted = "list(ts_sorted.iterperiods(0, %d))" % (n - 1)
        d, s = bench("Iterate all periods", setup, stmt_dict, stmt_sorted)
        results.append(("Iterate all periods", d, s))

        # --- Distribution ---
        stmt_dict = "ts_dict.distribution(0, %d)" % (n - 1)
        stmt_sorted = "ts_sorted.distribution(0, %d)" % (n - 1)
        d, s = bench("Distribution", setup, stmt_dict, stmt_sorted)
        results.append(("Distribution", d, s))

        # --- Set interval ---
        n_intervals = max(1, n // 10)
        setup_intervals = f"""
import random
from __main__ import DictTimeSeries, SortedDictTimeSeries
random.seed(0)
data = [(i, random.randint(0, 10)) for i in range({n})]
intervals = []
for _ in range({n_intervals}):
    a = random.randint(0, {n} - 2)
    b = random.randint(a + 1, {n} - 1)
    intervals.append((a, b, random.randint(0, 10)))
"""
        stmt_dict = """
ts = DictTimeSeries(data, default=0)
for s, e, v in intervals:
    ts.set_interval(s, e, v)
"""
        stmt_sorted = """
ts = SortedDictTimeSeries(data, default=0)
for s, e, v in intervals:
    ts.set_interval(s, e, v)
"""
        d, s = bench("Set interval", setup_intervals, stmt_dict, stmt_sorted)
        results.append(("Set interval", d, s))

        # --- Mixed workload ---
        setup_mixed = f"""
import random
from __main__ import DictTimeSeries, SortedDictTimeSeries
random.seed(0)
data = [(i, random.randint(0, 10)) for i in range({n})]
ops = []
for _ in range({n}):
    if random.random() < 0.5:
        ops.append(('set', random.random() * {n}, random.randint(0, 10)))
    else:
        ops.append(('get', random.random() * {n}, None))
"""
        stmt_dict = """
ts = DictTimeSeries(data, default=0)
for op, t, v in ops:
    if op == 'set':
        ts.set(t, v)
    else:
        ts.get(t)
"""
        stmt_sorted = """
ts = SortedDictTimeSeries(data, default=0)
for op, t, v in ops:
    if op == 'set':
        ts.set(t, v)
    else:
        ts.get(t)
"""
        d, s = bench("Mixed workload", setup_mixed, stmt_dict, stmt_sorted)
        results.append(("Mixed workload", d, s))

        # --- Print table ---
        print()
        header = f"{'Benchmark':<25} {'dict+list':>12} {'SortedDict':>12} {'Speedup':>10}"
        print(header)
        print("-" * len(header))
        for name, dt, st in results:
            speedup = st / dt if dt > 0 else float("inf")

            # format times nicely
            def fmt_time(t):
                if t < 1e-6:
                    return f"{t*1e9:.1f} ns"
                elif t < 1e-3:
                    return f"{t*1e6:.1f} us"
                elif t < 1:
                    return f"{t*1e3:.1f} ms"
                else:
                    return f"{t:.2f} s"

            marker = "<--" if speedup > 1 else ""
            print(
                f"{name:<25} {fmt_time(dt):>12} {fmt_time(st):>12} {speedup:>8.2f}x {marker}"
            )

        benchmarks.append((n, results))

    # --- Summary ---
    print(f"\n\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    print(
        f"\n{'Benchmark':<25}",
        "  ".join(f"{'N='+str(n):>12}" for n, _ in benchmarks),
    )
    print("-" * (25 + 14 * len(benchmarks)))
    bench_names = [name for name, _, _ in benchmarks[0][1]]
    for bname in bench_names:
        row = f"{bname:<25}"
        for _n, results in benchmarks:
            for name, dt, st in results:
                if name == bname:
                    speedup = st / dt if dt > 0 else float("inf")
                    row += f"  {speedup:>10.2f}x"
                    break
        print(row)


def bench_merge(
    description, setup, stmt_simple, stmt_pq, number=None, repeat=3
):
    """Run a benchmark comparing simple vs pq merge.

    Returns (simple_time, pq_time) in seconds (best of `repeat`).
    """
    if number is None:
        for trial_number in [1, 10, 100, 1000, 10000]:
            t = timeit.timeit(stmt_simple, setup, number=trial_number)
            if t > 0.05:
                number = trial_number
                break
        else:
            number = trial_number

    times_simple = timeit.repeat(
        stmt_simple, setup, number=number, repeat=repeat
    )
    times_pq = timeit.repeat(stmt_pq, setup, number=number, repeat=repeat)

    best_simple = min(times_simple) / number
    best_pq = min(times_pq) / number
    return best_simple, best_pq


def run_merge_benchmarks():
    print(f"\n\n{'#'*60}")
    print("  MERGE BENCHMARKS")
    print(f"{'#'*60}")

    all_results = []

    # Scenario 1: Few series, varying points per series
    for K, N in [(2, 100), (2, 1000), (2, 10000), (5, 1000), (5, 10000)]:
        label = f"{K} series x {N} pts"
        setup = f"""
import random
from __main__ import DictTimeSeries, merge_simple, merge_pq
random.seed(0)
ts_list = []
for _ in range({K}):
    data = [(random.random() * {N}, random.randint(0, 10)) for _ in range({N})]
    ts_list.append(DictTimeSeries(data, default=0))
op = sum
"""
        stmt_simple = "merge_simple(ts_list, operation=op)"
        stmt_pq = "merge_pq(ts_list, operation=op)"
        s, p = bench_merge(label, setup, stmt_simple, stmt_pq)
        all_results.append((label, s, p))

    # Scenario 2: Many small series (the "thousands of 1-2 point series" case)
    for K in [10, 50, 100, 500, 1000, 5000]:
        N = 2  # each series has just 2 points
        label = f"{K} series x {N} pts"
        setup = f"""
import random
from __main__ import DictTimeSeries, merge_simple, merge_pq
random.seed(0)
ts_list = []
for i in range({K}):
    t = random.random() * 1000
    ts_list.append(DictTimeSeries([(t, 1), (t + random.random() * 10, 0)], default=0))
op = sum
"""
        stmt_simple = "merge_simple(ts_list, operation=op)"
        stmt_pq = "merge_pq(ts_list, operation=op)"
        s, p = bench_merge(label, setup, stmt_simple, stmt_pq)
        all_results.append((label, s, p))

    # Print table
    print()
    header = (
        f"{'Scenario':<25} {'simple':>12} {'pq':>12} {'simple speedup':>15}"
    )
    print(header)
    print("-" * len(header))
    for label, st, pt in all_results:
        speedup = pt / st if st > 0 else float("inf")

        def fmt_time(t):
            if t < 1e-6:
                return f"{t*1e9:.1f} ns"
            elif t < 1e-3:
                return f"{t*1e6:.1f} us"
            elif t < 1:
                return f"{t*1e3:.1f} ms"
            else:
                return f"{t:.2f} s"

        marker = "<--" if speedup > 1 else ""
        print(
            f"{label:<25} {fmt_time(st):>12} {fmt_time(pt):>12} {speedup:>13.2f}x {marker}"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Verifying correctness...")
    verify_correctness()

    print("\nRunning benchmarks...")
    run_benchmarks()

    run_merge_benchmarks()
