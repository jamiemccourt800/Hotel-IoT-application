# test_alert_agent_log.py - Unit tests for alert_agent logging functions

import pytest
from tests.conftest import load_module_from_path

ALERT_AGENT = load_module_from_path(
    "alert_agent",
    "hotel/room1/alert-agent/app/main.py",
)

def test_log_function_exists():
    """Test that the log function exists in the alert agent module."""
    assert hasattr(ALERT_AGENT, "log")
    assert callable(ALERT_AGENT.log)

def test_log_function_basic(capsys):
    """Test basic logging functionality."""
    ALERT_AGENT.log("INFO", "test-event", "test message", extra_field="value")
    captured = capsys.readouterr()
    assert "INFO" in captured.out
    assert "test-event" in captured.out
    assert "test message" in captured.out

def test_log_function_with_boolean(capsys):
    """Test logging with boolean fields."""
    ALERT_AGENT.log("INFO", "test-event", "test with bool", is_alert=True, is_normal=False)
    captured = capsys.readouterr()
    assert "INFO" in captured.out
    assert "test-event" in captured.out
    assert "is_alert=true" in captured.out  # Boolean should be lowercase
    assert "is_normal=false" in captured.out  # Boolean should be lowercase

def test_device_key_function():
    """Test the device_key function."""
    tags = {"hotel_id": "hotel_01", "room": "101", "sensor": "temp-001"}
    key = ALERT_AGENT.device_key(tags)
    assert key == "hotel_01:101:temp-001"

def test_device_key_with_missing_tags():
    """Test device_key with missing tags."""
    tags = {"hotel_id": "hotel_01"}
    key = ALERT_AGENT.device_key(tags)
    assert "hotel_01" in key

def test_now_ms_function():
    """Test the now_ms function."""
    ts = ALERT_AGENT.now_ms()
    assert isinstance(ts, int)
    assert ts > 0

def test_now_s_function():
    """Test the now_s function."""
    ts = ALERT_AGENT.now_s()
    assert isinstance(ts, float)
    assert ts > 0

def test_should_emit_function():
    """Test the should_emit deduplication function."""
    # First call should emit
    result1 = ALERT_AGENT.should_emit("test-dedup-key-unique-123")
    assert result1 is True
    
    # Immediate second call should not emit (within dedup window)
    result2 = ALERT_AGENT.should_emit("test-dedup-key-unique-123")
    assert result2 is False

def test_alert_agent_environment_variables():
    """Test that alert agent uses correct environment variable names matching docker-compose."""
    # These should match the environment variables used in docker-compose.test.hotel.yml
    # and hotel/docker-compose.hotel1.yml
    assert hasattr(ALERT_AGENT, 'BROKER')
    assert hasattr(ALERT_AGENT, 'PORT')
    assert hasattr(ALERT_AGENT, 'SUB')
    assert hasattr(ALERT_AGENT, 'PUB')
    assert hasattr(ALERT_AGENT, 'HOTEL')
    assert hasattr(ALERT_AGENT, 'ROOM')
    assert hasattr(ALERT_AGENT, 'TEMP_HIGH_C')
    assert hasattr(ALERT_AGENT, 'OFFLINE_TIMEOUT_S')
    assert hasattr(ALERT_AGENT, 'DEDUP_WINDOW_S')
    
    # Check types and default values match production config
    assert isinstance(ALERT_AGENT.BROKER, str)
    assert ALERT_AGENT.BROKER == "mosquitto"  # Matches docker-compose
    assert isinstance(ALERT_AGENT.PORT, int)
    assert ALERT_AGENT.PORT == 1883  # Matches docker-compose
    assert isinstance(ALERT_AGENT.HOTEL, str)
    assert ALERT_AGENT.HOTEL == "hotel_01"  # Matches docker-compose
    assert isinstance(ALERT_AGENT.ROOM, str)
    assert ALERT_AGENT.ROOM == "101"  # Matches docker-compose
    assert isinstance(ALERT_AGENT.TEMP_HIGH_C, float)
    assert ALERT_AGENT.TEMP_HIGH_C == 28.0  # Code default (docker-compose overrides to 30)
    assert isinstance(ALERT_AGENT.OFFLINE_TIMEOUT_S, int)
    assert ALERT_AGENT.OFFLINE_TIMEOUT_S == 120  # Code default (docker-compose overrides to 45)
    assert isinstance(ALERT_AGENT.DEDUP_WINDOW_S, int)
    assert ALERT_AGENT.DEDUP_WINDOW_S == 60  # Code default (docker-compose overrides to 30)
