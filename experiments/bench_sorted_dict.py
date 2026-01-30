"""Benchmark: traces built-in SortedDict vs sortedcontainers.SortedDict.

Compares performance of TimeSeries operations using the lightweight
built-in SortedDict (dict + sorted list + bisect) against the
sortedcontainers.SortedDict implementation.

Run standalone:
    python experiments/bench_sorted_dict.py
"""

import timeit

import traces
import traces.timeseries as ts_module

try:
    import sortedcontainers

    HAS_SORTEDCONTAINERS = True
except ImportError:
    HAS_SORTEDCONTAINERS = False


def bench(setup, stmt_local, stmt_sc, number=None, repeat=3):
    """Run a benchmark. Returns (local_time, sc_time) per iteration."""
    if number is None:
        for trial_number in [1, 10, 100, 1000, 10000]:
            t = timeit.timeit(stmt_local, setup, number=trial_number)
            if t > 0.05:
                number = trial_number
                break
        else:
            number = trial_number

    times_local = timeit.repeat(stmt_local, setup, number=number, repeat=repeat)
    times_sc = timeit.repeat(stmt_sc, setup, number=number, repeat=repeat)
    return min(times_local) / number, min(times_sc) / number


def fmt_time(t):
    if t < 1e-6:
        return f"{t*1e9:.1f} ns"
    elif t < 1e-3:
        return f"{t*1e6:.1f} us"
    elif t < 1:
        return f"{t*1e3:.1f} ms"
    else:
        return f"{t:.2f} s"


def run_benchmarks():
    if not HAS_SORTEDCONTAINERS:
        print("sortedcontainers is not installed, cannot compare.")
        return

    # Verify the patching actually works
    from traces.sorted_dict import SortedDict as LocalSortedDict

    original = ts_module.SortedDict
    assert original is LocalSortedDict, "expected local SortedDict"

    ts_module.SortedDict = sortedcontainers.SortedDict
    ts_sc = traces.TimeSeries([(1, "a")], default=0)
    ts_module.SortedDict = original
    ts_local = traces.TimeSeries([(1, "a")], default=0)

    print(
        f"Verify: local _d type = {type(ts_local._d).__module__}.{type(ts_local._d).__name__}"
    )
    print(
        f"Verify: sc    _d type = {type(ts_sc._d).__module__}.{type(ts_sc._d).__name__}"
    )
    assert (
        "sortedcontainers" in type(ts_sc._d).__module__
    ), f"Patching failed: sc _d is {type(ts_sc._d)}"
    assert (
        "traces" in type(ts_local._d).__module__
    ), f"Patching failed: local _d is {type(ts_local._d)}"
    print("Patching verified.\n")

    sizes = [100, 1_000, 10_000, 100_000]

    all_benchmarks = []

    for n in sizes:
        print(f"\n{'='*70}")
        print(f"  N = {n:,}")
        print(f"{'='*70}")

        results = []

        # The key insight: timeseries.py does `from .sorted_dict import SortedDict`
        # which binds `SortedDict` in the `traces.timeseries` module namespace.
        # We patch `traces.timeseries.SortedDict` to swap implementations.
        common_setup = """
import random, datetime
import traces
import traces.timeseries as ts_module
import sortedcontainers
from traces.sorted_dict import SortedDict as LocalSortedDict

_Original = ts_module.SortedDict

def make_local_ts(*args, **kwargs):
    ts_module.SortedDict = LocalSortedDict
    ts = traces.TimeSeries(*args, **kwargs)
    ts_module.SortedDict = _Original
    return ts

def make_sc_ts(*args, **kwargs):
    ts_module.SortedDict = sortedcontainers.SortedDict
    ts = traces.TimeSeries(*args, **kwargs)
    ts_module.SortedDict = _Original
    return ts

random.seed(42)
"""

        # --- Build from data (numeric keys) ---
        setup = (
            common_setup
            + f"""
data = [(random.random() * {n}, random.randint(0, 10)) for _ in range({n})]
"""
        )
        stmt_local = "make_local_ts(data, default=0)"
        stmt_sc = "make_sc_ts(data, default=0)"
        lo, sc = bench(setup, stmt_local, stmt_sc)
        results.append(("Build from data (numeric)", lo, sc))

        # --- Build from data (datetime keys) ---
        setup = (
            common_setup
            + f"""
base = datetime.datetime(2020, 1, 1)
data = [(base + datetime.timedelta(seconds=random.random() * 86400 * 30),
         random.randint(0, 10)) for _ in range({n})]
"""
        )
        stmt_local = "make_local_ts(data, default=0)"
        stmt_sc = "make_sc_ts(data, default=0)"
        lo, sc = bench(setup, stmt_local, stmt_sc)
        results.append(("Build from data (datetime)", lo, sc))

        # --- Build incrementally ---
        setup = (
            common_setup
            + f"""
times = [random.random() * {n} for _ in range({n})]
values = [random.randint(0, 10) for _ in range({n})]
"""
        )
        stmt_local = """
ts = make_local_ts(default=0)
for t, v in zip(times, values):
    ts[t] = v
"""
        stmt_sc = """
ts = make_sc_ts(default=0)
for t, v in zip(times, values):
    ts[t] = v
"""
        lo, sc = bench(setup, stmt_local, stmt_sc)
        results.append(("Build incrementally", lo, sc))

        # --- Build with set_many ---
        setup_set_many = (
            common_setup
            + f"""
pairs = list(zip(
    [random.random() * {n} for _ in range({n})],
    [random.randint(0, 10) for _ in range({n})],
))
"""
        )
        stmt_local = """
ts = make_local_ts(default=0)
ts.set_many(pairs)
"""
        stmt_sc = """
ts = make_sc_ts(default=0)
ts.set_many(pairs)
"""
        lo, sc = bench(setup_set_many, stmt_local, stmt_sc)
        results.append(("Build w/ set_many", lo, sc))

        # --- Random lookups (get/interpolation) ---
        setup = (
            common_setup
            + f"""
data = [(i, random.randint(0, 10)) for i in range({n})]
ts_local = make_local_ts(data, default=0)
ts_sc = make_sc_ts(data, default=0)
lookup_times = [random.random() * {n} for _ in range({n})]
"""
        )
        stmt_local = """
for t in lookup_times:
    ts_local.get(t)
"""
        stmt_sc = """
for t in lookup_times:
    ts_sc.get(t)
"""
        lo, sc = bench(setup, stmt_local, stmt_sc)
        results.append(("Random lookups", lo, sc))

        # --- iterperiods ---
        setup = (
            common_setup
            + f"""
data = [(i, random.randint(0, 10)) for i in range({n})]
ts_local = make_local_ts(data, default=0)
ts_sc = make_sc_ts(data, default=0)
"""
        )
        stmt_local = f"list(ts_local.iterperiods(0, {n - 1}))"
        stmt_sc = f"list(ts_sc.iterperiods(0, {n - 1}))"
        lo, sc = bench(setup, stmt_local, stmt_sc)
        results.append(("Iterate all periods", lo, sc))

        # --- distribution ---
        stmt_local = f"ts_local.distribution(0, {n - 1})"
        stmt_sc = f"ts_sc.distribution(0, {n - 1})"
        lo, sc = bench(setup, stmt_local, stmt_sc)
        results.append(("Distribution", lo, sc))

        # --- set_interval ---
        n_intervals = max(1, n // 10)
        setup_si = (
            common_setup
            + f"""
data = [(i, random.randint(0, 10)) for i in range({n})]
intervals = []
for _ in range({n_intervals}):
    a = random.randint(0, {n} - 2)
    b = random.randint(a + 1, {n} - 1)
    intervals.append((a, b, random.randint(0, 10)))
"""
        )
        stmt_local = """
ts = make_local_ts(data, default=0)
for s, e, v in intervals:
    ts.set_interval(s, e, v)
"""
        stmt_sc = """
ts = make_sc_ts(data, default=0)
for s, e, v in intervals:
    ts.set_interval(s, e, v)
"""
        lo, sc = bench(setup_si, stmt_local, stmt_sc)
        results.append(("Set interval", lo, sc))

        # --- Print table ---
        print()
        header = (
            f"{'Benchmark':<30} {'built-in':>12} {'sortedctnrs':>12}"
            f" {'ratio':>10}"
        )
        print(header)
        print("-" * len(header))
        for name, lo_t, sc_t in results:
            ratio = sc_t / lo_t if lo_t > 0 else float("inf")
            winner = (
                "<- built-in"
                if ratio > 1.1
                else "<- sortedctnrs"
                if ratio < 0.9
                else ""
            )
            print(
                f"{name:<30} {fmt_time(lo_t):>12} {fmt_time(sc_t):>12}"
                f" {ratio:>8.2f}x {winner}"
            )

        all_benchmarks.append((n, results))

    # --- Summary table ---
    print(f"\n\n{'='*70}")
    print("  SUMMARY (ratio = sortedcontainers time / built-in time)")
    print(
        "  >1x means built-in is faster, <1x means sortedcontainers is faster"
    )
    print(f"{'='*70}")

    size_headers = "  ".join(f"{'N='+str(n):>12}" for n, _ in all_benchmarks)
    print(f"\n{'Benchmark':<30} {size_headers}")
    print("-" * (30 + 14 * len(all_benchmarks)))

    bench_names = [name for name, _, _ in all_benchmarks[0][1]]
    for bname in bench_names:
        row = f"{bname:<30}"
        for _n, results in all_benchmarks:
            for name, lo_t, sc_t in results:
                if name == bname:
                    ratio = sc_t / lo_t if lo_t > 0 else float("inf")
                    row += f"  {ratio:>10.2f}x"
                    break
        print(row)


if __name__ == "__main__":
    print("Benchmarking TimeSeries with built-in SortedDict")
    print("vs sortedcontainers.SortedDict")
    print()
    run_benchmarks()
