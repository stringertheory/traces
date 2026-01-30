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
are primarily designed for evenly-spaced measurements. Also, in the
real world, time series have missing observations or you may have
multiple series with different frequencies: it's can be useful to
model these as unevenly-spaced.

.. include:: goals.rst

Traces was designed by the team at `Datascope
<https://en.wikipedia.org/wiki/Datascope_Analytics>`__ based on several practical
applications in different domains, because it turns out :doc:`unevenly-spaced data is actually pretty great, particularly for sensor data analysis <unevenly-spaced>`.

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
    >>> time_series[datetime(2042, 2, 1,  6,  0,  0)] = 0 #  6:00:00am
    >>> time_series[datetime(2042, 2, 1,  7, 45, 56)] = 1 #  7:45:56am
    >>> time_series[datetime(2042, 2, 1,  8, 51, 42)] = 0 #  8:51:42am
    >>> time_series[datetime(2042, 2, 1, 12,  3, 56)] = 1 # 12:03:56am
    >>> time_series[datetime(2042, 2, 1, 12,  7, 13)] = 0 # 12:07:13am

What if you want to know if the light was on at 11am? Unlike a
python dictionary, you can look up the value at any time even if it's
not one of the measurement times.

.. code:: python

    >>> time_series[datetime(2042, 2, 1, 11,  0, 0)] # 11:00am
    0

The ``distribution`` function gives you the fraction of time that the
``TimeSeries`` is in each state.

.. code:: python

    >>> time_series.distribution(
    >>>   start=datetime(2042, 2, 1,  6,  0,  0), # 6:00am
    >>>   end=datetime(2042, 2, 1,  13,  0,  0)   # 1:00pm
    >>> )
    Histogram({0: 0.8355952380952381, 1: 0.16440476190476191})

The light was on about 16% of the time between 6am and 1pm.

Adding more data...
+++++++++++++++++++

Now let's get a little more complicated and look at the sensor
readings from forty lights in a building.

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

How many lights are typically on during business hours, from 8am to
6pm?

.. code:: python

    >>> histogram = count.distribution(
    >>>   start=datetime(2042, 2, 1,  8,  0,  0),   # 8:00am
    >>>   end=datetime(2042, 2, 1,  12 + 6,  0,  0) # 6:00pm
    >>> )
    >>> histogram.median()
    17

The ``distribution`` function returns a :ref:`Histogram <histogram>`
that can be used to get summary metrics such as the mean or quantiles.

Tracking discrete events
+++++++++++++++++++++++

The traces library also provides an :ref:`EventSeries <eventseries>` class
for tracking discrete events that occur at specific times, like system
logins, errors, or customer interactions.

.. code:: python

    >>> logins = traces.EventSeries([
    ...     datetime(2042, 2, 1, 8, 15, 0),
    ...     datetime(2042, 2, 1, 9, 30, 0),
    ...     datetime(2042, 2, 1, 10, 45, 0),
    ... ])
    >>> logins.events_between(
    ...     datetime(2042, 2, 1, 8, 0, 0),
    ...     datetime(2042, 2, 1, 10, 0, 0)
    ... )
    2

EventSeries is especially useful for analyzing event frequencies, inter-event times,
and tracking active cases over time.

It's flexible
+++++++++++++

The measurements points (keys) in a ``TimeSeries`` can be in any units as
long as they can be ordered. The values can be anything.

For example, you can use a ``TimeSeries`` to keep track the contents
of a grocery basket by the number of minutes within a shopping trip.

.. code:: python

    >>> time_series = traces.TimeSeries()
    >>> time_series[1.2] = {'broccoli'}
    >>> time_series[1.7] = {'broccoli', 'apple'}
    >>> time_series[2.2] = {'apple'}          # puts broccoli back
    >>> time_series[3.5] = {'apple', 'beets'} # mmm, beets

To learn more, check the :ref:`examples <examples>` and the detailed
:ref:`reference <api>`.

More info
---------

.. toctree::
   :maxdepth: 2

   examples
   api_reference
   sorted_dict

Contributing
-------------

Contributions are welcome and greatly appreciated! Please visit `the
repository
<https://github.com/datascopeanalytics/traces/blob/master/CONTRIBUTING.md>`_
for more info.
