"""
Advanced example showing how to use traces for financial time series analysis.

This example demonstrates:
1. Converting irregular financial data to a TimeSeries
2. Working with time zones
3. Performing custom operations on time series
4. Converting between different data formats
5. Using masks for specific analysis periods (trading hours)
"""

import datetime
import json
from datetime import timedelta

import traces


def parse_datetime(date_string):
    """Parse ISO format datetime string with optional timezone"""
    return datetime.datetime.fromisoformat(date_string.replace("Z", "+00:00"))


# Sample stock price data with irregular intervals
# In a real application, this might come from an API or database
sample_data = [
    {"time": "2023-03-01T09:30:00Z", "price": 150.25, "volume": 1200},
    {"time": "2023-03-01T09:45:30Z", "price": 151.75, "volume": 800},
    {"time": "2023-03-01T10:15:45Z", "price": 153.50, "volume": 1500},
    {"time": "2023-03-01T11:30:20Z", "price": 152.25, "volume": 950},
    {"time": "2023-03-01T13:15:00Z", "price": 154.00, "volume": 2100},
    {"time": "2023-03-01T14:45:10Z", "price": 156.75, "volume": 1800},
    {"time": "2023-03-01T15:59:55Z", "price": 155.50, "volume": 3200},
    {"time": "2023-03-02T09:31:05Z", "price": 156.00, "volume": 2300},
    {"time": "2023-03-02T10:22:30Z", "price": 158.25, "volume": 1600},
    {"time": "2023-03-02T12:48:15Z", "price": 157.50, "volume": 900},
    {"time": "2023-03-02T14:15:45Z", "price": 159.75, "volume": 1750},
    {"time": "2023-03-02T15:55:00Z", "price": 162.25, "volume": 4500},
]


# 1. Create TimeSeries from irregular stock price data
def create_price_series():
    price_series = traces.TimeSeries(default=None)
    volume_series = traces.TimeSeries(default=0)

    price_series.set_many(
        (parse_datetime(r["time"]), r["price"]) for r in sample_data
    )
    volume_series.set_many(
        (parse_datetime(r["time"]), r["volume"]) for r in sample_data
    )

    return price_series, volume_series


price_ts, volume_ts = create_price_series()

print("== Stock Price Time Series ==")
print(f"Number of measurements: {price_ts.n_measurements()}")
print(f"Time range: {price_ts.first_key()} to {price_ts.last_key()}")
print(f"First price: ${price_ts.first_value()}")
print(f"Last price: ${price_ts.last_value()}")


# 2. Define a function to create trading hours mask
def create_trading_hours_mask(
    start_date,
    end_date,
    start_hour=9,
    start_minute=30,
    end_hour=16,
    end_minute=0,
):
    """Create a mask for regular trading hours (e.g., 9:30 AM to 4:00 PM)"""
    mask = traces.TimeSeries(default=False)

    # Build trading hours for all weekdays in the range
    pairs = []
    current_date = start_date
    while current_date <= end_date:
        # Skip weekends (Saturday=5, Sunday=6)
        if current_date.weekday() < 5:  # Monday through Friday
            market_open = datetime.datetime.combine(
                current_date, datetime.time(start_hour, start_minute)
            )
            market_close = datetime.datetime.combine(
                current_date, datetime.time(end_hour, end_minute)
            )
            pairs.append((market_open, True))
            pairs.append((market_close, False))

        current_date += datetime.timedelta(days=1)

    mask.set_many(pairs)
    return mask


# Create a mask for trading hours across our date range
start_date = parse_datetime("2023-03-01T00:00:00Z").date()
end_date = parse_datetime("2023-03-02T23:59:59Z").date()
trading_hours_mask = create_trading_hours_mask(start_date, end_date)


# 3. Calculate various statistics using the mask
# Average price during trading hours
trading_hours_avg = price_ts.mean(mask=trading_hours_mask)
print(f"\nAverage price during trading hours: ${trading_hours_avg:.2f}")

# Distribution of prices
price_distribution = price_ts.distribution(mask=trading_hours_mask)
print(f"Median price: ${price_distribution.median():.2f}")
print(f"Min price: ${price_distribution.min():.2f}")
print(f"Max price: ${price_distribution.max():.2f}")


# Calculate volume-weighted average price (VWAP)
def calculate_vwap(price_ts, volume_ts):
    """Calculate volume-weighted average price"""
    weighted_ts = price_ts.operation(volume_ts, lambda p, v: p * v)
    total_volume = sum(volume_ts.values())
    total_weighted = sum(weighted_ts.values())
    return total_weighted / total_volume


vwap = calculate_vwap(price_ts, volume_ts)
print(f"Volume-weighted average price (VWAP): ${vwap:.2f}")


# 4. Resampling the irregular data to regular intervals
# Create a regularly sampled time series with 30-minute intervals
start_time = price_ts.first_key()
end_time = price_ts.last_key()
interval = timedelta(minutes=30)

# Using moving average to prevent aliasing
regular_prices = price_ts.moving_average(
    sampling_period=interval,
    window_size=interval,
    start=start_time,
    end=end_time,
)

print("\n== Resampled Price Data (30-minute intervals) ==")
for time, price in regular_prices:
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: ${price:.2f}")


# 5. Calculate returns (percent change between measurements)
def calculate_returns(price_ts):
    """Calculate percentage returns between consecutive prices"""
    returns_ts = traces.TimeSeries(default=0)

    pairs = []
    prev_price = None
    for t, price in price_ts:
        if prev_price is not None:
            pairs.append((t, (price - prev_price) / prev_price * 100))
        prev_price = price

    returns_ts.set_many(pairs)
    return returns_ts


returns_ts = calculate_returns(price_ts)

print("\n== Returns Between Measurements ==")
for t, ret in returns_ts:
    if ret != 0:  # Skip the first point which has 0 return
        print(f"{t.strftime('%Y-%m-%d %H:%M:%S')}: {ret:.2f}%")


# 6. Export the data to JSON for use in other tools
json_data = price_ts.to_json(
    time_transform=lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S"), dict_format=True
)

print("\n== Sample of JSON Export ==")
# Print just a small sample of the JSON
json_dict = json.loads(json_data)
sample_keys = list(json_dict.keys())[:3]
sample_json = {k: json_dict[k] for k in sample_keys}
print(json.dumps(sample_json, indent=2))


# 7. Show how to use distribution_by_hour_of_day
# This is useful for analyzing patterns by hour
print("\n== Price Distribution by Hour ==")
for hour in range(9, 17):  # 9 AM to 4 PM
    mask = traces.day_of_week(start_time, end_time, "Wednesday")
    hour_mask = traces.hour_of_day(start_time, end_time, hour)
    combined_mask = mask & hour_mask

    # Only calculate if we have data for this hour
    if price_ts.distribution(mask=combined_mask).total() > 0:
        hour_avg = price_ts.mean(mask=combined_mask)
        print(f"Hour {hour}: ${hour_avg:.2f}")
