.. _merge_strategies:

Merge implementation strategies
===============================

Merging multiple TimeSeries is one of the most important operations in
traces. Given K TimeSeries with N total measurement points across all
of them, the merge produces a single TimeSeries where each value is a
list of all the input values at that time (or a function of all the
values if `operation` is given).

As a concrete example, consider two TimeSeries tracking whether a light
is on (1) or off (0):

.. code-block:: python

    >>> a = TimeSeries(default=0)
    >>> a[1] = 1
    >>> a[3] = 0

    >>> b = TimeSeries(default=0)
    >>> b[2] = 1
    >>> b[4] = 0

Without an operation, merge produces a TimeSeries where each value is
a list of the states of all inputs at that time:

.. code-block:: python

    >>> merged = TimeSeries.merge([a, b])
    >>> for t, v in merged:
    ...     print(t, v)
    1 [1, 0]
    2 [1, 1]
    3 [0, 1]
    4 [0, 0]

With ``operation=sum``, the list is reduced to a single value — here,
the count of lights that are on:

.. code-block:: python

    >>> count = TimeSeries.merge([a, b], operation=sum)
    >>> for t, v in count:
    ...     print(t, v)
    1 1
    2 2
    3 1
    4 0

The core challenge is iterating through all transitions in time order
while tracking the current state of each input series. There are
several ways to do this, each with different performance
characteristics. This page describes three approaches and their
tradeoffs.

This is useful context for reimplementing merge in another language —
the right choice depends on the expected workload.

The three approaches
--------------------

1. Naive (collect-keys)
~~~~~~~~~~~~~~~~~~~~~~~

The simplest approach: collect all unique measurement times across all
K series, then at each time, query every series for its value.

.. code-block:: python

    def naive_iter_merge(timeseries_list):
        # Collect all unique measurement times
        all_times = set()
        for ts in timeseries_list:
            for t, _v in ts:
                all_times.add(t)

        # At each time, query every series
        for t in sorted(all_times):
            yield t, [ts[t] for ts in timeseries_list]

**How it works:** Build a set of all times (O(N)), sort them (O(N log N)),
then for each of the T unique times, look up the value in each of the K
series via binary search (O(log N) per lookup).

**Complexity:** O(N log N + T × K × log N) time, O(T × K) memory for the
output state lists.

**Pros:**

- Dead simple to implement and understand.
- No auxiliary data structures beyond a set and a sorted list.
- Easy to port to any language — uses only sets, sorted arrays, and
  binary search.

**Cons:**

- Performs K binary searches at every unique time, even when only one
  series changed. This is the dominant cost: for K=1000 with 2
  transitions each, there are ~2000 unique times and each requires
  1000 lookups — 2 million binary searches total.
- Scales poorly with K. At K=1000, this approach is **40× slower**
  than the alternatives (see benchmarks below).

**When to use it:** For small K (under ~20 series) where simplicity
matters more than performance, or as a reference implementation for
testing.

This was the first approach used by the `traces JavaScript implementation
<https://github.com/stringertheory/traces-js>`_:

.. code-block:: javascript

    function merge(traceList, operation = (d) => d) {
      let keys = new Set(traceList.map((d) => d.list).flat());
      let result = new Trace([], operation(traceList.map((d) => d.defaultValue)));
      for (let k of keys) {
        result.set(k, operation(traceList.map((d) => d.get(k))));
      }
      return result;
    }

2. Priority queue (heap merge)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use a min-heap to perform a K-way merge of the pre-sorted input series.
Each series contributes an iterator; the heap always contains the next
upcoming transition from each active series.

.. code-block:: python

    import heapq

    def heapq_iter_merge_transitions(timeseries_list):
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

**How it works:** The heap holds at most K entries (one per series).
Each ``heappop`` yields the next transition in time order. After
processing a transition, the next value from that series is pushed
back onto the heap.

**Complexity:** O(N log K) time (each of N transitions requires one
heap push and one heap pop, each O(log K)). O(K) memory for the heap
plus K iterator objects.

