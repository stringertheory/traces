import importlib

import pytest

import traces

matplotlib_importable = importlib.util.find_spec("matplotlib")


def _make_ts():
    ts = traces.TimeSeries()
    ts[0] = 0
    ts[1] = 1
    return ts


def test_message_when_matplotlib_not_installed():
    """When matplotlib is not importable, make sure that calling plot
    raises an informative error message.

    """
    if not matplotlib_importable:
        ts = _make_ts()

        with pytest.raises(ImportError) as error:
            ts.plot()

        assert "need to install matplotlib" in str(error)
