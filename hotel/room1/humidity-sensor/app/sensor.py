"""
Humidity sensor business logic extracted from existing main.py.
Handles MQTT communication, telemetry publishing, and target updates.
"""
import json
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from common import HotelMQTTClient, HumidityTelemetry, MessageTags, get_logger
from simulation import HumiditySimulation

class HumiditySensor:
    """Humidity sensor with MQTT communication and simulation"""
    
    def __init__(self, device_config, mqtt_config, humidity_config):
        self.device_config = device_config
        self.mqtt_config = mqtt_config  
        self.humidity_config = humidity_config
        self.logger = get_logger("humidity-sensor", device_config)
        
        # Initialize components
        self.mqtt_client = HotelMQTTClient(mqtt_config, "humidity-sensor", device_config)
        self.simulation = HumiditySimulation(humidity_config)
        
    def start(self):
        """Main sensor operation loop"""
        self.logger.info('startup', 'started', 
                        hotel_id=self.device_config.hotel_id,
                        room=self.device_config.room,
                        sensor=self.device_config.sensor,
                        interval_s=self.humidity_config.interval,
                        speed=self.humidity_config.speed,
                        target_humidity=self.humidity_config.target_humidity)
        
        # Connect to MQTT with retries (using shared client)
        client = self.mqtt_client.connect_with_retries()
        
        # Set up MQTT topics (matching existing structure)
        base_topic = f"{self.device_config.hotel_id}/{self.device_config.room}/{self.device_config.sensor}"
        telemetry_topic = f"{base_topic}/telemetry"
        status_topic = f"{base_topic}/status"
        target_topic = f"{self.device_config.hotel_id}/{self.device_config.room}/humidifier"
        
        # Set up Last Will Testament for offline detection
        lwt_payload = {
            "measurement": "alert",
            "tags": {
                "hotel_id": self.device_config.hotel_id,
                "room": self.device_config.room,
                "sensor": self.device_config.sensor
            },
            "fields": {"kind": "sensor_offline", "severity": "HIGH"},
            "timestamp": int(time.time() * 1000)
        }
        self.mqtt_client.setup_last_will(status_topic, lwt_payload)
        
        # Subscribe to target humidity updates
        client.subscribe(target_topic, qos=self.mqtt_config.qos)
        client.on_message = self._on_target_update
        
        # Publish sensor online status
        online_payload = {
            "measurement": "alert",
            "tags": {
                "hotel_id": self.device_config.hotel_id,
                "room": self.device_config.room,
                "sensor": self.device_config.sensor
            },
            "fields": {"kind": "sensor_online", "severity": "INFO"},
            "timestamp": int(time.time() * 1000)
        }
        self.mqtt_client.publish_telemetry(status_topic, online_payload)
        
        # Start telemetry publishing loop
        self._telemetry_loop(client, telemetry_topic)
        
    def _telemetry_loop(self, client, telemetry_topic):
        """Publish humidity readings at configured interval"""
        self.logger.info('publishing', f'publishing telemetry to {telemetry_topic}', 
                        topic_out=telemetry_topic)
        
        published_count = 0
        try:
            for timestamp, humidity in self.simulation.generate_readings():
                # Build message using shared schema
                message = HumidityTelemetry(
                    tags=MessageTags(
                        hotel_id=self.device_config.hotel_id,
                        room=self.device_config.room,
                        sensor=self.device_config.sensor
                    ),
                    fields={
                        "humidityPercent": humidity
                    },
                    timestamp=timestamp
                )
                
                # Publish via standardized client  
                self.mqtt_client.publish_telemetry(telemetry_topic, message.to_dict())
                published_count += 1
                
                # Log current humidity every 10 readings to avoid log spam
                if published_count % 10 == 0:
                    self.logger.info('telemetry', f'current humidity: {humidity}%', 
                                   current_humidity=humidity, target_humidity=self.simulation.target_humidity)
                
        except KeyboardInterrupt:
            self.logger.info('shutdown', 'stopping sensor')
        finally:
            client.loop_stop()
            client.disconnect()
            self.logger.info('shutdown', 'sensor disconnected cleanly', 
                           published_count=published_count)
            
    def _on_target_update(self, client, userdata, msg):
        """Handle target humidity updates from humidifier/dehumidifier"""
        try:
            data = json.loads(msg.payload.decode())
            if "target_humidity" in data:
                target = float(data["target_humidity"])
                self.simulation.set_target_humidity(target)
                self.logger.info('target-update', f'updated target humidity to {target}%',
                               target_humidity=target, topic_in=msg.topic)
        except Exception as e:
            self.logger.error('target-update', f'failed to process target update: {e}',
                            error=str(e), topic_in=msg.topic)
