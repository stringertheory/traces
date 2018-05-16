.. _examples:

Examples
========

.. include:: goals.rst

This section has a few examples of how to do these things.

Read and manipulate
-------------------

Say we have a directory with a bunch of CSV files with information
about light bulbs in a home. Each CSV file has the wattage used by the
bulb as a function of time. Some of the light bulbs only send a signal
when the state changes, but some send a signal every minute. We can
read them with this code.

.. literalinclude:: ../examples/helloworld.py
   :lines: 12-37

The call to :code:`ts.compact()` will remove any redundant
measurements. Depending on how often your data changes compared to how
often it is sampled, this can reduce the size of the data
dramatically.

Basic analysis
--------------

Now, let's say we want to do some basic exploratory analysis of how
much power is used in the whole home. We'll first take all of the
individual traces and merge them into a single TimeSeries where the
values is the total wattage.

.. literalinclude:: ../examples/helloworld.py
   :lines: 39

The merged time series has times that are the union of all times in
the individual series. Since each time series is the wattage of the
lightbulb, the values after the sum are the total wattage used over
time. Here's how to check the mean power consumption in January.

.. literalinclude:: ../examples/helloworld.py
   :lines: 43-47

Let's say we want to break this down to see how the distribution of
power consumption varies by time of day.

.. literalinclude:: ../examples/helloworld.py
   :lines: 51-52

Or day of week.

.. literalinclude:: ../examples/helloworld.py
   :lines: 54-55

Finally, we just want to look at the distribution of power consumption
during business hours on each day in January.

.. literalinclude:: ../examples/helloworld.py
   :lines: 59-63

In practice, you'd probably be plotting these distribution and time
series using your tool of choice.

Transform to evenly-spaced
--------------------------

Now, let's say we want to do some forecasting of the power consumption
of this home. There is probably some seasonality that need to be
accounted for, among other things, and we know that `statsmodels
<http://statsmodels.sourceforge.net/>`_ and `pandas
<http://pandas.pydata.org/>`_ are tools with some batteries included
for that type of thing. Let's convert to a `pandas Series
<http://pandas.pydata.org/pandas-docs/stable/generated/pandas.Series.html>`_.

.. literalinclude:: ../examples/helloworld.py
   :lines: 70

That will convert to a regularly-spaced time series using a moving
average to avoid `aliasing <https://en.wikipedia.org/wiki/Aliasing>`_
(more info `here <http://scicomp.stackexchange.com/a/615>`_). At this
point, a good next step is the `excellent tutorial by Tom Augspurger
<http://tomaugspurger.github.io/modern-7-timeseries.html>`_, starting
with the *Modeling Time Series* section.
