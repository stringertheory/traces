"""
Advanced example showing how to use traces for IoT sensor data analysis.

This example demonstrates:
1. Working with multiple unevenly-spaced sensor time series
2. Handling missing data and anomalies
3. Merging and aligning multiple sensors
4. Performing aggregations and statistics
5. Detecting events and thresholds
"""

import datetime
import random
from datetime import timedelta

import traces


# Generate synthetic IoT sensor data
def generate_sensor_data(
    duration_days=3,
    avg_readings_per_day=48,
    base_value=20,
    noise_level=2,
    missing_data_prob=0.1,
    anomaly_prob=0.05,
):
    """
    Generate synthetic IoT temperature sensor data with realistic patterns:
    - Daily cycles (warmer during day, cooler at night)
    - Random noise
    - Occasional missing data points
    - Rare anomalies/spikes
    """
    start_time = datetime.datetime(2023, 5, 1)
    end_time = start_time + datetime.timedelta(days=duration_days)

    # Total number of readings
    n_readings = int(duration_days * avg_readings_per_day)

    # Create time series with some randomness in measurement times
    ts = traces.TimeSeries(default=None)

    for i in range(n_readings):
        # Random time within the range
        progress = i / n_readings
        hours_offset = duration_days * 24 * progress

        # Add some randomness to the measurement times
        jitter = random.uniform(-0.5, 0.5)  # Hours of jitter
        measurement_time = start_time + timedelta(hours=hours_offset + jitter)

        # Skip if outside our time range or simulate missing data
        if measurement_time > end_time or random.random() < missing_data_prob:
            continue

        # Calculate base temperature with daily cycle
        hour_of_day = measurement_time.hour
        daily_factor = -cos_like(hour_of_day, peak_hour=14)  # Peak at 2pm
        daily_amplitude = 5  # 5 degrees variation throughout the day

        # Weekly pattern (slightly warmer on weekends)
        day_of_week = measurement_time.weekday()
        weekend_boost = 1.5 if day_of_week >= 5 else 0  # Weekend boost

        base_temp = (
            base_value + (daily_factor * daily_amplitude) + weekend_boost
        )

        # Add random noise
        noise = random.uniform(-noise_level, noise_level)
        temperature = base_temp + noise

        # Occasionally add anomalies (spikes or drops)
        if random.random() < anomaly_prob:
            if random.random() < 0.5:
                # Temperature spike
                temperature += random.uniform(5, 15)
            else:
                # Temperature drop
                temperature -= random.uniform(5, 15)

        ts[measurement_time] = round(temperature, 1)

    return ts


def cos_like(hour, peak_hour=12):
    """Simple cosine-like function for daily temperature cycles"""
    return 0.5 + 0.5 * cos_transform((hour - peak_hour) % 24, period=24)


def cos_transform(x, period=24):
    """Transform x to a cosine wave with the given period"""
    import math

    return math.cos(2 * math.pi * x / period)


# Create multiple sensor datasets
print("== IoT Sensor Analysis ==")
print("Generating synthetic sensor data...")

# Three temperature sensors with slightly different characteristics
temp_kitchen = generate_sensor_data(base_value=22, noise_level=1.5)
temp_living_room = generate_sensor_data(base_value=21, noise_level=1.0)
temp_outside = generate_sensor_data(
    base_value=15, noise_level=3.0, avg_readings_per_day=24
)

print(f"Kitchen sensor: {temp_kitchen.n_measurements()} measurements")
print(f"Living room sensor: {temp_living_room.n_measurements()} measurements")
print(f"Outside sensor: {temp_outside.n_measurements()} measurements")


# 1. Basic statistics for individual sensors
def print_sensor_stats(name, ts):
    """Print basic statistics for a sensor time series"""
    print(f"\n== {name} Sensor Statistics ==")

    # Calculate statistics using distribution
    dist = ts.distribution()
    print(f"Average: {dist.mean():.1f}°C")
    print(f"Min: {dist.min():.1f}°C")
    print(f"Max: {dist.max():.1f}°C")
    print(f"Standard deviation: {dist.standard_deviation():.2f}")

    # Quantiles
    q25, median, q75 = dist.quantiles([0.25, 0.5, 0.75])
    print(f"25th percentile: {q25:.1f}°C")
    print(f"Median: {median:.1f}°C")
    print(f"75th percentile: {q75:.1f}°C")


print_sensor_stats("Kitchen", temp_kitchen)
print_sensor_stats("Living Room", temp_living_room)
print_sensor_stats("Outside", temp_outside)


# 2. Merge multiple sensors to find temperature difference
# Calculate the difference between inside and outside temperature
temp_diff = traces.TimeSeries.merge(
    [temp_kitchen, temp_outside],
    operation=lambda values: values[0] - values[1]
    if None not in values
    else None,
)

print("\n== Indoor/Outdoor Temperature Difference ==")
print(f"Average difference: {temp_diff.distribution().mean():.1f}°C")


