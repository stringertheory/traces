.. _api:

API Reference
=============

.. _timeseries:

TimeSeries
----------

TODO: Description of the concept of the TimeSeries, i.e. what happens
when you get a time before the first measurement or after the last
measurement.

Under the hood
++++++++++++++

``TimeSeries`` uses the excellent `sortedcontainers.SortedDict
<http://www.grantjenks.com/docs/sortedcontainers/introduction.html#sorteddict>`__
under the hood.

.. autoclass:: traces.TimeSeries
    :members:

.. _domain:
       
Domain
------

TODO: Description of the concept of the Domain.

.. autoclass:: traces.Domain
    :members:

.. _histogram:
       
Histogram
---------

TODO: Description of the concept of the Histogram.

.. autoclass:: traces.Histogram
    :members:

