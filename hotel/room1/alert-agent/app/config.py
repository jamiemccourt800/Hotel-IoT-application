"""
Alert agent configuration.
"""
import os
from dataclasses import dataclass

@dataclass
class AlertConfig:
    """Alert agent configuration"""
    temp_high_c: float = 30.0
    temp_low_c: float = 15.0
    humidity_high_pct: float = 70.0
    humidity_low_pct: float = 30.0
    light_high_pct: float = 100.0
    light_low_pct: float = 0.0
    offline_timeout_s: int = 120
    dedup_window_s: int = 60
    
    @classmethod
    def from_env(cls) -> 'AlertConfig':
        """Create alert config from environment variables"""
        return cls(
            temp_high_c=float(os.getenv("TEMP_HIGH_C", "30.0")),
            temp_low_c=float(os.getenv("TEMP_LOW_C", "15.0")),
            humidity_high_pct=float(os.getenv("HUMIDITY_HIGH_PCT", "70.0")),
            humidity_low_pct=float(os.getenv("HUMIDITY_LOW_PCT", "30.0")),
            light_high_pct=float(os.getenv("LIGHT_HIGH_PCT", "100.0")),
            light_low_pct=float(os.getenv("LIGHT_LOW_PCT", "0.0")),
            offline_timeout_s=int(os.getenv("OFFLINE_TIMEOUT_S", "120")),
            dedup_window_s=int(os.getenv("DEDUP_WINDOW_S", "60"))
        )
