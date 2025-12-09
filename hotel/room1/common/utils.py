"""Common utility functions used across services.
Eliminates duplicate helper functions and provides consistent implementations.

Usage:
------
from common import now_ms, clamp_0_100, env_bool, validate_temperature_range

# Timestamps
timestamp = now_ms()  # Milliseconds since epoch for telemetry

# Value clamping
brightness = clamp_0_100(user_input)  # Ensures 0-100 range

# Environment variable parsing with defaults
debug_mode = env_bool('DEBUG_MODE', default=False)
max_retries = env_int('MAX_RETRIES', default=3)
target_temp = env_float('TARGET_TEMP', default=21.0)

# Validation
if validate_temperature_range(temp):
    process_temperature(temp)

Exported Functions:
------------------
- now_ms(), now_s():                  Timestamp utilities
- clamp_0_100(), device_key():        Value manipulation
- env_bool(), env_int(), env_float(): Environment parsing
- validate_*_range():                 Input validation
"""
import time
from typing import Union

def now_ms() -> int:
    """Current timestamp in milliseconds since epoch"""
    return int(time.time() * 1000)

def now_s() -> float:
    """Current timestamp in seconds since epoch"""
    return time.time()

def clamp_0_100(v: Union[int, float]) -> int:
    """Clamp value to 0-100 range for percentages (brightness, humidity, etc.)"""
    return 0 if v < 0 else 100 if v > 100 else int(v)

def device_key(hotel_id: str, room: str, sensor: str) -> str:
    """Generate unique device key for deduplication and tracking"""
    return f"{hotel_id}:{room}:{sensor}"

def env_bool(name: str, default: bool) -> bool:
    """
    Read a boolean environment variable.
    Accepts: 1, true, yes, on (case insensitive) as True.
    Anything else (including unset) returns default.
    """
    import os
    v = os.environ.get(name)
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "on")

def env_int(name: str, default: int) -> int:
    """
    Read an integer environment variable.
    Returns default if unset or malformed.
    """
    import os
    try:
        return int(os.environ.get(name, str(default)))
    except (ValueError, TypeError):
        return default

def env_float(name: str, default: float) -> float:
    """
    Read a float environment variable.
    Returns default if unset or malformed.
    """
    import os
    try:
        return float(os.environ.get(name, str(default)))
    except (ValueError, TypeError):
        return default

def validate_temperature_range(temp: float, min_temp: float = -50.0, max_temp: float = 120.0) -> bool:
    """Validate temperature is within acceptable physical range"""
    return min_temp <= temp <= max_temp

def validate_humidity_range(humidity: float) -> bool:
    """Validate humidity is within 0-100% range"""
    return 0.0 <= humidity <= 100.0

def validate_brightness_range(brightness: int) -> bool:
    """Validate brightness is within 0-100 range"""
    return 0 <= brightness <= 100