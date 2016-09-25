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
measurement, you'll get the first measurement value.

.. code:: python

    >>> cart = traces.TimeSeries()
    >>> cart[-1]
    set(['broccoli'])

If, however, you set the default when creating the TimeSeries, you'll
get that instead:

.. code:: python

    >>> cart = traces.TimeSeries(default=set())
    >>> cart[-1]
    set([])

In this case, it might also make sense to add the t=0 point as a
measurement with :code:`cart[0] = set()`. If you know the time span
over which the measurements are taken and you want your code to break
if there is something out of that range, you can set a domain on the
TimeSeries.

.. code:: python

    >>> cart = traces.TimeSeries(domain=(0, 120))
    >>> cart[121]
    Traceback (most recent call last):
      File "bunga.py", line 4, in <module>
        cart[121]
      File "/Users/stringer/Projects/traces/traces/timeseries.py", line 772, in __getitem__
        return self.get(time)
      File "/Users/stringer/Projects/traces/traces/timeseries.py", line 124, in get
        raise KeyError(msg)
    KeyError: '121 is outside of the domain.'

Setting an explicit domain can help avoid pesky bugs with dirty sensor
data.
    
Performance note
++++++++++++++++

Traces is not designed for maximal performance, but it's no slouch
since it uses the excellent `sortedcontainers.SortedDict
<http://www.grantjenks.com/docs/sortedcontainers/introduction.html#sorteddict>`__
under the hood to store sparse time series.

.. autoclass:: traces.TimeSeries
    :members:

.. _domain:
       
Domain
------

.. autoclass:: traces.Domain
    :members:

.. _histogram:
       
Histogram
---------

.. autoclass:: traces.Histogram
    :members:

