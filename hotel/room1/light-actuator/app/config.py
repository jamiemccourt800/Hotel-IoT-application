"""
Light actuator configuration.
"""
import os
from dataclasses import dataclass

@dataclass
class LightControllerConfig:
    """Light controller configuration"""
    default_brightness: float = 75.0
    control_interval: float = 5.0  # Control loop frequency in seconds
    
    @classmethod
    def from_env(cls) -> 'LightControllerConfig':
        """Create light controller config from environment variables"""
        return cls(
            default_brightness=float(os.getenv("DEFAULT_BRIGHTNESS", "75.0")),
            control_interval=float(os.getenv("CONTROL_INTERVAL", "5.0"))
        )
