# Unevenly Spaced Data

September 26, 2016

As the Internet of Things (IoT) comes of age, we’re seeing more and more data from event-triggered sensors instead of sensors that record measurements at regular time intervals. These event-triggered sensors give rise to `unevenly-spaced time series <https://en.wikipedia.org/wiki/Unevenly_spaced_time_series>`__. Many analysts will immediately convert unevenly-spaced data to evenly-spaced time series to be compatible with existing sensor data analytics tools, but we have found that the conversion is usually unnecessary, and sometimes even causes problems.

## Unevenly-spaced data is actually pretty great

Imagine a wireless sensor that measures when a light is on.

The sensor has two options: it can send the signal only when the light is switched on or off, or it can send a signal to a base station to indicate whether the light is on every second.

The former, event-driven approach has several advantages: (FOOTNOTE: It also comes with a potential disadvantage that missed signals can cause larger errors. For example, if the wireless connection is unreliable and the last “switched turned off” signal is missed at the end of the day, you could inadvertently make the mistake that the light was on all night long. In this case it can often make sense to include an infrequent “heartbeat” signal, say every hour, that prevents very large measurement errors in the event of dropped signal: this still only requires about 1/60 of the energy-consuming wireless signals to be sent.)

Energy usage in sensor data collection. Sending energy-consuming wireless signals only when necessary will preserve battery as long as events occur less often than you’d be sending regular updates
Time resolution of sensor data processing. You know precisely when the state changed without needing to implement buffering logic on the sensor itself between regular signals.
Reduces redundancy in sensor data storage. No redundancy, without needing to implement compression logic on the base station.
These practical issues are especially important with increasingly more “things” that are wirelessly sending data. Let’s consider a quick calculation.

Suppose you record if a light bulb is on every second (maybe you’ve got a Hue or WeMo lightbulb). In a year, then, you’ll record about 86 thousand data points per day, or about 32 million data points in a year for just one light bulb. If you have 40 light bulbs in your home (the average number of lightbulbs in a U.S. home), that is more than 1.2 billion data points for your home in a year: BIG DATA ;)

Suppose you only turn on and off a light 10 times a day. If you collect your data in an event-driven manner, you will only have 20 data points per day, about 7 thousand data points per year, or about 290 thousand data points for your home. It’s more than a 4,000x reduction in the number of measurements to store!

## Don’t get rid of your unevenly-spaced data

When analysts are presented with unevenly-spaced sensor data, they usually convert the unevenly-spaced data to a evenly-spaced time series by regular sampling or linear interpolation. This conversion helps get the data into a format that are used by the most common tools for time series analysis. In addition to the constraints on data size, this method also presents other practical challenges:

It is easy to make mistakes. Since evenly-spaced time series are usually stored without timestamps (in an array, along with the start time and time interval), it’s easy to use the wrong time units — conversions are `notoriously error-prone <https://en.wikipedia.org/wiki/Mars_Climate_Orbiter>`__ — or mix up when the data was recorded.
It encourages bloat. If you have data from several sources with different time resolution, the usual approach is to sample at the smallest time resolution. You can end up with a time series that is sampled every second from a sensor that samples every hour.
Beyond the practical challenges, there are `technical reasons to be careful <http://www.eckner.com/papers/unevenly_spaced_time_series_analysis.pdf>`__ when converting unevenly-spaced data to regular time series including:

Data loss and dilution. You lose data that are closely spaced, and you add redundant data points when the data are too sparse.
Time information. The duration between each measurement can contain useful information about the data. For example, based on the frequency and duration of the light switching on or off, we can safely say that the second house is more likely to use an automated light switch than the first house.

## Traces deals gracefully with unevenly-spaced data

At Datascope, we’re increasingly finding ourselves helping clients with data from battery-powered sensors that are attached to “things”. In response, we built a lightweight Python package called traces to simplify the reading, writing, and analysis of unevenly-spaced data.

For example, if you want to know how many lightbulbs are turned on given the data from all light bulbs in your house, you can get this information using a very simple syntax.

We’ve found that handling unevenly-spaced data natively is not just useful for sensor data. For example, it’s great for handling time series with missing observations or aggregating multiple time series taken at differing regular intervals. We hope you find it useful, and if you’re interested, we welcome contributions to the code!

Contributors to this post
headshot of Yoke Peng Leong
headshot of Mike Stringer
