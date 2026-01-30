"""
Example demonstrating how to use EventSeries for practical event analysis.

This example shows:
1. Creating EventSeries from various data sources
2. Analyzing event frequency and patterns
3. Tracking active cases over time
4. Working with inter-event times
5. Comparing event patterns across different time periods
"""

import random
from datetime import datetime, timedelta

from traces import EventSeries, TimeSeries

# 1. Creating EventSeries from timestamps
# -----------------------------------------

print("=== Creating EventSeries ===")

# Create from datetime objects
website_logins = EventSeries(
    [
        datetime(2023, 5, 1, 8, 15),
        datetime(2023, 5, 1, 8, 45),
        datetime(2023, 5, 1, 9, 2),
        datetime(2023, 5, 1, 9, 30),
        datetime(2023, 5, 1, 10, 5),
        datetime(2023, 5, 1, 10, 5),  # Two users logging in at the same time
        datetime(2023, 5, 1, 10, 45),
        datetime(2023, 5, 1, 11, 20),
        datetime(2023, 5, 1, 12, 0),
        datetime(2023, 5, 1, 13, 10),
        datetime(2023, 5, 1, 14, 25),
        datetime(2023, 5, 1, 15, 30),
        datetime(2023, 5, 1, 16, 40),
        datetime(2023, 5, 1, 17, 0),
        datetime(2023, 5, 1, 17, 15),
    ]
)

# Create from strings (simulating reading from logs)
server_errors = EventSeries(
    [
        "2023-05-01 09:15:23",
        "2023-05-01 09:15:45",
        "2023-05-01 09:16:02",  # Cluster of errors
        "2023-05-01 09:16:15",  # during system update
        "2023-05-01 10:30:05",
        "2023-05-01 14:22:12",
        "2023-05-01 16:45:30",
    ]
)

# Convert string times to datetime for consistency
server_errors = EventSeries(
    [
        datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        for time_str in server_errors
    ]
)

print(f"Recorded {len(website_logins)} login events")
print(f"Recorded {len(server_errors)} error events")


# 2. Analyzing login frequency by hour
# -------------------------------------

print("\n=== Login Frequency Analysis ===")

# Get cumulative logins over time
cumulative_logins = website_logins.cumulative_sum()

# Print login count at end of each hour
business_hours = [datetime(2023, 5, 1, hour) for hour in range(8, 18)]
for hour in business_hours:
    hour_end = hour + timedelta(hours=1) - timedelta(seconds=1)
    logins_this_hour = website_logins.events_between(hour, hour_end)
    total_logins = cumulative_logins[hour_end]

    print(
        f"{hour.hour:02d}:00 - {hour.hour:02d}:59: {logins_this_hour} logins (Total: {total_logins})"
    )


# 3. Tracking active user sessions
# --------------------------------

print("\n=== Active User Sessions ===")

# Create logout events (users typically stay logged in for 30-90 minutes)
session_durations = [
    timedelta(minutes=random.randint(30, 90))
    for _ in range(len(website_logins))
]
website_logouts = EventSeries(
    [
        login_time + duration
        for login_time, duration in zip(website_logins, session_durations)
    ]
)

# Calculate active sessions over time
active_sessions = EventSeries.count_active(website_logins, website_logouts)

# Check number of active sessions at specific times
check_times = [
    datetime(2023, 5, 1, 9, 0),
    datetime(2023, 5, 1, 10, 30),
    datetime(2023, 5, 1, 12, 0),
    datetime(2023, 5, 1, 15, 0),
    datetime(2023, 5, 1, 17, 30),
]

for time in check_times:
    print(f"{time.strftime('%H:%M')}: {active_sessions[time]} active sessions")


# 4. Analyzing inter-event times
# ------------------------------

print("\n=== Login Inter-arrival Analysis ===")

# Calculate time between logins
login_intervals = list(website_logins.iter_interevent_times())

# Analyze intervals
average_interval = sum(
    [interval.total_seconds() for interval in login_intervals]
) / len(login_intervals)
print(f"Average time between logins: {average_interval/60:.1f} minutes")

# Group intervals by hour of day
morning_intervals = []
afternoon_intervals = []

for i, login_time in enumerate(website_logins[:-1]):  # Exclude last login
    if login_time.hour < 12:
        morning_intervals.append(login_intervals[i].total_seconds() / 60)
    else:
        afternoon_intervals.append(login_intervals[i].total_seconds() / 60)

if morning_intervals:
    print(
        f"Morning average interval: {sum(morning_intervals)/len(morning_intervals):.1f} minutes"
    )
if afternoon_intervals:
    print(
        f"Afternoon average interval: {sum(afternoon_intervals)/len(afternoon_intervals):.1f} minutes"
    )


# 5. Correlating errors with login activity
# -----------------------------------------

print("\n=== Error Correlation ===")


# Function to create hourly event count time series
def hourly_counts(event_series, start_time, end_time):
    """Convert EventSeries to hourly count TimeSeries"""
    result = TimeSeries(default=0)
    current = start_time

    while current < end_time:
        next_hour = current + timedelta(hours=1)
        count = event_series.events_between(
            current, next_hour - timedelta(seconds=1)
        )
        result[current] = count
        current = next_hour

    return result


# Define time range
start_time = datetime(2023, 5, 1, 8, 0)
end_time = datetime(2023, 5, 1, 18, 0)

# Create hourly time series
login_counts = hourly_counts(website_logins, start_time, end_time)
error_counts = hourly_counts(server_errors, start_time, end_time)

# Print table of activity
print("Hour  | Logins | Errors | Error Rate")
print("------+--------+--------+-----------")
for hour in range(8, 18):
    time_point = datetime(2023, 5, 1, hour)
    logins = login_counts[time_point]
    errors = error_counts[time_point]

    # Calculate error rate (errors per login)
    if logins > 0:
        error_rate = errors / logins
        error_rate_str = f"{error_rate:.2f}"
    else:
        error_rate_str = "N/A"

    print(f"{hour:02d}:00 | {logins:6d} | {errors:6d} | {error_rate_str}")


# 6. Analyzing error clusters
# ---------------------------

print("\n=== Error Clustering Analysis ===")

# Find time spans with frequent errors
error_intervals = list(server_errors.iter_interevent_times())
cluster_threshold = timedelta(minutes=5)  # Define what constitutes a cluster

# Find clusters
cluster_start_idx = None
clusters = []

for i, interval in enumerate(error_intervals):
    if interval <= cluster_threshold:
        # This error is close to the previous one
        if cluster_start_idx is None:
            cluster_start_idx = i
    elif cluster_start_idx is not None:
        # End of a cluster
        clusters.append(
            (
                server_errors[cluster_start_idx],
                server_errors[i],
                i - cluster_start_idx + 1,
            )
        )
        cluster_start_idx = None

# Check if the last interval was part of a cluster
if cluster_start_idx is not None:
    clusters.append(
        (
            server_errors[cluster_start_idx],
            server_errors[-1],
            len(server_errors) - cluster_start_idx,
        )
    )

# Report clusters
if clusters:
    print(f"Found {len(clusters)} error clusters:")
    for start_time, end_time, count in clusters:
        duration = (end_time - start_time).total_seconds() / 60
        print(
            f"  {start_time.strftime('%H:%M:%S')} - {end_time.strftime('%H:%M:%S')}: "
            f"{count} errors in {duration:.1f} minutes"
        )
else:
    print("No error clusters found.")
