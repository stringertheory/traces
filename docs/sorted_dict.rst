.. _sorted_dict:

Internal sorted dictionary
==========================

Traces uses an internal ``SortedDict`` class (in ``traces.sorted_dict``)
to store the time-value pairs in a ``TimeSeries``. This is a lightweight
implementation built on Python's ``dict`` and ``bisect`` module, with no
external dependencies.

Previously, traces used ``sortedcontainers.SortedDict`` for this
purpose. The `sortedcontainers <https://grantjenks.com/docs/sortedcontainers/>`_
library is an excellent, well-tested, pure-Python library for sorted
data structures.

Design
------

The built-in ``SortedDict`` maintains two data structures:

- A Python ``dict`` for O(1) key-value lookups
- A sorted ``list`` of keys for ordered iteration and binary search via
  the ``bisect`` module

This design has different performance characteristics than
``sortedcontainers.SortedDict``, which uses a B-tree-like structure
(a list of sublists) that provides more balanced performance across
operations.

Performance comparison
----------------------

Benchmarks were run using the full ``TimeSeries`` API (not just raw
data structure operations), with data sizes from N=100 to N=100,000.
The ratio column shows ``sortedcontainers`` time divided by built-in
time, so values greater than 1x indicate the built-in is faster.

**Where the built-in SortedDict is faster:**

- **Random lookups**: 1.6--3.3x faster across all sizes. The built-in
  uses O(1) dict lookup when the key exists and falls back to
  ``bisect`` otherwise. This advantage grows with N.
- **Iterating periods and computing distributions**: 1.4--3.7x faster
  across all sizes. These operations iterate over sorted keys and
  look up values, benefiting from the same dict + bisect combination.
- **Set interval**: 3.3--4.5x faster across all sizes. The built-in
  uses a single list-slice deletion to remove a range of keys,
  while the ``sortedcontainers`` path deletes keys individually.
- **Building incrementally at small N** (under ~1,000): 1.3--1.5x
  faster due to lower per-operation overhead.

**Where sortedcontainers.SortedDict is faster:**

- **Building incrementally at large N**: At N=10,000,
  ``sortedcontainers`` is 1.6x faster; at N=100,000 it is 10x
  faster. The built-in uses ``bisect.insort``, which has O(n) cost
  per insertion due to list element shifting. ``sortedcontainers``
  uses a B-tree-like structure with O(log n) amortized insertions.
  This only applies to individual insertions (``ts[time] = value``
  in a loop); using ``set_many()`` avoids this penalty entirely.

**Where they are comparable:**

- **Building from data** and **building with set_many**: Within a
  few percent of each other at all sizes. Both paths use bulk
  insertion (``dict.update`` + ``sorted``) rather than per-element
  insertion.

Bulk insertion with set_many
----------------------------

``TimeSeries.set_many(data)`` accepts an iterable of ``(time, value)``
pairs or a dictionary, and inserts all points in a single operation.
This avoids the per-element ``bisect.insort`` cost that makes
individual insertions slow at large N::

    # Instead of this:
    for time, value in data:
        ts[time] = value

    # Use this:
    ts.set_many(data)

``set_many`` accepts generators, so data does not need to be
materialized into a list first. ``from_csv`` and ``from_json`` use
``set_many`` internally.

Choosing an implementation
--------------------------

The built-in ``SortedDict`` is a good default for most use cases.
Typical time series workloads involve loading data in bulk (from files,
databases, or lists of measurements) and then performing read
operations like lookups, ``distribution()``, or ``iterperiods()``.
The built-in is faster for all of these read operations.

``sortedcontainers.SortedDict`` is a better choice if your workload
involves building very large time series incrementally through many
individual, random-order insertions (e.g., more than 10,000 points
added one at a time) and you cannot use ``set_many()`` to batch them.

Reproducing the benchmarks
--------------------------

You can reproduce these benchmarks by running::

    python experiments/bench_sorted_dict.py
