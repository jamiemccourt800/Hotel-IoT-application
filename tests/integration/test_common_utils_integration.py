"""
Integration tests for hotel/room1/common/utils.py
Tests utility functions in realistic scenarios
"""
import pytest
import time
import os
from hotel.room1.common.utils import (
    now_ms, now_s, clamp_0_100, device_key,
    env_bool, env_int, env_float
)


@pytest.mark.integration
@pytest.mark.timeout(5)
class TestUtilsIntegration:
    """Test utility functions in integration context"""
    
    def test_now_ms_returns_current_time(self):
        """Verify now_ms returns current epoch milliseconds"""
        before = int(time.time() * 1000)
        result = now_ms()
        after = int(time.time() * 1000)
        
        assert before <= result <= after
        assert isinstance(result, int)
    
    def test_now_s_returns_current_time(self):
        """Verify now_s returns current epoch seconds"""
        before = time.time()
        result = now_s()
        after = time.time()
        
        assert before <= result <= after
        assert isinstance(result, float)
    
    def test_clamp_0_100_normal_range(self):
        """Test clamp with values in 0-100 range"""
        assert clamp_0_100(0) == 0
        assert clamp_0_100(50) == 50
        assert clamp_0_100(100) == 100
        assert clamp_0_100(75.8) == 75
    
    def test_clamp_0_100_below_range(self):
        """Test clamp with values below 0"""
        assert clamp_0_100(-1) == 0
        assert clamp_0_100(-100) == 0
        assert clamp_0_100(-0.5) == 0
    
    def test_clamp_0_100_above_range(self):
        """Test clamp with values above 100"""
        assert clamp_0_100(101) == 100
        assert clamp_0_100(255) == 100
        assert clamp_0_100(100.1) == 100
    
    def test_device_key_generation(self):
        """Test device key format for deduplication"""
        key = device_key("hotel1", "101", "temperature")
        assert key == "hotel1:101:temperature"
        
        key2 = device_key("h2", "202", "humidity")
        assert key2 == "h2:202:humidity"
        
        # Ensure uniqueness
        assert key != key2
    
    def test_env_bool_true_values(self, monkeypatch):
        """Test env_bool with various truthy values"""
        test_cases = ["1", "true", "TRUE", "True", "yes", "YES", "on", "ON"]
        
        for value in test_cases:
            monkeypatch.setenv("TEST_BOOL", value)
            assert env_bool("TEST_BOOL", False) is True, f"Failed for value: {value}"
    
    def test_env_bool_false_values(self, monkeypatch):
        """Test env_bool with falsy values"""
        test_cases = ["0", "false", "no", "off", "random", ""]
        
        for value in test_cases:
            monkeypatch.setenv("TEST_BOOL", value)
            assert env_bool("TEST_BOOL", True) is False, f"Failed for value: {value}"
    
    def test_env_bool_default_when_unset(self, monkeypatch):
        """Test env_bool returns default when variable unset"""
        monkeypatch.delenv("UNSET_VAR", raising=False)
        
        assert env_bool("UNSET_VAR", True) is True
        assert env_bool("UNSET_VAR", False) is False
    
    def test_env_int_valid_values(self, monkeypatch):
        """Test env_int with valid integer strings"""
        monkeypatch.setenv("TEST_INT", "42")
        assert env_int("TEST_INT", 0) == 42
        
        monkeypatch.setenv("TEST_INT", "-10")
        assert env_int("TEST_INT", 0) == -10
        
        monkeypatch.setenv("TEST_INT", "0")
        assert env_int("TEST_INT", 99) == 0
    
    def test_env_int_invalid_values(self, monkeypatch):
        """Test env_int returns default for invalid values"""
        monkeypatch.setenv("TEST_INT", "not_a_number")
        assert env_int("TEST_INT", 42) == 42
        
        monkeypatch.setenv("TEST_INT", "12.5")
        assert env_int("TEST_INT", 100) == 100
        
        monkeypatch.setenv("TEST_INT", "")
        assert env_int("TEST_INT", 50) == 50
    
    def test_env_int_default_when_unset(self, monkeypatch):
        """Test env_int returns default when variable unset"""
        monkeypatch.delenv("UNSET_INT", raising=False)
        assert env_int("UNSET_INT", 123) == 123
    
    def test_env_float_valid_values(self, monkeypatch):
        """Test env_float with valid float strings"""
        monkeypatch.setenv("TEST_FLOAT", "3.14159")
        assert abs(env_float("TEST_FLOAT", 0.0) - 3.14159) < 0.00001
        
        monkeypatch.setenv("TEST_FLOAT", "-2.5")
        assert env_float("TEST_FLOAT", 0.0) == -2.5
        
        monkeypatch.setenv("TEST_FLOAT", "42")
        assert env_float("TEST_FLOAT", 0.0) == 42.0
    
    def test_env_float_invalid_values(self, monkeypatch):
        """Test env_float returns default for invalid values"""
        monkeypatch.setenv("TEST_FLOAT", "not_a_float")
        assert env_float("TEST_FLOAT", 1.5) == 1.5
        
        monkeypatch.setenv("TEST_FLOAT", "")
        assert env_float("TEST_FLOAT", 2.0) == 2.0
    
    def test_env_float_default_when_unset(self, monkeypatch):
        """Test env_float returns default when variable unset"""
        monkeypatch.delenv("UNSET_FLOAT", raising=False)
        assert env_float("UNSET_FLOAT", 9.99) == 9.99
    
    def test_timestamp_functions_correlation(self):
        """Test that now_ms and now_s are correlated"""
        ms = now_ms()
        s = now_s()
        
        # Convert ms to seconds and compare (should be within 1 second)
        ms_as_s = ms / 1000.0
        assert abs(ms_as_s - s) < 1.0
