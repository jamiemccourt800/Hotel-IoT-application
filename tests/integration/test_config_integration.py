"""
Integration tests for hotel/room1/common/config.py
Tests configuration loading from environment variables
"""
import pytest
import os
from hotel.room1.common.config import (
    MQTTConfig, DeviceConfig, TemperatureConfig,
    LightConfig, HumidityConfig
)


@pytest.mark.integration
@pytest.mark.timeout(5)
class TestConfigIntegration:
    """Test configuration management in integration context"""
    
    def test_mqtt_config_from_env(self, monkeypatch):
        """Test MQTTConfig loads from environment variables"""
        monkeypatch.setenv("MQTT_BROKER", "test-broker")
        monkeypatch.setenv("MQTT_PORT", "1234")
        monkeypatch.setenv("QOS", "2")
        monkeypatch.setenv("KEEPALIVE", "120")
        
        config = MQTTConfig.from_env()
        
        assert config.broker == "test-broker"
        assert config.port == 1234
        assert config.qos == 2
        assert config.keepalive == 120
    
    def test_mqtt_config_defaults(self, monkeypatch):
        """Test MQTTConfig uses defaults when env vars not set"""
        # Clear env vars
        for key in ["MQTT_BROKER", "MQTT_PORT", "QOS", "KEEPALIVE"]:
            monkeypatch.delenv(key, raising=False)
        
        config = MQTTConfig.from_env()
        
        assert config.broker == "mosquitto"
        assert config.port == 1883
        assert config.qos == 1
        assert config.keepalive == 60
    
    def test_mqtt_config_string_representation(self):
        """Test MQTTConfig __str__ method for debugging"""
        config = MQTTConfig(broker="localhost", port=1883, qos=1, keepalive=60)
        config_str = str(config)
        
        assert "MQTTConfig" in config_str
        assert "broker" in config_str.lower() or "localhost" in config_str
    
    def test_device_config_from_env(self, monkeypatch):
        """Test DeviceConfig loads from environment variables"""
        monkeypatch.setenv("HOTEL_ID", "hotel_42")
        monkeypatch.setenv("ROOM", "555")
        monkeypatch.setenv("SENSOR", "test-sensor")
        
        config = DeviceConfig.from_env("default-sensor")
        
        assert config.hotel_id == "hotel_42"
        assert config.room == 555
        assert config.sensor == "test-sensor"
    
    def test_device_config_defaults(self, monkeypatch):
        """Test DeviceConfig uses defaults when env vars not set"""
        for key in ["HOTEL_ID", "ROOM", "SENSOR"]:
            monkeypatch.delenv(key, raising=False)
        
        config = DeviceConfig.from_env("my-sensor")
        
        assert config.hotel_id == "hotel_01"
        assert config.room == 101
        assert config.sensor == "my-sensor"  # Uses parameter default
    
    def test_device_config_string_representation(self):
        """Test DeviceConfig __str__ for debugging"""
        config = DeviceConfig(hotel_id="h1", room=202, sensor="temp")
        config_str = str(config)
        
        assert "DeviceConfig" in config_str
        assert "h1" in config_str or "hotel_id" in config_str.lower()
    
    def test_temperature_config_from_env(self, monkeypatch):
        """Test TemperatureConfig loads from environment"""
        monkeypatch.setenv("TARGET_TEMP", "22.5")
        monkeypatch.setenv("INTERVAL", "2.0")
        monkeypatch.setenv("SPEED", "1.5")
        monkeypatch.setenv("TEMP_HIGH_C", "35.0")
        
        config = TemperatureConfig.from_env()
        
        assert config.target_temp == 22.5
        assert config.interval == 2.0
        assert config.speed == 1.5
        assert config.high_threshold == 35.0
    
    def test_temperature_config_defaults(self, monkeypatch):
        """Test TemperatureConfig defaults"""
        for key in ["TARGET_TEMP", "INTERVAL", "SPEED", "TEMP_HIGH_C"]:
            monkeypatch.delenv(key, raising=False)
        
        config = TemperatureConfig.from_env()
        
        assert config.target_temp == 21.0
        assert config.interval == 1.0
        assert config.speed == 1.0
        assert config.high_threshold == 30.0
    
    def test_temperature_config_string_representation(self):
        """Test TemperatureConfig __str__ for debugging"""
        config = TemperatureConfig(target_temp=21.0, interval=1.0, speed=1.0, high_threshold=30.0)
        config_str = str(config)
        
        assert "TemperatureConfig" in config_str
    
    def test_light_config_from_env(self, monkeypatch):
        """Test LightConfig loads from environment"""
        monkeypatch.setenv("INITIAL_ON", "false")
        monkeypatch.setenv("INITIAL_BRIGHTNESS", "50")
        monkeypatch.setenv("AUTO_MODE", "true")
        
        config = LightConfig.from_env()
        
        assert config.initial_on is False
        assert config.initial_brightness == 50
        assert config.auto_mode is True
    
    def test_light_config_boolean_parsing(self, monkeypatch):
        """Test LightConfig correctly parses boolean strings"""
        # Test various truthy values
        for value in ["1", "true", "TRUE", "yes", "on"]:
            monkeypatch.setenv("INITIAL_ON", value)
            config = LightConfig.from_env()
            assert config.initial_on is True, f"Failed for value: {value}"
        
        # Test falsy values
        for value in ["0", "false", "no", "off", "random"]:
            monkeypatch.setenv("INITIAL_ON", value)
            config = LightConfig.from_env()
            assert config.initial_on is False, f"Failed for value: {value}"
    
    def test_light_config_defaults(self, monkeypatch):
        """Test LightConfig defaults"""
        for key in ["INITIAL_ON", "INITIAL_BRIGHTNESS", "AUTO_MODE"]:
            monkeypatch.delenv(key, raising=False)
        
        config = LightConfig.from_env()
        
        assert config.initial_on is True
        assert config.initial_brightness == 100
        assert config.auto_mode is False
    
    def test_light_config_string_representation(self):
        """Test LightConfig __str__ for debugging"""
        config = LightConfig(initial_on=True, initial_brightness=100, auto_mode=False)
        config_str = str(config)
        
        assert "LightConfig" in config_str
    
    def test_humidity_config_from_env(self, monkeypatch):
        """Test HumidityConfig loads from environment"""
        monkeypatch.setenv("TARGET_HUMIDITY", "55.0")
        monkeypatch.setenv("HUMIDITY_HIGH", "75.0")
        monkeypatch.setenv("HUMIDITY_LOW", "25.0")
        monkeypatch.setenv("INTERVAL", "2.5")
        
        config = HumidityConfig.from_env()
        
        assert config.target_humidity == 55.0
        assert config.high_threshold == 75.0
        assert config.low_threshold == 25.0
        assert config.interval == 2.5
    
    def test_humidity_config_defaults(self, monkeypatch):
        """Test HumidityConfig defaults"""
        for key in ["TARGET_HUMIDITY", "HUMIDITY_HIGH", "HUMIDITY_LOW", "INTERVAL"]:
            monkeypatch.delenv(key, raising=False)
        
        config = HumidityConfig.from_env()
        
        assert config.target_humidity == 50.0
        assert config.high_threshold == 70.0
        assert config.low_threshold == 30.0
        assert config.interval == 1.0
    
    def test_humidity_config_string_representation(self):
        """Test HumidityConfig __str__ for debugging"""
        config = HumidityConfig(target_humidity=50.0, high_threshold=70.0, 
                                low_threshold=30.0, interval=1.0)
        config_str = str(config)
        
        assert "HumidityConfig" in config_str
