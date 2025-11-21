"""
Environment-based configuration management with type safety.
Eliminates scattered os.getenv() calls across services and provides validation.
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class MQTTConfig:
    """MQTT connection configuration"""
    broker: str = "mosquitto"
    port: int = 1883
    qos: int = 1
    keepalive: int = 60
    
    @classmethod
    def from_env(cls) -> 'MQTTConfig':
        """Create MQTT config from environment variables"""
        return cls(
            broker=os.getenv("MQTT_BROKER", "mosquitto"),
            port=int(os.getenv("MQTT_PORT", "1883")),
            qos=int(os.getenv("QOS", "1")),
            keepalive=int(os.getenv("KEEPALIVE", "60"))
        )

@dataclass  
class DeviceConfig:
    """Device identification configuration"""
    hotel_id: str = "hotel_01"
    room: int = 101 
    sensor: str = "device"
    
    @classmethod
    def from_env(cls, default_sensor: str) -> 'DeviceConfig':
        """Create device config from environment variables"""
        return cls(
            hotel_id=os.getenv("HOTEL_ID", "hotel_01"),
            room=int(os.getenv("ROOM", "101")),  # Convert to int to match schema
            sensor=os.getenv("SENSOR", default_sensor)
        )

@dataclass
class TemperatureConfig:
    """Temperature sensor/actuator configuration"""
    target_temp: float = 21.0
    interval: float = 1.0
    speed: float = 1.0
    high_threshold: float = 30.0
    
    @classmethod
    def from_env(cls) -> 'TemperatureConfig':
        """Create temperature config from environment variables"""
        return cls(
            target_temp=float(os.getenv("TARGET_TEMP", "21.0")),
            interval=float(os.getenv("INTERVAL", "1.0")),
            speed=float(os.getenv("SPEED", "1.0")),
            high_threshold=float(os.getenv("TEMP_HIGH_C", "30.0"))
        )
        
@dataclass
class LightConfig:
    """Light sensor/actuator configuration"""
    initial_on: bool = True
    initial_brightness: int = 100
    auto_mode: bool = False
    
    @classmethod
    def from_env(cls) -> 'LightConfig':
        """Create light config from environment variables"""
        return cls(
            initial_on=os.getenv("INITIAL_ON", "true").lower() in ("1", "true", "yes", "on"),
            initial_brightness=int(os.getenv("INITIAL_BRIGHTNESS", "100")),
            auto_mode=os.getenv("AUTO_MODE", "false").lower() in ("1", "true", "yes", "on")
        )
        
@dataclass  
class HumidityConfig:
    """Humidity sensor/actuator configuration"""
    target_humidity: float = 50.0
    high_threshold: float = 70.0
    low_threshold: float = 30.0
    interval: float = 1.0
    
    @classmethod
    def from_env(cls) -> 'HumidityConfig':
        """Create humidity config from environment variables"""
        return cls(
            target_humidity=float(os.getenv("TARGET_HUMIDITY", "50.0")),
            high_threshold=float(os.getenv("HUMIDITY_HIGH", "70.0")),
            low_threshold=float(os.getenv("HUMIDITY_LOW", "30.0")),
            interval=float(os.getenv("INTERVAL", "1.0"))
        )