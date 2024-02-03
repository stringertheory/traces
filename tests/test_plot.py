import pytest

import traces


@pytest.mark.mpl_image_compare(
    savefig_kwargs={"bbox_inches": "tight", "dpi": 300},
    remove_text=True,
    style="ggplot",
    tolerance=20,
)
def test_plot():
    ts = traces.TimeSeries()
    ts[0] = 0
    ts[1] = 2
    ts[3] = 1
    ts[5] = 0

    figure, axes = ts.plot()
    return figure


def test_optional_import():
    # TODO: something like this https://stackoverflow.com/a/51048604/1431778
    pass


def test_invalid_call():
    ts = traces.TimeSeries()
    ts[0] = 0
    ts[1] = 1

    ts.plot(interpolate="previous")
    ts.plot(interpolate="linear")

    with pytest.raises(ValueError):
        ts.plot(interpolate="yomama")


def test_empty():
    ts = traces.TimeSeries()

    ts.plot()
