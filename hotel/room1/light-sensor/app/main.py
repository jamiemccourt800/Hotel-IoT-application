"""
Light sensor entry point - minimal orchestration only.
Replaces monolithic main.py with modular design.
"""
import sys
import os

# Add parent directories to path for common imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sensor import LightSensor
from config import LightConfig
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from common import DeviceConfig, MQTTConfig

def main():
    """Initialize and start light sensor"""
    # Load configuration from environment
    device_config = DeviceConfig.from_env("light-sensor")
    mqtt_config = MQTTConfig.from_env()
    light_config = LightConfig.from_env()
    
    # Initialize and start sensor
    sensor = LightSensor(device_config, mqtt_config, light_config)
    sensor.start()

if __name__ == "__main__":
    main()
