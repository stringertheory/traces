"""EventSeries module for handling series of events occurring at specific times.

This module provides the EventSeries class that represents a sequence of events
occurring at specific times. Unlike TimeSeries which tracks measurements over time,
EventSeries represents discrete events without associated values.
"""

import itertools

import sortedcontainers

from . import utils
from .timeseries import TimeSeries


class EventSeries(sortedcontainers.SortedList):
    """A sorted collection of event times.

    EventSeries is a specialized data structure for representing a sequence of events
    that occur at specific times. It inherits from sortedcontainers.SortedList and
    keeps event times in chronological order.

    This class is useful for:
    - Tracking when events occur (like clicks, logins, system events, etc.)
    - Counting events over time periods
    - Analyzing inter-event times (time between consecutive events)
    - Tracking cases that open and close (like support tickets, hospital visits)

    Unlike TimeSeries, EventSeries doesn't track values associated with each time point,
    only the times themselves. It may contain duplicate times if multiple events
    occur simultaneously.

    Args:
        data (iterable, optional): An optional iterable of time points to initialize the series.
            Times can be any comparable type (datetime, float, int, string, etc.) but
            should be consistent throughout the series.

    Examples:
        >>> # Create an empty EventSeries
        >>> es = EventSeries()
        >>>
        >>> # Create from a list of timestamps
        >>> from datetime import datetime
        >>> events = [
        ...     datetime(2023, 1, 1, 12, 0, 0),
        ...     datetime(2023, 1, 1, 14, 30, 0),
        ...     datetime(2023, 1, 2, 9, 15, 0)
        ... ]
        >>> es = EventSeries(events)
        >>>
        >>> # Create from string times (requires consistent format)
        >>> es = EventSeries(["08:00", "09:30", "13:15", "15:45"])
    """

    def __init__(self, data=None):
        """Initialize an EventSeries with optional data.

        Args:
            data (iterable, optional): An optional iterable of time points.
        """
        super().__init__(data)

    def cumsum(self):
        """Alias for cumulative_sum()

        Returns:
            TimeSeries: A cumulative count of events over time.
        """
        return self.cumulative_sum()

    def cumulative_sum(self):
        """Create a TimeSeries of cumulative event counts over time.

        Generates a TimeSeries where each unique time in the EventSeries becomes
        a measurement point, and the value is the total number of events that have
        occurred up to and including that time.

        Returns:
            TimeSeries: A new TimeSeries with times from the EventSeries as keys
                and cumulative counts as values. The default value is 0.

        Examples:
            >>> es = EventSeries([1, 1, 4, 5, 9, 6, 3, 9, 15])
            >>> cumulative = es.cumulative_sum()
            >>> cumulative[1]  # Two events at time 1
            2
            >>> cumulative[5]  # Five events up to and including time 5
            5
            >>> cumulative[15]  # All nine events by time 15
            9
            >>> cumulative[0]  # No events before time 1
            0
        """
        ts = TimeSeries(default=0)
        running_total = 0
        for t, event_group in itertools.groupby(self):
            running_total += len(list(event_group))
            ts[t] = running_total

        return ts

    def events_between(self, start, end):
        """Count events occurring within a specific time interval.

        Counts the number of events that occurred between the specified start and end times,
        inclusive of both endpoints (closed interval).

        Args:
            start: The start time of the interval (inclusive)
            end: The end time of the interval (inclusive)

        Returns:
            int: The number of events that occurred within the specified interval.

        Examples:
            >>> es = EventSeries([1, 1, 4, 5, 9, 6, 3, 9, 15])
            >>> es.events_between(1, 5)  # Events at times 1, 1, 3, 4, 5
            5
            >>> es.events_between(7, 10)  # Events at times 9, 9
            2
            >>> es.events_between(16, 20)  # No events in this range
            0
        """
        start_idx = self.bisect_left(start)
        end_idx = self.bisect_right(end)
        return end_idx - start_idx

    def iter_interevent_times(self):
        """Iterate through the time intervals between consecutive events.

        Yields the time difference between each consecutive pair of events
        in the series. This is useful for analyzing event arrival patterns,
        wait times, or service intervals.

        Yields:
            The time difference between consecutive events. The type will depend
            on the time type used in the EventSeries (timedelta for datetime objects,
            numeric difference for numbers, etc.)

        Examples:
            >>> from datetime import datetime, timedelta
            >>> events = [
            ...     datetime(2023, 1, 1, 12, 0, 0),
            ...     datetime(2023, 1, 1, 14, 30, 0),  # 2.5 hours after first
            ...     datetime(2023, 1, 1, 14, 45, 0),  # 15 minutes after second
            ... ]
            >>> es = EventSeries(events)
            >>> intervals = list(es.iter_interevent_times())
            >>> intervals[0]  # Time between first and second events
            timedelta(hours=2, minutes=30)
            >>> intervals[1]  # Time between second and third events
            timedelta(minutes=15)
        """
        for t0, t1 in utils.pairwise(self):
            yield t1 - t0

    @staticmethod
    def count_active(es_open, es_closed):
        """Calculate the number of active cases over time from open and close events.

        This method is useful for tracking the number of concurrent active cases
        at any point in time, such as:
        - Open support tickets
        - Active sessions or logins
        - Hospital patients
        - Ongoing processes

        It takes two event series: one for when cases open/start, and another for
        when cases close/end. It then computes the difference between cumulative
        open and close events to determine how many cases are active at each point.

        Args:
            es_open (EventSeries): Series of times when cases open or start
            es_closed (EventSeries): Series of times when cases close or end

        Returns:
            TimeSeries: A TimeSeries with the number of active cases at any point in time.
                The default value is 0 (representing times before any cases opened).

        Examples:
            >>> # Track support tickets opened and closed
            >>> ticket_opened = EventSeries(["08:00", "09:00", "13:00", "07:00"])
            >>> ticket_closed = EventSeries(["08:30", "12:00", "12:00"])
            >>> active_tickets = EventSeries.count_active(ticket_opened, ticket_closed)
            >>>
            >>> active_tickets["07:00"]  # 1 ticket opened
            1
            >>> active_tickets["08:15"]  # 2 opened, 0 closed
            2
            >>> active_tickets["08:45"]  # 2 opened, 1 closed
            1
            >>> active_tickets["13:15"]  # 4 opened, 3 closed
            1
        """
        return es_open.cumsum() - es_closed.cumsum()
