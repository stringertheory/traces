import collections
import functools
import sys
import time

TIMING_RESULTS = collections.defaultdict(list)


class timer:
    def __call__(self, function):
        """Turn the object into a decorator"""

        @functools.wraps(function)
        def wrapper(*arg, **kwargs):
            t1 = time.clock()
            result = function(*arg, **kwargs)
            t2 = time.clock()
            TIMING_RESULTS[function.__name__].append(t2 - t1)
            return result

        return wrapper


def print_results(*args):
    args = sorted([f.__name__ for f in args])
    focus = set(args)
    result = {}
    for name, timing_results in sorted(TIMING_RESULTS.iteritems()):
        if name not in focus:
            continue
        n = 0
        sum_ = 0
        min_ = float("inf")
        max_ = float("-inf")
        for dt in timing_results:
            n += 1
            sum_ += dt
            if dt < min_:
                min_ = dt
            if dt > max_:
                max_ = dt
        avg = float(sum_) / n
        msg = f"{name}: n={n} avg={avg} min={min_} max={max_}"
        result[name] = {
            "n": n,
            "avg": avg,
            "min": min_,
            "max": min_,
        }
    for i, name_a in enumerate(args):
        for j in range(i):
            name_b = args[j]
            ratio = result[name_a]["min"] / result[name_b]["min"]
            if ratio <= 1:
                msg = f"{name_a} is {1 / ratio:.1f}x faster than {name_b}"
            else:
                msg = f"{name_b} is {ratio:.1f}x faster than {name_a}"
            print(msg, file=sys.stderr)

    return result


def timing_loop(n, mod=1000):
    for index, i in enumerate(range(n)):
        if not index % mod:
            print("iteration %i" % index, file=sys.stderr)
        yield i
