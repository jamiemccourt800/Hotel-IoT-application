"""
Temperature sensor entry point - minimal orchestration only.
Replaces 200+ line monolithic main.py with 25 lines.
"""
import sys
import os

# Add parent directories to path for common imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sensor import TemperatureSensor
from config import TemperatureConfig
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from common import DeviceConfig, MQTTConfig

def main():
    """Initialize and start temperature sensor"""
    # Load configuration from environment
    device_config = DeviceConfig.from_env("temperature-sensor")
    mqtt_config = MQTTConfig.from_env()
    temp_config = TemperatureConfig.from_env()
    
    # Initialize and start sensor
    sensor = TemperatureSensor(device_config, mqtt_config, temp_config)
    sensor.start()

if __name__ == "__main__":
    main()