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

Visualizing Time Series
++++++++++++++++++++++

The TimeSeries class provides a :code:`plot()` method for easy visualization of your data:

.. code:: python

    >>> ts = traces.TimeSeries()
    >>> ts[0] = 0
    >>> ts[1] = 2
    >>> ts[3] = 1
    >>> ts[5] = 0
    >>>
    >>> # Create a basic plot with default settings
    >>> fig, ax = ts.plot()

You can customize the plot appearance with various parameters:

.. code:: python

    >>> # Create a plot with linear interpolation and custom styling
    >>> fig, ax = ts.plot(
    ...     interpolate="linear",  # Use linear interpolation between points
    ...     figure_width=10,       # Set figure width in inches
    ...     linewidth=2,           # Set line thickness
    ...     marker="s",            # Use square markers
    ...     markersize=5,          # Set marker size
    ...     color="#FF5733"        # Use custom color
    ... )

The plot method returns matplotlib objects that you can further customize or save to a file:

.. code:: python

    >>> # Add title and labels
    >>> ax.set_title("My Time Series Data")
    >>> ax.set_xlabel("Time")
    >>> ax.set_ylabel("Value")
    >>>
    >>> # Save the plot to a file
    >>> fig.savefig("my_timeseries.png")

.. autoclass:: traces.TimeSeries
    :members:

.. _histogram:

Histogram
---------

.. autoclass:: traces.Histogram
    :members:

.. _eventseries:

EventSeries
-----------

An EventSeries represents a sequence of events that occur at specific times.
Unlike TimeSeries which tracks measurements (values) over time, EventSeries
only tracks when events occur, without associated values.

.. code:: python

    >>> # Track website login events
    >>> logins = traces.EventSeries([
    ...     "2023-05-01 08:15",
    ...     "2023-05-01 09:30",
    ...     "2023-05-01 10:45",
    ...     "2023-05-01 12:00"
    ... ])

EventSeries is useful for analyzing:

* Event frequencies and patterns
* Time intervals between events
* Event counts within specific time ranges
* Active cases over time (like support tickets, hospital stays)

.. code:: python

    >>> # Count events in a time range
    >>> logins.events_between("2023-05-01 08:00", "2023-05-01 10:00")
    2

    >>> # Get cumulative count of events over time
    >>> cumulative = logins.cumulative_sum()
    >>> cumulative["2023-05-01 11:00"]
    3

.. autoclass:: traces.EventSeries
    :members:
