.. traces documentation master file, created by
   sphinx-quickstart on Tue Sep 20 09:46:11 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

traces
======

A Python library for unevenly-spaced time series analysis.

Why?
----

Taking measurements at irregular intervals is common, but most tools
for analyzing data over time are designed for regularly-spaced
measurements. It's a shame, because `unevenly-spaced data is actually
pretty great, particularly for sensor data analysis
<https://datascopeanalytics.com/blog/unevenly-spaced-time-series/>`_.

Traces aims to make it simple to:

-  read, write, and manipulate unevenly-spaced time series data
-  perform basic analyses of unevenly-spaced time series data without
   making an awkward / lossy transformation to evenly-spaced
   representations
-  gracefully transform unevenly-spaced times series data to
   evenly-spaced representations

Installation
------------

To install traces, run this command in your terminal:

.. code:: bash

    $ pip install traces
   
Quickstart: using traces
------------------------

To see a basic use of traces, let's look at these data from a light
switch, also known as *Big Data from the Internet of Things*.

.. figure:: _static/img/trace.svg
   :alt: light switch trace

The main object in traces is a :ref:`TimeSeries <timeseries>`, which
you create just like a dictionary, adding the five measurements at
6:00am, 7:45:56am, etc.

.. code:: python

    >>> time_series = traces.TimeSeries()
    >>> time_series[datetime(2042, 2, 1,  6,  0,  0)] = 0
    >>> time_series[datetime(2042, 2, 1,  7, 45, 56)] = 1
    >>> time_series[datetime(2042, 2, 1,  8, 51, 42)] = 0
    >>> time_series[datetime(2042, 2, 1, 12,  3, 56)] = 1
    >>> time_series[datetime(2042, 2, 1, 12,  7, 13)] = 0

What if you want to know if the light was on at 11am? Unlike a
python dictionary, you can look up the value at any time even if it's
not one of the measurement times.

.. code:: python

    >>> time_series[datetime(2042, 2, 1, 11,  0, 0)]
    0

The ``distribution`` function gives you the fraction of time that the
``TimeSeries`` is in each state.

.. code:: python

    >>> time_series.distribution(
    >>>   start_time=datetime(2042, 2, 1,  6,  0,  0),
    >>>   end_time=datetime(2042, 2, 1,  13,  0,  0)
    >>> )
    Histogram({0: 0.8355952380952381, 1: 0.16440476190476191})

The light was on about 16% of the time between 6am and 1pm.

Adding more data...
+++++++++++++++++++

Now let's get a little more complicated and look at the sensor
readings from forty lights in a house.

.. figure:: _static/img/traces.svg
   :alt: many light switch trace

How many lights are on throughout the day? The merge function takes
the forty individual ``TimeSeries`` and efficiently merges them into
one ``TimeSeries`` where the each value is a list of all lights.

.. code:: python

    >>> trace_list = [... list of forty traces.TimeSeries ...]
    >>> count = traces.TimeSeries.merge(trace_list, operation=sum)

We also applied a ``sum`` operation to the list of states to get the
``TimeSeries`` of the number of lights that are on.
    
.. figure:: _static/img/count.svg
   :alt: many light switch count

How many lights are on in the building on average during business hours,
from 8am to 6pm?

.. code:: python

    >>> histogram = count.distribution(
    >>>   start_time=datetime(2042, 2, 1,  8,  0,  0),
    >>>   end_time=datetime(2042, 2, 1,  12 + 6,  0,  0)
    >>> )
    >>> histogram.median()
    17

The ``distribution`` function returns a :ref:`Histogram <histogram>`
that can be used to get summary metrics such as the mean or quantiles.

It's flexible
+++++++++++++
   
The measurements points (keys) in a ``TimeSeries`` can be in any units as
long as they can be ordered. The values can be anything.

For example, you can use a ``TimeSeries`` to keep track the contents
of a grocery basket by the number of minutes within a shopping trip.

.. code:: python

    >>> time_series = traces.TimeSeries()
    >>> time_series[1.2] = set(['broccoli'])
    >>> time_series[1.4] = set(['broccoli', 'orange'])
    >>> time_series[1.7] = set(['broccoli', 'orange', 'banana'])
    >>> time_series[2.2] = set(['orange', 'banana'])
    >>> time_series[3.5] = set(['orange', 'banana', 'beets'])

This is just a few things that traces can do -- it's been designed to
by the team at `Datascope <https://datascopeanalytics.com/>`__ based on
several use cases in different application domains. To learn more,
check the :ref:`examples <examples>` and the detailed :ref:`reference
<api>`.

More info
---------

.. toctree::
   :maxdepth: 2

   examples
   api_reference

Contributing
-------------

Contributions are welcome and greatly appreciated! Please visit `the
repository
<https://github.com/datascopeanalytics/traces/blob/master/CONTRIBUTING.md>`_
for more info.
