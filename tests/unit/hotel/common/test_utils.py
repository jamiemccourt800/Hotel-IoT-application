"""Unit tests for common/utils.py"""
import pytest
import time
import os
from common.utils import (
    now_ms, now_s, clamp_0_100, device_key,
    env_bool, env_int, env_float,
    validate_temperature_range, validate_humidity_range, validate_brightness_range
)


class TestTimeUtilities:
    """Test time-related utility functions"""
    
    def test_now_ms_returns_integer(self):
        """Test now_ms returns integer timestamp"""
        result = now_ms()
        assert isinstance(result, int)
        
    def test_now_ms_reasonable_value(self):
        """Test now_ms returns reasonable timestamp (after 2020)"""
        result = now_ms()
        # Timestamp should be > Jan 1, 2020 in milliseconds
        assert result > 1577836800000
        
    def test_now_ms_increases(self):
        """Test now_ms returns increasing values"""
        ts1 = now_ms()
        time.sleep(0.01)  # Sleep 10ms
        ts2 = now_ms()
        assert ts2 > ts1
        
    def test_now_s_returns_float(self):
        """Test now_s returns float timestamp"""
        result = now_s()
        assert isinstance(result, float)
        
    def test_now_s_reasonable_value(self):
        """Test now_s returns reasonable timestamp"""
        result = now_s()
        # Timestamp should be > Jan 1, 2020 in seconds
        assert result > 1577836800
        
    def test_now_s_increases(self):
        """Test now_s returns increasing values"""
        ts1 = now_s()
        time.sleep(0.01)
        ts2 = now_s()
        assert ts2 > ts1


class TestClampFunction:
    """Test clamp_0_100 utility function"""
    
    def test_clamp_value_in_range(self):
        """Test values within 0-100 are unchanged"""
        assert clamp_0_100(50) == 50
        assert clamp_0_100(0) == 0
        assert clamp_0_100(100) == 100
        assert clamp_0_100(50.5) == 50
        
    def test_clamp_negative_value(self):
        """Test negative values are clamped to 0"""
        assert clamp_0_100(-1) == 0
        assert clamp_0_100(-100) == 0
        assert clamp_0_100(-0.5) == 0
        
    def test_clamp_over_100(self):
        """Test values over 100 are clamped to 100"""
        assert clamp_0_100(101) == 100
        assert clamp_0_100(200) == 100
        assert clamp_0_100(100.5) == 100
        
    def test_clamp_returns_int(self):
        """Test clamp always returns integer"""
        assert isinstance(clamp_0_100(50.7), int)
        assert isinstance(clamp_0_100(99.9), int)
        assert clamp_0_100(99.9) == 99


class TestDeviceKey:
    """Test device_key utility function"""
    
    def test_device_key_format(self):
        """Test device key uses colon separator"""
        result = device_key("hotel_01", "101", "temperature")
        assert result == "hotel_01:101:temperature"
        
    def test_device_key_different_inputs(self):
        """Test device key produces different results for different inputs"""
        key1 = device_key("hotel_01", "101", "temperature")
        key2 = device_key("hotel_01", "102", "temperature")
        key3 = device_key("hotel_02", "101", "temperature")
        
        assert key1 != key2
        assert key1 != key3
        assert key2 != key3
        
    def test_device_key_consistency(self):
        """Test device key produces same result for same inputs"""
        key1 = device_key("hotel_01", "101", "temperature")
        key2 = device_key("hotel_01", "101", "temperature")
        assert key1 == key2


