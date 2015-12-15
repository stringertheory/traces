
Measuring things at irregular time intervals is common. Events such as
earthquakes, floods, or volcanic eruptions occur at irregular time
intervals. In clinical trials, a patient’s health may be observed only
at irregular time intervals. And, last but not least, the Internet of
Things streams out a shit ton of data where sensor values are recorded
at irregular intervals due to battery conservation strategies,
uncertain network connectivity, and many other reasons.

And, while there are a bunch of tools for analyzing regularly spaced
time series data, there aren't many for irregularly spaced time
series.

The goal of `traces` is to make it easier to do simple analyses of
irregularly spaced time series data without an awkward, lossy
conversion to a regularly spaced one.

- easy to write, access, and manipulate
- enable simple, exploratory analysis (but not to get too fancy)
- simple conversion to dense time series representation for further analysis


# The `traces` model

Continuous time

This will have some "documentation."

## MathJax

When \(a \ne 0\), there are two solutions to \(ax^2 + bx + c = 0\) and they are
$$x = {-b \pm \sqrt{b^2-4ac} \over 2a}.$$

![screenshot](img/cat.jpg)
