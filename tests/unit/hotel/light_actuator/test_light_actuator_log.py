# test_light_actuator_log.py - Unit tests for light_actuator logging and utility functions

import pytest
from tests.conftest import load_module_from_path

LIGHT_ACTUATOR = load_module_from_path(
    "light_actuator",
    "hotel/room1/light-actuator/logic/main.py",
)

def test_log_function_exists():
    """Test that the log function exists in the light actuator module."""
    assert hasattr(LIGHT_ACTUATOR, "log")
    assert callable(LIGHT_ACTUATOR.log)

def test_log_function_basic(capsys):
    """Test basic logging functionality."""
    LIGHT_ACTUATOR.log("INFO", "test-event", "test message", extra_field="value")
    captured = capsys.readouterr()
    assert "INFO" in captured.out
    assert "test-event" in captured.out
    assert "test message" in captured.out

def test_log_function_with_boolean(capsys):
    """Test logging with boolean fields."""
    LIGHT_ACTUATOR.log("INFO", "test-event", "test with bool", is_active=True, is_ready=False)
    captured = capsys.readouterr()
    assert "INFO" in captured.out
    assert "test-event" in captured.out
    assert "is_active=true" in captured.out  # Boolean should be lowercase
    assert "is_ready=false" in captured.out  # Boolean should be lowercase

def test_build_state_function():
    """Test the build_state function."""
    state = LIGHT_ACTUATOR.build_state("hotel_01", "101", "light-actuator", True, 75, 22.5)
    assert state["measurement"] == "state"
    assert state["tags"]["hotel_id"] == "hotel_01"
    assert state["tags"]["room"] == "101"
    assert state["fields"]["on"] is True
    assert state["fields"]["brightness"] == 75

def test_build_state_without_temperature():
    """Test build_state without temperature."""
    state = LIGHT_ACTUATOR.build_state("hotel_01", "101", "light-actuator", False, 0, None)
    assert state["measurement"] == "state"
    assert state["fields"]["on"] is False
    assert state["fields"]["brightness"] == 0
    assert "temperature" not in state["fields"]  # Temperature not included when None

def test_build_alert_function():
    """Test the build_alert function."""
    alert = LIGHT_ACTUATOR.build_alert("hotel_01", "101", "light-actuator", "actuator_online", "INFO")
    assert alert["measurement"] == "alert"
    assert alert["tags"]["hotel_id"] == "hotel_01"
    assert alert["tags"]["room"] == "101"
    assert alert["tags"]["sensor"] == "light-actuator"
    assert alert["fields"]["kind"] == "actuator_online"
    assert alert["fields"]["severity"] == "INFO"

def test_build_ack_function():
    """Test the build_ack function."""
    ack = LIGHT_ACTUATOR.build_ack("corr-123", "hotel_01", "101", "light-actuator", "ok", "")
    assert ack["correlationId"] == "corr-123"  # Note: correlationId not correlation_id
    assert ack["tags"]["hotel_id"] == "hotel_01"
    assert ack["fields"]["status"] == "ok"  # status is in fields, not top-level

def test_clamp_0_100():
    """Test the clamp_0_100 function."""
    assert LIGHT_ACTUATOR.clamp_0_100(50) == 50
    assert LIGHT_ACTUATOR.clamp_0_100(0) == 0
    assert LIGHT_ACTUATOR.clamp_0_100(100) == 100
    assert LIGHT_ACTUATOR.clamp_0_100(-10) == 0
    assert LIGHT_ACTUATOR.clamp_0_100(150) == 100

def test_env_bool():
    """Test the env_bool function."""
    assert LIGHT_ACTUATOR.env_bool("NONEXISTENT_VAR", True) is True
    assert LIGHT_ACTUATOR.env_bool("NONEXISTENT_VAR", False) is False