class TestEnvironmentVariables:
    """Test environment variable parsing functions"""
    
    def test_env_bool_true_values(self):
        """Test env_bool recognizes true values"""
        os.environ["TEST_BOOL"] = "1"
        assert env_bool("TEST_BOOL", False) is True
        
        os.environ["TEST_BOOL"] = "true"
        assert env_bool("TEST_BOOL", False) is True
        
        os.environ["TEST_BOOL"] = "TRUE"
        assert env_bool("TEST_BOOL", False) is True
        
        os.environ["TEST_BOOL"] = "yes"
        assert env_bool("TEST_BOOL", False) is True
        
        os.environ["TEST_BOOL"] = "on"
        assert env_bool("TEST_BOOL", False) is True
        
        # Cleanup
        del os.environ["TEST_BOOL"]
        
    def test_env_bool_false_values(self):
        """Test env_bool treats other values as false regardless of default"""
        os.environ["TEST_BOOL"] = "0"
        assert env_bool("TEST_BOOL", True) is False  # Returns False, not default
        
        os.environ["TEST_BOOL"] = "false"
        assert env_bool("TEST_BOOL", True) is False  # Returns False, not default
        
        os.environ["TEST_BOOL"] = "no"
        assert env_bool("TEST_BOOL", True) is False  # Returns False, not default
        
        # Cleanup
        del os.environ["TEST_BOOL"]
        
    def test_env_bool_unset_uses_default(self):
        """Test env_bool returns default when variable not set"""
        # Make sure variable doesn't exist
        if "NONEXISTENT_VAR" in os.environ:
            del os.environ["NONEXISTENT_VAR"]
            
        assert env_bool("NONEXISTENT_VAR", True) is True
        assert env_bool("NONEXISTENT_VAR", False) is False
        
    def test_env_int_valid_value(self):
        """Test env_int parses valid integers"""
        os.environ["TEST_INT"] = "42"
        assert env_int("TEST_INT", 0) == 42
        
        os.environ["TEST_INT"] = "-10"
        assert env_int("TEST_INT", 0) == -10
        
        # Cleanup
        del os.environ["TEST_INT"]
        
    def test_env_int_invalid_value_uses_default(self):
        """Test env_int uses default for invalid values"""
        os.environ["TEST_INT"] = "not_a_number"
        assert env_int("TEST_INT", 99) == 99
        
        os.environ["TEST_INT"] = "3.14"
        assert env_int("TEST_INT", 99) == 99
        
        # Cleanup
        del os.environ["TEST_INT"]
        
    def test_env_int_unset_uses_default(self):
        """Test env_int returns default when variable not set"""
        if "NONEXISTENT_INT" in os.environ:
            del os.environ["NONEXISTENT_INT"]
            
        assert env_int("NONEXISTENT_INT", 123) == 123
        
    def test_env_float_valid_value(self):
        """Test env_float parses valid floats"""
        os.environ["TEST_FLOAT"] = "3.14"
        assert env_float("TEST_FLOAT", 0.0) == 3.14
        
        os.environ["TEST_FLOAT"] = "-2.5"
        assert env_float("TEST_FLOAT", 0.0) == -2.5
        
        os.environ["TEST_FLOAT"] = "42"
        assert env_float("TEST_FLOAT", 0.0) == 42.0
        
        # Cleanup
        del os.environ["TEST_FLOAT"]
        
    def test_env_float_invalid_value_uses_default(self):
        """Test env_float uses default for invalid values"""
        os.environ["TEST_FLOAT"] = "not_a_number"
        assert env_float("TEST_FLOAT", 9.99) == 9.99
        
        # Cleanup
        del os.environ["TEST_FLOAT"]
        
    def test_env_float_unset_uses_default(self):
        """Test env_float returns default when variable not set"""
        if "NONEXISTENT_FLOAT" in os.environ:
            del os.environ["NONEXISTENT_FLOAT"]
            
        assert env_float("NONEXISTENT_FLOAT", 1.23) == 1.23


class TestValidationFunctions:
    """Test validation utility functions"""
    
    def test_validate_temperature_valid_range(self):
        """Test temperature validation accepts valid values"""
        assert validate_temperature_range(20.0) is True
        assert validate_temperature_range(0.0) is True
        assert validate_temperature_range(-10.0) is True
        assert validate_temperature_range(50.0) is True
        
    def test_validate_temperature_default_limits(self):
        """Test temperature validation with default limits"""
        assert validate_temperature_range(-50.0) is True
        assert validate_temperature_range(120.0) is True
        assert validate_temperature_range(-51.0) is False
        assert validate_temperature_range(121.0) is False
        
    def test_validate_temperature_custom_limits(self):
        """Test temperature validation with custom limits"""
        assert validate_temperature_range(25.0, 0.0, 50.0) is True
        assert validate_temperature_range(0.0, 0.0, 50.0) is True
        assert validate_temperature_range(50.0, 0.0, 50.0) is True
        assert validate_temperature_range(-1.0, 0.0, 50.0) is False
        assert validate_temperature_range(51.0, 0.0, 50.0) is False
        
    def test_validate_humidity_valid_range(self):
        """Test humidity validation accepts 0-100%"""
        assert validate_humidity_range(0.0) is True
        assert validate_humidity_range(50.0) is True
        assert validate_humidity_range(100.0) is True
        assert validate_humidity_range(45.5) is True
        
    def test_validate_humidity_invalid_range(self):
        """Test humidity validation rejects values outside 0-100%"""
        assert validate_humidity_range(-0.1) is False
        assert validate_humidity_range(-10.0) is False
        assert validate_humidity_range(100.1) is False
        assert validate_humidity_range(150.0) is False
        
    def test_validate_brightness_valid_range(self):
        """Test brightness validation accepts 0-100"""
        assert validate_brightness_range(0) is True
        assert validate_brightness_range(50) is True
        assert validate_brightness_range(100) is True
        
    def test_validate_brightness_invalid_range(self):
        """Test brightness validation rejects values outside 0-100"""
        assert validate_brightness_range(-1) is False
        assert validate_brightness_range(-10) is False
        assert validate_brightness_range(101) is False
        assert validate_brightness_range(200) is False
