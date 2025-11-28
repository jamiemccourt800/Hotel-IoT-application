"""
Integration tests for hotel/room1/common/logging.py
Tests real logging behavior with MQTT integration
"""
import pytest
import time
from io import StringIO
import sys
from hotel.room1.common.logging import HotelLogger, get_logger


@pytest.mark.integration
@pytest.mark.timeout(5)
class TestLoggingIntegration:
    """Test structured logging in integration context"""
    
    def test_logger_creates_structured_output(self, capsys):
        """Verify logger produces correctly formatted log entries"""
        logger = HotelLogger("test-service", hotel_id="hotel1", room="101", sensor="temp")
        
        logger.info("test-event", "test message", extra_field="value")
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "INFO" in output
        assert "test-service" in output
        assert "hotel1/101/temp" in output
        assert "event=test-event" in output
        assert 'msg="test message"' in output
        assert "extra_field=value" in output
    
    def test_logger_warning_level(self, capsys):
        """Test warning level logging"""
        logger = HotelLogger("sensor", hotel_id="h1", room="202", sensor="humidity")
        
        logger.warning("sensor-drift", "humidity reading unstable", drift=5.2)
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "WARN" in output.upper()
        assert "sensor-drift" in output
        assert "drift=5.2" in output
    
    def test_logger_error_level(self, capsys):
        """Test error level logging"""
        logger = HotelLogger("actuator", hotel_id="h2", room="303", sensor="light")
        
        logger.error("actuator-failure", "failed to set brightness", error_code=42)
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "ERROR" in output
        assert "actuator-failure" in output
        assert "error_code=42" in output
    
    def test_logger_overrides_device_info(self, capsys):
        """Test that per-call device info overrides instance defaults"""
        logger = HotelLogger("service", hotel_id="default", room="999", sensor="default")
        
        logger.info("override-test", "custom device", hotel_id="custom", room="123", sensor="override")
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "custom/123/override" in output
        assert "default/999/default" not in output
    
    def test_logger_boolean_formatting(self, capsys):
        """Test that boolean values are formatted as lowercase"""
        logger = HotelLogger("test", hotel_id="h1", room="1", sensor="s1")
        
        logger.info("bool-test", "testing booleans", enabled=True, disabled=False)
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "enabled=true" in output
        assert "disabled=false" in output
        # Ensure not capitalized
        assert "True" not in output
        assert "False" not in output
    
    def test_get_logger_factory(self, capsys):
        """Test get_logger factory function"""
        # Create a simple object with attributes
        class DeviceConfig:
            def __init__(self):
                self.hotel_id = 'factory-hotel'
                self.room = '404'
                self.sensor = 'factory-sensor'
        
        device_config = DeviceConfig()
        logger = get_logger("factory-service", device_config)
        logger.info("factory-test", "logger from factory")
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "factory-service" in output
        assert "factory-hotel/404/factory-sensor" in output
    
    def test_logger_timestamp_format(self, capsys):
        """Verify timestamp format matches expected pattern"""
        logger = HotelLogger("ts-test", hotel_id="h1", room="1", sensor="s1")
        
        before = time.time()
        logger.info("timestamp-test", "checking timestamp")
        after = time.time()
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Timestamp should be ISO-8601 format with milliseconds
        assert "T" in output
        assert "Z" in output
        # Should contain date components
        assert "2025" in output or "2024" in output or "2026" in output
    
    def test_logger_room_conversion_to_string(self, capsys):
        """Test that room numbers are converted to strings"""
        logger = HotelLogger("service", hotel_id="h1", room=101, sensor="temp")
        
        logger.info("room-test", "room as integer")
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Room should be in device string as "101" not 101
        assert "h1/101/temp" in output