def test_env_bool_with_env_values(monkeypatch):
    """Test env_bool with actual environment values."""
    monkeypatch.setenv("TEST_BOOL_TRUE", "true")
    assert LIGHT_ACTUATOR.env_bool("TEST_BOOL_TRUE", False) is True
    
    monkeypatch.setenv("TEST_BOOL_1", "1")
    assert LIGHT_ACTUATOR.env_bool("TEST_BOOL_1", False) is True
    
    monkeypatch.setenv("TEST_BOOL_YES", "yes")
    assert LIGHT_ACTUATOR.env_bool("TEST_BOOL_YES", False) is True
    
    monkeypatch.setenv("TEST_BOOL_ON", "on")
    assert LIGHT_ACTUATOR.env_bool("TEST_BOOL_ON", False) is True
    
    monkeypatch.setenv("TEST_BOOL_FALSE", "false")
    assert LIGHT_ACTUATOR.env_bool("TEST_BOOL_FALSE", True) is False
    
    monkeypatch.setenv("TEST_BOOL_0", "0")
    assert LIGHT_ACTUATOR.env_bool("TEST_BOOL_0", True) is False

def test_env_int():
    """Test the env_int function."""
    assert LIGHT_ACTUATOR.env_int("NONEXISTENT_VAR", 42) == 42
    assert LIGHT_ACTUATOR.env_int("NONEXISTENT_VAR", 0) == 0

def test_env_int_with_env_values(monkeypatch):
    """Test env_int with actual environment values."""
    monkeypatch.setenv("TEST_INT", "123")
    assert LIGHT_ACTUATOR.env_int("TEST_INT", 0) == 123
    
    monkeypatch.setenv("TEST_INT_INVALID", "not-a-number")
    assert LIGHT_ACTUATOR.env_int("TEST_INT_INVALID", 42) == 42  # Falls back to default

def test_now_ms():
    """Test the now_ms function returns a timestamp."""
    ts = LIGHT_ACTUATOR.now_ms()
    assert isinstance(ts, int)
    assert ts > 0

def test_light_actuator_environment_variables():
    """Test that light actuator uses correct environment variable names matching docker-compose."""
    # These should match the environment variables used in docker-compose.test.hotel.yml
    # and hotel/docker-compose.hotel1.yml
    assert hasattr(LIGHT_ACTUATOR, 'HOTEL_ID')
    assert hasattr(LIGHT_ACTUATOR, 'ROOM')
    assert hasattr(LIGHT_ACTUATOR, 'SENSOR')
    assert hasattr(LIGHT_ACTUATOR, 'BROKER')
    assert hasattr(LIGHT_ACTUATOR, 'BROKER_PORT')
    assert hasattr(LIGHT_ACTUATOR, 'QOS')
    assert hasattr(LIGHT_ACTUATOR, 'KEEPALIVE')
    
    # Check types and default values match production config
    assert isinstance(LIGHT_ACTUATOR.HOTEL_ID, str)
    assert LIGHT_ACTUATOR.HOTEL_ID == "hotel_01"  # Matches docker-compose
    assert isinstance(LIGHT_ACTUATOR.ROOM, str)
    assert LIGHT_ACTUATOR.ROOM == "101"  # Matches docker-compose
    assert isinstance(LIGHT_ACTUATOR.SENSOR, str)
    assert LIGHT_ACTUATOR.SENSOR == "light-actuator"  # Matches docker-compose
    assert isinstance(LIGHT_ACTUATOR.BROKER, str)
    assert LIGHT_ACTUATOR.BROKER == "mosquitto"  # Matches docker-compose
    assert isinstance(LIGHT_ACTUATOR.BROKER_PORT, int)
    assert LIGHT_ACTUATOR.BROKER_PORT == 1883  # Matches docker-compose
    assert isinstance(LIGHT_ACTUATOR.QOS, int)
    assert LIGHT_ACTUATOR.QOS == 1  # Matches docker-compose
    assert isinstance(LIGHT_ACTUATOR.KEEPALIVE, int)
    assert LIGHT_ACTUATOR.KEEPALIVE == 60  # Matches docker-compose
