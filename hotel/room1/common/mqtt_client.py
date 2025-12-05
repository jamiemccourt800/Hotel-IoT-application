"""Standardized MQTT client with connection handling and retries.
Eliminates duplicated MQTT setup code across services (150+ lines per service).

Usage:
------
from common import HotelMQTTClient, MQTTConfig, DeviceConfig

# Initialize client
mqtt_config = MQTTConfig.from_env()
device_config = DeviceConfig.from_env('sensor-name')
client = HotelMQTTClient(mqtt_config, 'service-name', device_config)

# Connect with automatic retries
client.connect_with_retries(max_attempts=30)

# Setup last will (optional)
client.setup_last_will('hotel/status', {'status': 'offline'})

# Publish telemetry
client.publish_telemetry('hotel/temperature', telemetry_payload)

Exported:
---------
- HotelMQTTClient: Wrapper with retry logic and standardized publishing
"""
import time
import json
import paho.mqtt.client as mqtt
from typing import Callable, Optional, Dict, Any
from .logging import get_logger

class HotelMQTTClient:
    """Standardized MQTT client wrapper for hotel services"""
    
    def __init__(self, config, service_name: str, device_config):
        self.config = config
        self.service_name = service_name
        self.device_config = device_config
        self.logger = get_logger(service_name, device_config)
        self.client = None
        
    def connect_with_retries(self, max_attempts: int = 30) -> mqtt.Client:
        """Robust MQTT connection with exponential backoff retry logic"""
        # Create MQTT client compatible with paho-mqtt 2.x
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv311, clean_session=True)
        
        attempts = 0
        delay = 2.0
        
        while attempts < max_attempts:
            try:
                attempts += 1
                self.logger.info('connect-attempt', 
                    f'connecting to {self.config.broker}:{self.config.port}', 
                    attempt=attempts, max_attempts=max_attempts)
                    
                self.client.connect(self.config.broker, self.config.port, self.config.keepalive)
                self.client.loop_start()
                
                self.logger.info('connect', 'mqtt connected')
                return self.client
                
            except Exception as e:
                if attempts >= max_attempts:
                    self.logger.error('mqtt-connect-exhausted', 
                        f'failed to connect after {max_attempts} attempts', 
                        error=str(e))
                    raise
                    
                self.logger.warning('mqtt-connect-retry', 
                    f'connect failed: {e}; retrying in {delay}s', 
                    error=str(e))
                time.sleep(delay)
                delay = min(delay * 1.5, 30)  # Exponential backoff with max 30s
                
        return self.client
        
    def setup_last_will(self, topic: str, payload: dict):
        """Configure Last Will Testament for offline detection"""
        if self.client:
            self.client.will_set(
                topic, 
                payload=json.dumps(payload), 
                qos=self.config.qos, 
                retain=False
            )
            
    def publish_telemetry(self, topic: str, payload: dict, retain: bool = False):
        """Standardized telemetry publishing with error handling"""
        if self.client:
            try:
                result = self.client.publish(
                    topic, 
                    json.dumps(payload), 
                    qos=self.config.qos, 
                    retain=retain
                )
                # Log successful publish (matching existing pattern)
                # Note: Removed per-message logging to match current behavior
                
            except Exception as e:
                self.logger.error('publish-error', f'failed to publish to {topic}', 
                                error=str(e), topic=topic)
                
    def subscribe_to_commands(self, topic_pattern: str, callback: Callable):
        """Subscribe to command topics with QoS management"""
        if self.client:
            self.client.subscribe(topic_pattern, qos=self.config.qos)
            self.client.on_message = callback
            self.logger.info('subscribe', f'subscribed to {topic_pattern}', 
                           topic_pattern=topic_pattern)
            
    def disconnect(self):
        """Clean disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.logger.info('disconnect', 'mqtt disconnected cleanly')