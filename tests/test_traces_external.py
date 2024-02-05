import csv
import os
from datetime import datetime

from dateutil.parser import parse as date_parse

from traces import TimeSeries


def test_csv():
    filename = "sample.csv"
    with open(filename, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["hour", "value"])
        writer.writerow(["2000-01-01 10:00am", "15"])
        writer.writerow(["2000-01-01 11:00am", "34"])
        writer.writerow(["2000-01-01 12:00pm", "19"])
        writer.writerow(["2000-01-01 1:00pm", "nan"])
        writer.writerow(["2000-01-01 2:00pm", "18"])
        writer.writerow(["2000-01-01 3:00pm", "nan"])

    ts = TimeSeries.from_csv(filename, time_transform=date_parse)
    os.remove(filename)

    assert ts[datetime(2000, 1, 1, 9)] is None
    assert ts[datetime(2000, 1, 1, 10, 30)] == "15"
    assert ts[datetime(2000, 1, 1, 20)] == "nan"
