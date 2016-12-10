from __future__ import print_function

import sys
import glob

from datetime import datetime, timedelta

import traces
from traces import masks
from traces.utils import datetime_range


def parse_iso_datetime(value):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")


def read_all(pattern='data/lightbulb-*.csv'):
    """Read all of the CSVs in a directory matching the filename pattern
    as TimeSeries.

    """
    result = []
    for filename in glob.iglob(pattern):
        print('reading', filename, file=sys.stderr)
        ts = traces.TimeSeries.from_csv(
            filename,
            time_column=0,
            time_transform=parse_iso_datetime,
            value_column=1,
            value_transform=int,
            default=0,
        )
        ts.compact()
        result.append(ts)
        break
    return result

ts_list = read_all()

total_watts = traces.TimeSeries.merge(ts_list, operation=sum)

# use distribution to look at the distribution of number of lights on
# over a month
histogram = total_watts.distribution(
    start=datetime(2016, 1, 1),
    end=datetime(2016, 2, 1),
)
print(histogram.mean())

# use distribution with mask to look at the median/lower/upper of
# lights on by hour of day, plot with your tool of choice
for hour, distribution in total_watts.distribution_by_hour_of_day():
    print(hour, distribution.quantiles([0.25, 0.5, 0.75]))

for day, distribution in total_watts.distribution_by_day_of_week():
    print(day, distribution.quantiles([0.25, 0.5, 0.75]))

# look at the typical number of lights on during business hours
# (8am-6pm) for each day in january
for t in datetime_range(datetime(2016, 1, 1), datetime(2016, 2, 1), 'days'):
    biz_start = t + timedelta(hours=8)
    biz_end = t + timedelta(hours=18)
    histogram = total_watts.distribution(start=biz_start, end=biz_end)
    print(t, histogram.quantiles([0.25, 0.5, 0.75]))
    
# transform time series to evenly spaced version using moving average
# instead of just sampling to avoid aliasing, and proceed to use
# statsmodels/pandas to forecast electricity usage "Modeling Time
# Series" http://tomaugspurger.github.io/modern-7-timeseries.html, in
# the Jupyter notebook it's `In [17]`.
regular = total_watts.moving_average(300, pandas=True)
print(regular)
