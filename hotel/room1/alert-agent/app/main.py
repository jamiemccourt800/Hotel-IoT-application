"""
Alert agent entry point - minimal orchestration only.
Follows the same modular pattern as temperature/humidity/light sensors.
"""
import sys
import os

# Add parent directories to path for common imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agent import AlertAgent
from config import AlertConfig
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from common import DeviceConfig, MQTTConfig

def main():
    """Initialize and start alert agent"""
    # Load configuration from environment
    device_config = DeviceConfig.from_env("alert-agent")
    mqtt_config = MQTTConfig.from_env()
    alert_config = AlertConfig.from_env()
    
    # Initialize and start agent
    agent = AlertAgent(device_config, mqtt_config, alert_config)
    agent.start()

if __name__ == "__main__":
    main()