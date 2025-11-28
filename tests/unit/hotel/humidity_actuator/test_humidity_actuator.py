"""
Unit tests for humidity actuator control logic.
Tests deadband control, external commands, and mode management.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import json

# Import from humidity-actuator/app
import sys
sys.path.insert(0, 'hotel/room1/humidity-actuator/app')
from actuator import HumidityActuator


@pytest.fixture
def device_config():
    config = Mock()
    config.hotel_id = "hotel_01"
    config.room = 101
    config.sensor = "humidifier"
    return config


@pytest.fixture
def mqtt_config():
    config = Mock()
    config.broker = "localhost"
    config.port = 1883
    config.qos = 1
    config.keepalive = 60
    return config


@pytest.fixture
def humidity_config():
    config = Mock()
    config.default_target = 50.0
    config.deadband = 2.0
    config.max_humidification = 100.0
    config.max_dehumidification = 100.0
    config.control_interval = 5.0
    return config


class TestHumidityActuator:
    
    def test_initialization(self, device_config, mqtt_config, humidity_config):
        """Test actuator initializes in local control mode"""
        with patch('actuator.HotelMQTTClient'), patch('actuator.get_logger'):
            actuator = HumidityActuator(device_config, mqtt_config, humidity_config)
            assert actuator.external_control_mode == False
            
    def test_process_command_enables_external_mode(self, device_config, mqtt_config, humidity_config):
        """Test receiving command enables external control mode"""
        with patch('actuator.HotelMQTTClient') as mock_mqtt, patch('actuator.get_logger'), patch('actuator.now_ms'):
            mock_client = MagicMock()
            mock_mqtt.return_value.client = mock_client
            
            actuator = HumidityActuator(device_config, mqtt_config, humidity_config)
            
            command = {
                "fields": {"target_humidity": 60.0},
                "correlationId": "test-123"
            }
            
            actuator._process_command(command, "commands/humidity/hotel_01/101/humidifier")
            
            assert actuator.external_control_mode == True
            
    def test_process_command_sets_target(self, device_config, mqtt_config, humidity_config):
        """Test command sets humidity target"""
        with patch('actuator.HotelMQTTClient') as mock_mqtt, patch('actuator.get_logger'), patch('actuator.now_ms'):
            mock_client = MagicMock()
            mock_mqtt.return_value.client = mock_client
            
            actuator = HumidityActuator(device_config, mqtt_config, humidity_config)
            
            command = {
                "fields": {"target_humidity": 60.0},
                "correlationId": "test-123"
            }
            
            actuator._process_command(command, "commands/humidity/hotel_01/101/humidifier")
            
            assert actuator.humidifier.target_humidity == 60.0
