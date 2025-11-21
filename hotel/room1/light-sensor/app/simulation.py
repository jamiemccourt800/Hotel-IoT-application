"""
Light simulation algorithms extracted from existing main.py.
Implements time-of-day based light simulation.
"""
import time
import random
from typing import Iterator, Tuple

class LightSimulation:
    """Light simulation using time-of-day patterns"""
    
    def __init__(self, config):
        self.config = config
        self.current_brightness = 50  # Start at medium brightness
        
    def generate_readings(self) -> Iterator[Tuple[int, float]]:
        """Generate light readings using time-of-day simulation (extracted from existing logic)"""
        while True:
            # Calculate brightness based on time of day
            brightness = self._simulate_time_of_day()
            self.current_brightness = brightness
            
            timestamp = int(time.time() * 1000)
            yield timestamp, brightness
            
            # Sleep with speed control (matching original behavior)
            time.sleep(max(self.config.interval / max(self.config.speed, 0.01), 0.01))
    
    def _simulate_time_of_day(self) -> int:
        """
        Simulate ambient light based on time of day.
        
        Returns realistic light patterns:
        - Night (0-6am): Low light (0-20)
        - Morning (6-9am): Rising light (20-80)
        - Day (9am-6pm): High light (80-100)
        - Evening (6-10pm): Falling light (80-20)
        - Night (10pm-12am): Low light (20-0)
        """
        # Get current hour of day (0-23)
        current_hour = time.localtime().tm_hour
        
        # Base light level from time of day
        if 0 <= current_hour < 6:  # Night
            base = 10
        elif 6 <= current_hour < 9:  # Morning sunrise
            # Gradual increase from 10 to 80
            progress = (current_hour - 6) / 3.0
            base = int(10 + (70 * progress))
        elif 9 <= current_hour < 18:  # Daytime
            base = 90
        elif 18 <= current_hour < 22:  # Evening sunset
            # Gradual decrease from 80 to 20
            progress = (current_hour - 18) / 4.0
            base = int(80 - (60 * progress))
        else:  # Late night (22-24)
            base = 10
        
        # Add some random variation (+/- 10)
        variation = random.randint(-10, 10)
        brightness = base + variation
        
        # Clamp to valid range
        brightness = max(0, min(100, brightness))
        
        return brightness

