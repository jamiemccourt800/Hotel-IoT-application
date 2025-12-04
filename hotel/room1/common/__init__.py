"""
Common package initialization - exposes key classes for easy importing.
This eliminates the need for complex import paths across services.
"""
from .mqtt_client import HotelMQTTClient
from .logging import HotelLogger, get_logger  
from .schemas import TemperatureTelemetry, LightTelemetry, HumidityTelemetry, AlertMessage, MessageTags
from .config import DeviceConfig, MQTTConfig, TemperatureConfig, LightConfig, HumidityConfig
from .utils import now_ms, now_s, clamp_0_100, device_key
from .feature_flags import FeatureFlags

__all__ = [
    'HotelMQTTClient', 'HotelLogger', 'get_logger',
    'TemperatureTelemetry', 'LightTelemetry', 'HumidityTelemetry', 'AlertMessage', 'MessageTags',
    'DeviceConfig', 'MQTTConfig', 'TemperatureConfig', 'LightConfig', 'HumidityConfig',
    'now_ms', 'now_s', 'clamp_0_100', 'device_key',
    'FeatureFlags'
]