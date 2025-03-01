# Changelog

## [0.6.5] - In Development

### Added
- Added JSON import/export functionality:
  - `TimeSeries.from_json()` method to load from JSON files or strings
  - `TimeSeries.to_json()` method to export to JSON files or strings
  - Support for custom time and value transformations
  - Support for different JSON formats (list or dictionary)
- Added `is_not_none()` method as an improved replacement for the `exists()` method
- Added comprehensive docstrings for all public methods
- Added two new advanced examples:
  - `financial_analysis.py`: Demonstrating financial time series use cases
  - `iot_sensor_analysis.py`: Demonstrating IoT sensor data analysis
- Added deprecation warning to `exists()` method

### Fixed
- Fixed incorrect error handling in `_get_previous()` method
- Fixed string representation (`__str__` and `__repr__`) to consistently include default value
- Improved variable naming in string representation methods for clarity

## [0.6.4] - 2023-03-01

- Updating dependencies
- Fix vulnerability in dependencies