# 3. Detect events when temperature crosses thresholds
def detect_threshold_crossings(ts, threshold, rising=True):
    """
    Detect when a time series crosses a threshold

    Args:
        ts: The TimeSeries to analyze
        threshold: The threshold value
        rising: If True, detect rising edges; if False, detect falling edges

    Returns:
        A list of timestamps where threshold crossings occur
    """
    crossings = []
    prev_value = None

    for time, value in ts:
        if (
            prev_value is not None
            and value is not None
            and (
                (rising and prev_value < threshold and value >= threshold)
                or (
                    not rising and prev_value > threshold and value <= threshold
                )
            )
        ):
            crossings.append((time, value))

        prev_value = value

    return crossings


# Detect when outside temperature rises above 20°C
hot_events = detect_threshold_crossings(temp_outside, threshold=20, rising=True)
print(f"\n== Detected {len(hot_events)} hot events (outside temp > 20°C) ==")
for i, (time, temp) in enumerate(hot_events):
    if i < 5:  # Show only first 5 events
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {temp:.1f}°C")
    elif i == 5:
        print("...")


# 4. Detect anomalies using rolling statistics
def detect_anomalies(ts, window_size=timedelta(hours=6), z_score_threshold=3):
    """
    Detect anomalies in a time series using z-scores

    Returns a list of (time, value, z_score) tuples for anomalies
    """
    anomalies = []

    # Get all measurements
    measurements = list(ts.items())

    for _i, (current_time, current_value) in enumerate(measurements):
        if current_value is None:
            continue

        # Find measurements within the window
        window_values = []
        for time, value in measurements:
            if (
                current_time - window_size <= time < current_time
                and value is not None
            ):
                window_values.append(value)

        # Need enough values to compute statistics
        if len(window_values) < 3:
            continue

        # Calculate mean and standard deviation of the window
        window_mean = sum(window_values) / len(window_values)
        window_std = (
            sum((v - window_mean) ** 2 for v in window_values)
            / len(window_values)
        ) ** 0.5

        # Avoid division by zero
        if window_std < 0.01:
            continue

        # Calculate z-score
        z_score = abs(current_value - window_mean) / window_std

        # Check if it's an anomaly
        if z_score > z_score_threshold:
            anomalies.append((current_time, current_value, z_score))

    return anomalies


# Detect anomalies in outside temperature
anomalies = detect_anomalies(temp_outside, z_score_threshold=2.5)
print(f"\n== Detected {len(anomalies)} anomalies in outside temperature ==")
for i, (time, temp, z_score) in enumerate(
    sorted(anomalies, key=lambda x: x[2], reverse=True)
):
    if i < 5:  # Show top 5 anomalies by z-score
        print(
            f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {temp:.1f}°C (z-score: {z_score:.2f})"
        )


# 5. Resample to regular intervals for dashboarding
def resample_all_sensors(start_time, end_time, interval=timedelta(minutes=30)):
    """Resample all sensors to regular intervals for consistent reporting"""
    sensors = {
        "Kitchen": temp_kitchen,
        "Living Room": temp_living_room,
        "Outside": temp_outside,
    }

    resampled = {}
    times = []

    # Create regular timestamps
    current = start_time
    while current <= end_time:
        times.append(current)
        current += interval

    # Resample each sensor
    for name, ts in sensors.items():
        resampled[name] = []
        for t in times:
            value = ts.get(t)
            resampled[name].append(value)

    return times, resampled


# Resample all sensor data
start_time = min(
    temp_kitchen.first_key(),
    temp_living_room.first_key(),
    temp_outside.first_key(),
)
end_time = max(
    temp_kitchen.last_key(),
    temp_living_room.last_key(),
    temp_outside.last_key(),
)
times, resampled = resample_all_sensors(
    start_time, end_time, timedelta(hours=1)
)

print("\n== Resampled Hourly Sensor Readings (first 5 hours) ==")
print("Time                 | Kitchen   | Living Room | Outside")
print("-" * 60)
for i, t in enumerate(times):
    if i < 5:  # Show only first 5 hours
        k_val = (
            "None"
            if resampled["Kitchen"][i] is None
            else f"{resampled['Kitchen'][i]:.1f}°C"
        )
        l_val = (
            "None"
            if resampled["Living Room"][i] is None
            else f"{resampled['Living Room'][i]:.1f}°C"
        )
        o_val = (
            "None"
            if resampled["Outside"][i] is None
            else f"{resampled['Outside'][i]:.1f}°C"
        )
        print(
            f"{t.strftime('%Y-%m-%d %H:%M:%S')} | {k_val:10} | {l_val:11} | {o_val:10}"
        )


# 6. Find all periods where outside temperature is below freezing
freezing_mask = temp_outside.threshold(0, inclusive=False).to_bool(invert=True)

print("\n== Periods Below Freezing ==")
for i, (start, end, _is_freezing) in enumerate(
    freezing_mask.iterperiods(value=True)
):
    if i < 3:  # Show only first 3 periods
        duration = (end - start).total_seconds() / 3600  # Hours
        print(
            f"From {start.strftime('%Y-%m-%d %H:%M:%S')} to {end.strftime('%Y-%m-%d %H:%M:%S')} ({duration:.1f} hours)"
        )
