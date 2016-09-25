"""
# plot with your tool of choice
holidays
weekends
weekdays
business_days
hour_of_day
day_of_week
month_of_year

"""
from datetime import datetime, date, timedelta

from .utils import datetime_range, datetime_floor, weekday_number
from .domain import Domain


def hour_of_day(start, end, hour):

    # start should be date, or if datetime, will use date of datetime
    floored = datetime_floor(start)

    intervals = []
    for day_start in datetime_range(floored, end, 'days',
                                    inclusive_end=True):
        interval_start = day_start + timedelta(hours=hour)
        interval_end = interval_start + timedelta(hours=1)
        intervals.append([interval_start, interval_end])

    return Domain(intervals).slice(start, end)


def day_of_week(start, end, weekday):

    # allow weekday name or number
    number = weekday_number(weekday)

    # start should be date, or if datetime, will use date of datetime
    floored = datetime_floor(start)

    for day in datetime_range(floored, floored + timedelta(days=7), 'days'):
        if day.weekday() == number:
            first_day = day
            break

    intervals = []
    for week_start in datetime_range(first_day, end, 'weeks',
                                     inclusive_end=True):
        interval_start = week_start
        interval_end = interval_start + timedelta(days=1)
        intervals.append([interval_start, interval_end])

    return Domain(intervals).slice(start, end)
