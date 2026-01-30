"""Tests for new JSON import/export functionality in TimeSeries."""

import json
import os
import tempfile
from datetime import datetime

import pytest

from traces import TimeSeries


class TestJsonIO:
    """Test cases for TimeSeries JSON import/export functionality."""

    def test_to_json_list_format(self):
        """Test exporting TimeSeries to JSON in list format."""
        ts = TimeSeries()
        ts[datetime(2023, 1, 1, 12, 0, 0)] = 10
        ts[datetime(2023, 1, 1, 12, 30, 0)] = 15
        ts[datetime(2023, 1, 1, 13, 0, 0)] = 12

        json_str = ts.to_json()
        data = json.loads(json_str)

        assert isinstance(data, list)
        assert len(data) == 3
        assert data[0]["time"] == "2023-01-01T12:00:00"
        assert data[0]["value"] == 10
        assert data[1]["value"] == 15
        assert data[2]["value"] == 12

    def test_to_json_dict_format(self):
        """Test exporting TimeSeries to JSON in dictionary format."""
        ts = TimeSeries()
        ts[datetime(2023, 1, 1, 12, 0, 0)] = 10
        ts[datetime(2023, 1, 1, 12, 30, 0)] = 15

        json_str = ts.to_json(dict_format=True)
        data = json.loads(json_str)

        assert isinstance(data, dict)
        assert len(data) == 2
        assert data["2023-01-01T12:00:00"] == 10
        assert data["2023-01-01T12:30:00"] == 15

    def test_to_json_with_custom_transform(self):
        """Test exporting TimeSeries with custom transform functions."""
        ts = TimeSeries()
        ts[datetime(2023, 1, 1, 12, 0, 0)] = 10.5
        ts[datetime(2023, 1, 1, 13, 0, 0)] = 15.75

        # Custom transform functions
        time_transform = lambda dt: dt.strftime("%Y-%m-%d %H:%M")
        value_transform = lambda v: int(v)

        json_str = ts.to_json(
            time_transform=time_transform, value_transform=value_transform
        )
        data = json.loads(json_str)

        assert data[0]["time"] == "2023-01-01 12:00"
        assert data[0]["value"] == 10  # int(10.5)
        assert data[1]["time"] == "2023-01-01 13:00"
        assert data[1]["value"] == 15  # int(15.75)

    def test_to_json_file_output(self):
        """Test writing TimeSeries to a JSON file."""
        ts = TimeSeries()
        ts[datetime(2023, 1, 1, 12, 0, 0)] = 10
        ts[datetime(2023, 1, 1, 13, 0, 0)] = 15

        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False
        ) as temp_file:
            temp_filename = temp_file.name

        try:
            # Write to file
            result = ts.to_json(filename=temp_filename)

            # Verify result is None (indicating file write)
            assert result is None

            # Read and verify contents
            with open(temp_filename) as f:
                data = json.load(f)

            assert len(data) == 2
            assert data[0]["time"] == "2023-01-01T12:00:00"
            assert data[0]["value"] == 10
            assert data[1]["value"] == 15

        finally:
            # Clean up temp file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    def test_from_json_list_format(self):
        """Test creating TimeSeries from JSON in list format."""
        json_string = """[
            {"time": "2023-01-01T12:00:00", "value": 10},
            {"time": "2023-01-01T12:30:00", "value": 15},
            {"time": "2023-01-01T13:00:00", "value": 20}
        ]"""

        ts = TimeSeries.from_json(json_string=json_string)

        assert len(ts) == 3
        assert ts[datetime(2023, 1, 1, 12, 0, 0)] == 10
        assert ts[datetime(2023, 1, 1, 12, 30, 0)] == 15
        assert ts[datetime(2023, 1, 1, 13, 0, 0)] == 20

    def test_from_json_dict_format(self):
        """Test creating TimeSeries from JSON in dictionary format."""
        json_string = """{
            "2023-01-01T12:00:00": 10,
            "2023-01-01T13:00:00": 20
        }"""

        ts = TimeSeries.from_json(json_string=json_string)

        assert len(ts) == 2
        assert ts[datetime(2023, 1, 1, 12, 0, 0)] == 10
        assert ts[datetime(2023, 1, 1, 13, 0, 0)] == 20

    def test_from_json_with_custom_keys(self):
        """Test creating TimeSeries with custom time and value keys."""
        json_string = """[
            {"timestamp": "2023-01-01T12:00:00", "temperature": 10},
            {"timestamp": "2023-01-01T13:00:00", "temperature": 20}
        ]"""

        ts = TimeSeries.from_json(
            json_string=json_string,
            time_key="timestamp",
            value_key="temperature",
        )

        assert len(ts) == 2
        assert ts[datetime(2023, 1, 1, 12, 0, 0)] == 10
        assert ts[datetime(2023, 1, 1, 13, 0, 0)] == 20

    def test_from_json_with_custom_transform(self):
        """Test creating TimeSeries with custom transform functions."""
        # Create specific timestamps for testing
        dt1 = datetime(2023, 1, 1, 12, 0, 0)
        dt2 = datetime(2023, 1, 1, 13, 0, 0)

        # Convert to Unix timestamps (as strings)
        timestamp1 = str(int(dt1.timestamp()))
        timestamp2 = str(int(dt2.timestamp()))

        json_string = f"""[
            {{"time": "{timestamp1}", "value": "10.5"}},
            {{"time": "{timestamp2}", "value": "20.7"}}
        ]"""

        # Custom transform functions
        time_transform = lambda ts: datetime.fromtimestamp(int(ts))
        value_transform = lambda vs: float(vs)

        ts = TimeSeries.from_json(
            json_string=json_string,
            time_transform=time_transform,
            value_transform=value_transform,
        )

        assert len(ts) == 2

        # Get values at the specific times
        assert ts[dt1] == 10.5
        assert ts[dt2] == 20.7

    def test_from_json_file(self):
        """Test reading TimeSeries from a JSON file."""
        json_content = """[
            {"time": "2023-01-01T12:00:00", "value": 10},
            {"time": "2023-01-01T13:00:00", "value": 20}
        ]"""

        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False
        ) as temp_file:
            temp_file.write(json_content.encode("utf-8"))
            temp_filename = temp_file.name

        try:
            # Read from file
            ts = TimeSeries.from_json(filename=temp_filename)

            assert len(ts) == 2
            assert ts[datetime(2023, 1, 1, 12, 0, 0)] == 10
            assert ts[datetime(2023, 1, 1, 13, 0, 0)] == 20

        finally:
            # Clean up temp file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    def test_from_json_invalid_format(self):
        """Test creating TimeSeries from invalid JSON format."""
        json_string = "123"  # Not a list or dict

        with pytest.raises(
            TypeError, match="JSON data must be either a list or dictionary"
        ):
            TimeSeries.from_json(json_string=json_string)

    def test_from_json_missing_source(self):
        """Test error when no filename or json_string is provided."""
        with pytest.raises(
            ValueError, match="Either filename or json_string must be provided"
        ):
            TimeSeries.from_json()

    def test_roundtrip_json(self):
        """Test round-trip conversion (TimeSeries -> JSON -> TimeSeries)."""
        original = TimeSeries()
        original[datetime(2023, 1, 1, 12, 0, 0)] = 10
        original[datetime(2023, 1, 1, 13, 0, 0)] = 20

        # Convert to JSON and back
        json_str = original.to_json()
        recreated = TimeSeries.from_json(json_string=json_str)

        # Check if they match
        assert len(original) == len(recreated)
        for t, v in original:
            assert recreated[t] == v
