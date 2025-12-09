"""
Common Package - Shared Utilities for Hotel IoT Simulator
==========================================================

This module provides reusable components for all simulator services (sensors, actuators, agents).
It eliminates code duplication and ensures consistency across the system.

Module Organization:
-------------------
- MQTT:          HotelMQTTClient - Standardized MQTT connection and messaging
- Logging:       HotelLogger, get_logger - Structured logging across services
- Schemas:       Message types for MQTT communication (telemetry, commands, alerts)
- Config:        Environment-based configuration with type safety
- Utils:         Helper functions for time, validation, and environment parsing
- Feature Flags: GitLab Unleash integration for controlled feature rollout

Usage Examples:
--------------
# Basic imports used by most services
from common import (
    HotelMQTTClient, get_logger, DeviceConfig, MQTTConfig,
    TemperatureTelemetry, MessageTags, now_ms
)

# Feature flag integration (actuators)
from common import FeatureFlags

# Environment helpers for configuration
from common import env_bool, env_int, env_float

# Validation utilities
from common import validate_temperature_range, validate_humidity_range
"""

# ============================================================================
# MQTT Client
# ============================================================================
from .mqtt_client import HotelMQTTClient

# ============================================================================
# Logging
# ============================================================================
from .logging import HotelLogger, get_logger

# ============================================================================
# Message Schemas (MQTT Communication)
# ============================================================================
from .schemas import (
    MessageTags,
    BaseMessage,
    TemperatureTelemetry,
    LightTelemetry,
    HumidityTelemetry,
    AlertMessage,
    CommandMessage
)

# ============================================================================
# Configuration (Environment-based)
# ============================================================================
from .config import (
    DeviceConfig,
    MQTTConfig,
    TemperatureConfig,
    LightConfig,
    HumidityConfig
)

# ============================================================================
# Utility Functions
# ============================================================================
from .utils import (
    # Time utilities
    now_ms,
    now_s,
    
    # Value manipulation
    clamp_0_100,
    device_key,
    
    # Environment variable parsing
    env_bool,
    env_int,
    env_float,
    
    # Validation helpers
    validate_temperature_range,
    validate_humidity_range,
    validate_brightness_range
)

# ============================================================================
# Feature Flags (GitLab Unleash)
# ============================================================================
from .feature_flags import FeatureFlags

# ============================================================================
# Public API
# ============================================================================
__all__ = [
    # MQTT
    'HotelMQTTClient',
    
    # Logging
    'HotelLogger',
    'get_logger',
    
    # Schemas
    'MessageTags',
    'BaseMessage',
    'TemperatureTelemetry',
    'LightTelemetry',
    'HumidityTelemetry',
    'AlertMessage',
    'CommandMessage',
    
    # Configuration
    'DeviceConfig',
    'MQTTConfig',
    'TemperatureConfig',
    'LightConfig',
    'HumidityConfig',
    
    # Utilities
    'now_ms',
    'now_s',
    'clamp_0_100',
    'device_key',
    'env_bool',
    'env_int',
    'env_float',
    'validate_temperature_range',
    'validate_humidity_range',
    'validate_brightness_range',
    
    # Feature Flags
    'FeatureFlags'
]