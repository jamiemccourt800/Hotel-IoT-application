"""
Unit tests for temperature sensor class.
Tests TemperatureSensor telemetry publishing and MQTT integration.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import json

# Import from temperature-sensor/app
import sys
sys.path.insert(0, 'hotel/room1/temperature-sensor/app')
from sensor import TemperatureSensor


@pytest.fixture
def device_config():
    config = Mock()
    config.hotel_id = "hotel_01"
    config.room = 101
    config.sensor = "temperature-sensor"
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
def temp_config():
    config = Mock()
    config.target_temp = 22.0
    config.start_temp = 20.0
    config.interval = 1.0
    config.speed = 1.0
    return config


class TestTemperatureSensor:
    
    def test_initialization(self, device_config, mqtt_config, temp_config):
        """Test sensor initializes with configs"""
        with patch('sensor.HotelMQTTClient'), patch('sensor.get_logger'):
            sensor = TemperatureSensor(device_config, mqtt_config, temp_config)
            assert sensor.device_config == device_config
            assert sensor.mqtt_config == mqtt_config
            assert sensor.temp_config == temp_config
            
    def test_creates_mqtt_client_and_simulation(self, device_config, mqtt_config, temp_config):
        """Test sensor creates MQTT client and simulation"""
        with patch('sensor.HotelMQTTClient') as mock_mqtt_class, \
             patch('sensor.TemperatureSimulation') as mock_sim_class, \
             patch('sensor.get_logger'):
            
            sensor = TemperatureSensor(device_config, mqtt_config, temp_config)
            
            mock_mqtt_class.assert_called_once()
            mock_sim_class.assert_called_once_with(temp_config)
            
    def test_telemetry_message_format(self, device_config, mqtt_config, temp_config):
        """Test telemetry messages have correct format"""
        # This tests the integration with TemperatureTelemetry schema
        with patch('sensor.HotelMQTTClient'), patch('sensor.get_logger'):
            from common.schemas import TemperatureTelemetry, MessageTags
            
            # Create telemetry message as sensor does
            message = TemperatureTelemetry(
                tags=MessageTags(
                    hotel_id="hotel_01",
                    room=101,
                    sensor="temperature-sensor"
                ),
                fields={"temperatureC": 22.5},
                timestamp=1234567890
            )
            
            payload = message.to_dict()
            
            assert payload["measurement"] == "temperature"
            assert payload["tags"]["hotel_id"] == "hotel_01"
            assert payload["tags"]["room"] == 101
            assert payload["fields"]["temperatureC"] == 22.5
            assert payload["timestamp"] == 1234567890