**Pros:**

- Only processes actual transitions, never queries a series that
  didn't change.
- Streaming: produces transitions lazily without materializing all
  data up front.

**Cons:**

- Each heap operation has Python function call overhead (``heapq.heappush``
  and ``heapq.heappop`` are C functions, but each call crosses the
  Python/C boundary).
- Maintains K live iterator objects in memory for the duration of the merge.
- For small K, the log K advantage over flat sort's log N is negligible,
  and the per-element overhead is higher.

**When to use it:** When N per series is very large (tens of thousands
or more) and K is small — the heap avoids materializing all N triples
and uses significantly less memory (see benchmarks). Also the right
choice when the input series are streams (e.g. reading from files or
network sources) rather than in-memory data, since it produces
transitions lazily without buffering.

**Note on thread-safe wrappers:** Python's ``queue.PriorityQueue`` wraps
``heapq`` with a threading lock, adding acquire/release overhead on every
push and pop. For single-threaded merge, use ``heapq`` directly.

3. Flat sort (extract and sort)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Extract all (time, index, value) triples from every series into a single
list, sort it once, then iterate linearly.

.. code-block:: python

    def flat_sort_iter_merge_transitions(timeseries_list):
        triples = []
        for index, ts in enumerate(timeseries_list):
            for t, v in ts:
                triples.append((t, index, v))
        triples.sort()

        state = [ts.default for ts in timeseries_list]
        for t, index, next_value in triples:
            previous_value = state[index]
            state[index] = next_value
            yield t, index, previous_value, next_value

**How it works:** Flattening all transitions into a single list and sorting
turns the K-way merge into a standard sort problem. The subsequent
iteration is a simple linear scan with no function call overhead per
element (no ``heappush``/``heappop``).

**Complexity:** O(N log N) time for the sort, O(N) memory for the
triples list. The log N factor is theoretically worse than the priority
queue's log K, but in practice timsort's lower constant factor wins for
most workloads.

**Pros:**

- Fastest in practice for in-memory data (see benchmarks).
- No iterator objects or heap — just a flat list of tuples.
- Python's timsort exploits existing order within each series'
  contribution, performing well on the partially-sorted input.

**Cons:**

- Materializes all transitions at once. Not suitable for streaming
  inputs that don't fit in memory.
- O(N) memory for the triples list (though this is typically small
  compared to the TimeSeries objects themselves).

**When to use it:** For in-memory data, which is the common case.
This is the current default in traces.

This is what traces uses as of version 0.7.
Performance characteristics are discussed below and benchmarks can be
reproduced via ``python experiments/bench_merge_strategies.py``.

Benchmarks
----------

All benchmarks on a 2021 Apple M1 MacBook Pro, Python 3.12, minimum of
3 runs. Series values are integers; operation is ``sum``.

Many series, few transitions per series
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is the "light switch" or "ticket open/close" pattern: many boolean
or categorical series with only a few state changes each. Each series
has 2 transitions, so N (total transitions) = K × 2.

These benchmarks call ``merge(operation=sum)``, which goes through
``iter_merge`` and copies the full K-element state list at each yield.

.. list-table::
   :header-rows: 1
   :widths: 10 10 20 20 20

   * - K
     - N total
     - Naive
     - Priority queue
     - Flat sort
   * - 10
     - 20
     - 0.1 ms / 4 KB
     - 0.1 ms / 5 KB
     - 0.1 ms / 4 KB
   * - 50
     - 100
     - 1.8 ms / 14 KB
     - 0.3 ms / 18 KB
     - 0.3 ms / 13 KB
   * - 100
     - 200
     - 6.6 ms / 19 KB
     - 0.7 ms / 29 KB
     - 0.6 ms / 20 KB
   * - 500
     - 1,000
     - 150 ms / 81 KB
     - 6.0 ms / 172 KB
     - 5.1 ms / 119 KB
   * - 1,000
     - 2,000
     - 588 ms / 234 KB
     - 17.7 ms / 300 KB
     - 15.3 ms / 213 KB

