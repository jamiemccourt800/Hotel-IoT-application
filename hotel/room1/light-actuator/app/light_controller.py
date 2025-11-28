"""
Light control algorithms for smart lighting management.
Implements simple on/off/dimming control.
"""
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum

class LightMode(Enum):
    """Light operating modes"""
    OFF = "off"
    ON = "on"
    AUTO = "auto"

@dataclass
class ControlOutput:
    """Light control output"""
    mode: LightMode
    brightness_level: float  # 0-100%
    current_brightness: float = None

class LightController:
    """Simple light controller with brightness control"""
    
    def __init__(self, config):
        self.config = config
        self.brightness_level = config.default_brightness
        self.current_brightness = None
        self.mode = LightMode.OFF
        
    def set_brightness(self, brightness: float):
        """Update brightness level (0-100)"""
        self.brightness_level = max(0.0, min(100.0, brightness))
        if self.brightness_level > 0:
            self.mode = LightMode.ON
        else:
            self.mode = LightMode.OFF
        
    def set_mode(self, mode: str):
        """Set light operating mode"""
        try:
            self.mode = LightMode(mode.lower())
            if self.mode == LightMode.OFF:
                self.brightness_level = 0.0
            elif self.mode == LightMode.ON and self.brightness_level == 0:
                self.brightness_level = self.config.default_brightness
        except ValueError:
            self.mode = LightMode.OFF
            
    def turn_on(self):
        """Turn light on at default brightness"""
        self.mode = LightMode.ON
        if self.brightness_level == 0:
            self.brightness_level = self.config.default_brightness
            
    def turn_off(self):
        """Turn light off"""
        self.mode = LightMode.OFF
        self.brightness_level = 0.0
        
    def toggle(self):
        """Toggle light on/off"""
        if self.mode == LightMode.OFF:
            self.turn_on()
        else:
            self.turn_off()
            
    def update_current_brightness(self, brightness: float):
        """Update current brightness reading from sensor"""
        self.current_brightness = brightness
        
    def calculate_control_output(self) -> ControlOutput:
        """Calculate light control output"""
        return ControlOutput(
            mode=self.mode,
            brightness_level=self.brightness_level,
            current_brightness=self.current_brightness
        )
