from __future__ import print_function

import sys

from datetime import datetime, timedelta

import traces
from traces import masks


def iso(value):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")

# read a csv with 40 different wattage light bulbs, a few of them
# regularly-spaced.
ts_list = []
for lightbulb_id in range(1, 41):
    filename = 'data/lightbulb-{:02d}.csv'.format(lightbulb_id)
    print('reading {}'.format(filename), file=sys.stderr)
    ts = traces.TimeSeries.from_csv(
        filename,
        time_column=0,
        time_transform=iso,
        value_column=1,
        value_transform=int,
    )
    ts.compact()
    ts_list.append(ts)

import sys
sys.exit()
    
# use distribution to look at the distribution of number of lights on
# over a month
total = traces.TimeSeries.merge(ts_list, operation=sum)
histogram = total.distribution(
    start_time=datetime(2016, 1, 1),
    end_time=datetime(2016, 2, 1),
)
print(histogram.mean())


current_date = datetime(2016, 1, 1)
while current_date < datetime(2016, 3, 1):
    biz_start = current_date + timedelta(hours=8)
    biz_end = current_date + timedelta(hours=18)
    histogram = total.distribution(start_time=biz_start, end_time=biz_end)
    print(current_date, histogram.quantiles([0.1, 0.5, 0.9]))
    current_date += timedelta(days=1)
    
# use distribution with mask to look at the median/lower/upper of
# lights on by hour of day
for hour in range(24):
    mask = masks.hour_of_day(datetime(2016, 1, 1), datetime(2016, 3, 15), hour)
    histogram = total.distribution(mask=mask)
    print(hour, histogram.quantiles([0.1, 0.5, 0.9]))

for day in range(7):
    mask = masks.day_of_week(datetime(2016, 1, 1), datetime(2016, 3, 15), day)
    histogram = total.distribution(mask=mask)
    print(day, histogram.mean())
    
# plot with your tool of choice

# transform time series to evenly spaced version using moving average
# to avoid aliasing, and proceed to use statsmodels/pandas to forecast
# electricity usage "Modeling Time Series"
# http://tomaugspurger.github.io/modern-7-timeseries.html, in the
# Jupyter notebook it's `In [17]`.