At K=1000, the naive approach is **38× slower** than flat sort. The
naive approach's cost is dominated by performing K binary searches at
each of the ~2000 unique times (2 million lookups). The priority queue
and flat sort appear close here, with flat sort ~15% faster — but this
understates the difference (see "Consuming transitions directly" below
for why).

Few series, many transitions per series
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These benchmarks also call ``merge(operation=sum)``. N/series is
the number of transitions per series; N total = K × N/series.

.. list-table::
   :header-rows: 1
   :widths: 8 10 10 20 20 20

   * - K
     - N/series
     - N total
     - Naive
     - Priority queue
     - Flat sort
   * - 2
     - 100
     - 200
     - 0.5 ms / 25 KB
     - 0.4 ms / 18 KB
     - 0.4 ms / 18 KB
   * - 2
     - 1,000
     - 2,000
     - 8.6 ms / 263 KB
     - 6.2 ms / 138 KB
     - 5.9 ms / 136 KB
   * - 5
     - 100
     - 500
     - 2.2 ms / 67 KB
     - 1.3 ms / 36 KB
     - 1.3 ms / 35 KB
   * - 5
     - 1,000
     - 5,000
     - 35 ms / 790 KB
     - 16.9 ms / 448 KB
     - 16.4 ms / 468 KB

With small K, all three approaches are closer in speed. The naive
approach is still 1.5–2× slower due to the redundant binary searches.
The priority queue and flat sort are nearly identical here — with K=5,
the heap holds only 5 entries and log K is tiny.

iter_merge memory (full state lists)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``iter_merge`` yields ``(time, list_of_all_values)`` at each unique time.
Regardless of strategy, this requires copying a K-element list at each
yield. For large K, this copy dominates memory. Each series has 2
transitions (N total = K × 2).

.. list-table::
   :header-rows: 1
   :widths: 10 10 20 20 20

   * - K
     - N total
     - Naive
     - Priority queue
     - Flat sort
   * - 100
     - 200
     - 6.4 ms / 192 KB
     - 0.5 ms / 174 KB
     - 0.3 ms / 174 KB
   * - 500
     - 1,000
     - 150 ms / 4.1 MB
     - 3.2 ms / 3.9 MB
     - 3.1 ms / 4.0 MB
   * - 1,000
     - 2,000
     - 588 ms / 17.0 MB
     - 9.2 ms / 15.4 MB
     - 10.9 ms / 15.4 MB

The priority queue and flat sort look nearly identical here. This is
because the K-element list copies at each yield dominate both time and
memory, swamping the sort-vs-heap difference.

Consuming transitions directly (many series)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The flat sort advantage becomes clear when transitions are consumed
directly — without the O(K) list copy overhead. This is the pattern
used by ``count_by_value`` and any consumer that maintains its own
incremental state. Each series has 2 transitions (N total = K × 2).

.. list-table::
   :header-rows: 1
   :widths: 10 10 25 25

   * - K
     - N total
     - Priority queue
     - Flat sort
   * - 100
     - 200
     - 0.3 ms / 12 KB
     - 0.1 ms / 4 KB
   * - 500
     - 1,000
     - 1.7 ms / 82 KB
     - 0.8 ms / 24 KB
   * - 1,000
     - 2,000
     - 3.5 ms / 175 KB
     - 1.7 ms / 53 KB
   * - 5,000
     - 10,000
     - 25 ms / 1.8 MB
     - 13 ms / 0.9 MB

Flat sort is **2× faster** and uses **3× less memory** than the
priority queue when consuming transitions directly with many series.
The speed difference comes from timsort's cache-friendliness and lower
per-element overhead (no ``heappush``/``heappop`` calls per transition).
The memory difference comes from eliminating K iterator objects and
the 4-tuple heap entries (which include iterator references) in favor
of a flat list of 3-tuples.

