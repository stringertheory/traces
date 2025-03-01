"""Tests for improved methods in TimeSeries."""

import datetime
import warnings

import pytest

import traces
from traces import TimeSeries


class TestImprovedMethods:
    """Test cases for improved and fixed methods in TimeSeries."""

    def test_exists_method_deprecation_warning(self):
        """Test that exists() method triggers deprecation warning."""
        ts = TimeSeries()
        ts[0] = "data"
        ts[1] = None
        
        with warnings.catch_warnings(record=True) as w:
            # Ensure warnings are always triggered
            warnings.simplefilter("always")
            
            # Call the deprecated method
            result = ts.exists()
            
            # Verify warning was triggered
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message)

    def test_is_not_none_method(self):
        """Test that is_not_none() method works correctly."""
        ts = TimeSeries()
        ts[0] = "data"
        ts[1] = None
        ts[2] = 42
        ts[3] = False  # Falsy but not None
        
        result = ts.is_not_none()
        
        assert result[0] is True   # "data" is not None
        assert result[1] is False  # None is None
        assert result[2] is True   # 42 is not None
        assert result[3] is True   # False is not None (it's a valid value)
        
    def test_is_not_none_with_default(self):
        """Test that is_not_none() correctly handles default values."""
        # TimeSeries with None default
        ts_none_default = TimeSeries(default=None)
        result_none = ts_none_default.is_not_none()
        assert result_none.default is False  # None default -> False
        
        # TimeSeries with non-None default
        ts_value_default = TimeSeries(default=0)
        result_value = ts_value_default.is_not_none()
        assert result_value.default is True  # Non-None default -> True
        
    def test_exists_matches_is_not_none(self):
        """Test that exists() returns the same result as is_not_none()."""
        ts = TimeSeries()
        ts[0] = "data"
        ts[1] = None
        ts[2] = 42
        
        # Ignore deprecation warning for this test
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            exists_result = ts.exists()
            
        is_not_none_result = ts.is_not_none()
        
        # Compare all values
        for t in [0, 1, 2]:
            assert exists_result[t] == is_not_none_result[t]


class TestStringRepresentation:
    """Test cases for improved string representation methods."""
    
    def test_repr_shows_default(self):
        """Test that __repr__ includes the default value."""
        ts = TimeSeries(default=42)
        ts[0] = 10
        ts[1] = 20
        
        repr_str = repr(ts)
        assert "default=42" in repr_str
        
    def test_str_shows_default(self):
        """Test that __str__ includes the default value."""
        ts = TimeSeries(default="missing")
        ts[0] = "data"
        
        str_output = str(ts)
        assert "default='missing'" in str_output
        
    def test_str_truncation(self):
        """Test that __str__ truncates long time series correctly."""
        ts = TimeSeries()
        
        # Add more items than the MAX_LENGTH (which is 20)
        for i in range(30):
            ts[i] = i * 10
            
        str_output = str(ts)
        
        # Check that truncation message appears
        assert "<...10 items...>" in str_output
        
        # Check that beginning and end values are still there
        assert "0: 0" in str_output
        assert "29: 290" in str_output