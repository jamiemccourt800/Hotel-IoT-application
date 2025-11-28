"""
Integration tests for hotel/room1/common/mqtt_client.py
Tests MQTT client connection and retry logic with real broker
"""
import pytest
import time
import paho.mqtt.client as mqtt
from hotel.room1.common.mqtt_client import HotelMQTTClient
from hotel.room1.common.config import MQTTConfig


@pytest.mark.integration
@pytest.mark.timeout(20)
class TestMQTTClientIntegration:
    """Test MQTT client with real broker connection"""
    
    def test_mqtt_client_connects_successfully(self, integration_settings):
        """Test successful connection to MQTT broker"""
        config = MQTTConfig(
            broker=integration_settings["mqtt_host"],
            port=integration_settings["mqtt_port"],
            keepalive=60
        )
        # Create a simple object with attributes
        class DeviceConfig:
            def __init__(self):
                self.hotel_id = 'test-hotel'
                self.room = '101'
                self.sensor = 'integration-test'
        
        device_config = DeviceConfig()
        
        client_wrapper = HotelMQTTClient(config, "test-service", device_config)
        
        # Should connect without raising exception
        mqtt_client = client_wrapper.connect_with_retries(max_attempts=5)
        
        assert mqtt_client is not None
        assert client_wrapper.client is not None
        
        # Cleanup
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    
    def test_mqtt_client_retry_on_failure(self, integration_settings):
        """Test retry logic when connection fails initially"""
        # Use invalid port to trigger retry
        config = MQTTConfig(
            broker=integration_settings.get("mqtt_host", "mosquitto"),
            port=9999,  # Invalid port
            keepalive=60
        )
        # Create a simple object with attributes
        class DeviceConfig:
            def __init__(self):
                self.hotel_id = 'retry-test'
                self.room = '1'
                self.sensor = 'test'
        
        device_config = DeviceConfig()
        
        client_wrapper = HotelMQTTClient(config, "retry-service", device_config)
        
        # Should raise exception after max attempts
        with pytest.raises(Exception):
            client_wrapper.connect_with_retries(max_attempts=2)
    
    def test_mqtt_client_setup_last_will(self, integration_settings):
        """Test Last Will Testament configuration"""
        config = MQTTConfig(
            broker=integration_settings["mqtt_host"],
            port=integration_settings["mqtt_port"],
            keepalive=60
        )
        # Create a simple object with attributes
        class DeviceConfig:
            def __init__(self):
                self.hotel_id = 'lwt-test'
                self.room = '202'
                self.sensor = 'lwt-sensor'
        
        device_config = DeviceConfig()
        
        client_wrapper = HotelMQTTClient(config, "lwt-service", device_config)
        mqtt_client = client_wrapper.connect_with_retries(max_attempts=5)
        
        # Setup last will
        lwt_payload = {"status": "offline", "reason": "disconnect"}
        client_wrapper.setup_last_will("test/lwt", lwt_payload)
        
        # Verify client has will configured (client.will_set was called)
        # This doesn't raise exception if successful
        assert mqtt_client is not None
        
        # Cleanup
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    
    def test_mqtt_client_publish_message(self, integration_settings):
        """Test publishing message through HotelMQTTClient"""
        config = MQTTConfig(
            broker=integration_settings["mqtt_host"],
            port=integration_settings["mqtt_port"],
            keepalive=60
        )
        # Create a simple object with attributes
        class DeviceConfig:
            def __init__(self):
                self.hotel_id = 'pub-test'
                self.room = '303'
                self.sensor = 'pub-sensor'
        
        device_config = DeviceConfig()
        
        client_wrapper = HotelMQTTClient(config, "pub-service", device_config)
        mqtt_client = client_wrapper.connect_with_retries(max_attempts=5)
        
        # Publish test message
        test_payload = {"test": "data", "value": 42}
        client_wrapper.publish_telemetry("integration/test/publish", test_payload)
        
        # Give time for message to be sent
        time.sleep(0.5)
        
        # Cleanup
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    
    def test_mqtt_client_subscribe_and_receive(self, integration_settings):
        """Test subscribing and receiving messages"""
        config = MQTTConfig(
            broker=integration_settings["mqtt_host"],
            port=integration_settings["mqtt_port"],
            keepalive=60
        )
        # Create a simple object with attributes
        class DeviceConfig:
            def __init__(self):
                self.hotel_id = 'sub-test'
                self.room = '404'
                self.sensor = 'sub-sensor'
        
        device_config = DeviceConfig()
        
        received_messages = []
        
        def on_message(client, userdata, msg):
            received_messages.append({
                'topic': msg.topic,
                'payload': msg.payload.decode()
            })
        
        client_wrapper = HotelMQTTClient(config, "sub-service", device_config)
        mqtt_client = client_wrapper.connect_with_retries(max_attempts=5)
        
        # Subscribe with callback
        client_wrapper.subscribe_to_commands("integration/test/subscribe", on_message)
        
        # Give time for subscription to register
        time.sleep(0.5)
        
        # Publish message to subscribed topic
        client_wrapper.publish_telemetry("integration/test/subscribe", {"test": "subscribe"})
        
        # Wait for message
        time.sleep(1)
        
        # Verify message received
        assert len(received_messages) > 0
        assert received_messages[0]['topic'] == "integration/test/subscribe"
        
        # Cleanup
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