This matters for ``count_by_value``: at K=10,000 with 2 transitions per
series, ``count_by_value`` runs in 0.16s with flat sort vs 0.22s with
a priority queue — a 27% improvement that comes entirely from the
underlying sort strategy.

Consuming transitions directly (few series, very many transitions)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

With few series and very many transitions per series (small K, large N),
the priority queue's O(N log K) advantage over flat sort's O(N log N)
should theoretically win. Does it?

.. list-table::
   :header-rows: 1
   :widths: 8 10 10 25 25

   * - K
     - N/series
     - N total
     - Priority queue
     - Flat sort
   * - 2
     - 10,000
     - 20,000
     - 14 ms / 1.3 MB
     - 14 ms / 1.9 MB
   * - 2
     - 50,000
     - 100,000
     - 73 ms / 6.1 MB
     - 81 ms / 9.8 MB
   * - 2
     - 100,000
     - 200,000
     - 149 ms / 12.1 MB
     - 161 ms / 19.7 MB
   * - 2
     - 500,000
     - 1,000,000
     - 765 ms / 61.2 MB
     - 833 ms / 99.6 MB
   * - 3
     - 50,000
     - 150,000
     - 86 ms / 9.2 MB
     - 121 ms / 13.3 MB

At K=2 with 1M total transitions, the priority queue is **~10% faster**
in time. But the real win is **memory**: the heap uses 61 MB vs flat
sort's 100 MB. This is because flat sort materializes all N triples
at once, while the heap only holds K=2 entries at any time. The
memory ratio approaches N/K as N grows.

At K=3 with 150k transitions, the heap is ~30% faster — the log K = 1.6
vs log N = 17.2 ratio starts to matter when N is large enough.

**The takeaway:** the priority queue wins on memory when N is large
relative to K, because it doesn't materialize the full triples list.
The speed advantage is modest (10–30%) and only appears at very high
N. For the common traces use case — many entities with few state
changes each (large K, small N per series) — flat sort is faster and
uses less memory.

**The lesson:** the choice between priority queue and flat sort matters
most when the consumer processes transitions directly. When the
consumer goes through ``iter_merge`` (which copies K-element lists),
the copy overhead dominates and the sort strategy barely matters.

Choosing an approach
--------------------

**Use flat sort** (the traces default) when the data is in memory.
It's the fastest approach for the common case and has no complex data
structures to implement — just a list, a sort, and a linear scan.

**Use a priority queue** when N per series is very large (tens of
thousands+) and K is small — the heap avoids materializing all N
triples in memory (61 MB vs 100 MB at K=2, N=1M). Also the right
choice when inputs are streams (data arriving over time, reading from
files) since it produces transitions lazily without buffering.

**Use the naive approach** for simplicity when K is small (under ~20)
and correctness matters more than performance. It's the easiest to
implement, test, and reason about. It's also a good reference
implementation for validating the other approaches.

Avoiding O(K) copies: transitions vs. full state
-------------------------------------------------

All three approaches above can yield either full state lists (what
``iter_merge`` does) or individual transitions (what
``iter_merge_transitions`` does). The choice affects downstream
consumers:

- **Full state lists** are convenient when the consumer needs the
  complete picture at each time (e.g., applying an arbitrary operation
  like ``sum`` over all K values). The cost is O(K) per yield for the
  list copy.

- **Transitions** yield O(1) per event and are better when the consumer
  can maintain its own state incrementally. ``count_by_value`` uses
  this: it keeps a ``{value: count}`` dict and adjusts two entries per
  transition (decrement the old value's count, increment the new
  value's count).

For K=1000 with 2 transitions each, ``iter_merge`` copies 2000 lists of
1000 elements (2M element copies, ~15 MB). ``iter_merge_transitions``
yields 2000 individual tuples (~0.2 MB for the triples list). The
algorithmic improvement is independent of which sort strategy is used.

Reproducing the benchmarks
--------------------------

You can reproduce these benchmarks by running::

    python experiments/bench_merge_strategies.py
