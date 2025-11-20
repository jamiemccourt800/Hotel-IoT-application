"""
Common utility functions used across services.
Eliminates duplicate helper functions and provides consistent implementations.
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