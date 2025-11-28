"""Unit tests for common/logging.py"""
import pytest
import time
from io import StringIO
import sys
from common.logging import HotelLogger, get_logger
from common.config import DeviceConfig


class TestHotelLogger:
    """Test HotelLogger structured logging"""
    
    def test_logger_initialization(self):
        """Test logger initializes with correct attributes"""
        logger = HotelLogger("test-service", "hotel_01", "101", "temperature")
        assert logger.service_name == "test-service"
        assert logger.hotel_id == "hotel_01"
        assert logger.room == "101"
        assert logger.sensor == "temperature"
        
    def test_logger_default_values(self):
        """Test logger uses default values when not provided"""
        logger = HotelLogger("test-service")
        assert logger.service_name == "test-service"
        assert logger.hotel_id == "unknown"
        assert logger.room == "unknown"
        assert logger.sensor == "unknown"
        
    def test_logger_converts_room_to_string(self):
        """Test room number is converted to string"""
        logger = HotelLogger("test-service", "hotel_01", 101, "temperature")
        assert logger.room == "101"
        assert isinstance(logger.room, str)
        
    def test_log_method_output_format(self, capsys):
        """Test log method produces correctly formatted output"""
        logger = HotelLogger("test-service", "hotel_01", "101", "temperature")
        logger.log("INFO", "test-event", "test message", extra_field="value")
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Verify output contains expected components
        assert "INFO" in output
        assert "test-service" in output
        assert "hotel_01/101/temperature" in output
        assert "event=test-event" in output
        assert 'msg="test message"' in output
        assert "extra_field=value" in output
        
    def test_log_timestamp_format(self, capsys):
        """Test log timestamp is in correct ISO format with milliseconds"""
        logger = HotelLogger("test-service")
        logger.log("INFO", "test-event", "test message")
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Timestamp should be at start and end with 'Z'
        assert output[0].isdigit()  # Starts with year
        assert "T" in output[:20]  # Contains time separator
        assert "Z" in output[:30]  # Contains UTC indicator
        
    def test_log_boolean_fields_lowercase(self, capsys):
        """Test boolean fields are converted to lowercase strings"""
        logger = HotelLogger("test-service")
        logger.log("INFO", "test-event", "test message", enabled=True, disabled=False)
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "enabled=true" in output
        assert "disabled=false" in output
        
    def test_log_device_override(self, capsys):
        """Test device information can be overridden per log call"""
        logger = HotelLogger("test-service", "hotel_01", "101", "temperature")
        logger.log("INFO", "test-event", "test message", 
                  hotel_id="hotel_02", room="202", sensor="humidity")
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "hotel_02/202/humidity" in output
        
    def test_info_method(self, capsys):
        """Test info convenience method"""
        logger = HotelLogger("test-service")
        logger.info("test-event", "info message", field1="value1")
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "INFO" in output
        assert "event=test-event" in output
        assert 'msg="info message"' in output
        assert "field1=value1" in output
        
    def test_warning_method(self, capsys):
        """Test warning convenience method"""
        logger = HotelLogger("test-service")
        logger.warning("alert-event", "warning message", severity="medium")
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "WARNING" in output
        assert "event=alert-event" in output
        assert 'msg="warning message"' in output
        assert "severity=medium" in output
        
    def test_error_method(self, capsys):
        """Test error convenience method"""
        logger = HotelLogger("test-service")
        logger.error("error-event", "error message", error_code=500)
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "ERROR" in output
        assert "event=error-event" in output
        assert 'msg="error message"' in output
        assert "error_code=500" in output
        
    def test_multiple_extra_fields(self, capsys):
        """Test multiple additional fields are included"""
        logger = HotelLogger("test-service")
        logger.log("INFO", "test-event", "test message", 
                  field1="value1", field2=42, field3=3.14, field4=True)
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "field1=value1" in output
        assert "field2=42" in output
        assert "field3=3.14" in output
        assert "field4=true" in output


class TestGetLogger:
    """Test get_logger factory function"""
    
    def test_get_logger_with_config(self):
        """Test get_logger creates logger with device config"""
        config = DeviceConfig(
            hotel_id="hotel_01",
            room=101,
            sensor="temperature"
        )
        logger = get_logger("test-service", config)
        
        assert logger.service_name == "test-service"
        assert logger.hotel_id == "hotel_01"
        assert logger.room == "101"
        assert logger.sensor == "temperature"
        
    def test_get_logger_without_config(self):
        """Test get_logger creates logger without device config"""
        logger = get_logger("test-service")
        
        assert logger.service_name == "test-service"
        assert logger.hotel_id == "unknown"
        assert logger.room == "unknown"
        assert logger.sensor == "unknown"
        
    def test_get_logger_with_none_config(self):
        """Test get_logger handles None config gracefully"""
        logger = get_logger("test-service", None)
        
        assert logger.service_name == "test-service"
        assert logger.hotel_id == "unknown"
