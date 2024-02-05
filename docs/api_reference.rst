.. _api:

API Reference
=============

.. _timeseries:

TimeSeries
----------

In traces, a TimeSeries is similar to a dictionary that contains
measurements of something at different times. One difference is that
you can ask for the value at any time -- it doesn't need to be at a
measurement time. Let's say you're measuring the contents of a grocery
cart by the number of minutes within a shopping trip.

.. code:: python

    >>> cart = traces.TimeSeries()
    >>> cart[1.2] = {'broccoli'}
    >>> cart[1.7] = {'broccoli', 'apple'}
    >>> cart[2.2] = {'apple'}
    >>> cart[3.5] = {'apple', 'beets'}

If you want to know what's in the cart at 2 minutes, you can simply
get the value using :code:`cart[2]` and you'll see :code:`{'broccoli',
'apple'}`. By default, if you ask for a time before the first
measurement, you'll get `None`.

.. code:: python

    >>> cart = traces.TimeSeries()
    >>> cart[-1]
    None

If, however, you set the default when creating the TimeSeries, you'll
get that instead:

.. code:: python

    >>> cart = traces.TimeSeries(default=set())
    >>> cart[-1]
    set([])

In this case, it might also make sense to add the t=0 point as a
measurement with :code:`cart[0] = set()`.

Performance note
++++++++++++++++

Traces is not designed for maximal performance, but it's no slouch
since it uses the excellent `sortedcontainers.SortedDict
<http://www.grantjenks.com/docs/sortedcontainers/introduction.html#sorteddict>`__
under the hood to store sparse time series.

.. autoclass:: traces.TimeSeries
    :members:

.. _histogram:

Histogram
---------

.. autoclass:: traces.Histogram
    :members:
