"""
Humidity sensor entry point - minimal orchestration only.
Replaces 200+ line monolithic main.py with 25 lines.
"""
import sys
import os

# Add parent directories to path for common imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sensor import HumiditySensor
from config import HumidityConfig
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from common import DeviceConfig, MQTTConfig

def main():
    """Initialize and start humidity sensor"""
    # Load configuration from environment
    device_config = DeviceConfig.from_env("humidity-sensor")
    mqtt_config = MQTTConfig.from_env()
    humidity_config = HumidityConfig.from_env()
    
    # Initialize and start sensor
    sensor = HumiditySensor(device_config, mqtt_config, humidity_config)
    sensor.start()

if __name__ == "__main__":
    main()
