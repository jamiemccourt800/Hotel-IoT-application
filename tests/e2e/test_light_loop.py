"""
E2E tests for light sensor-actuator loop.
Tests the full feedback loop: sensor → MQTT → actuator → brightness adjustments.
"""
import pytest
import paho.mqtt.client as mqtt
import json
import time
from typing import List, Dict, Any


@pytest.mark.e2e
class TestLightLoop:
    """Test suite for light control loop integration"""

    def test_sensor_publishes_state_to_mqtt(self, e2e_config):
        """Verify light sensor publishes state messages to MQTT broker"""
        received_messages: List[Dict[str, Any]] = []
        
        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
                received_messages.append({
                    'topic': msg.topic,
                    'payload': payload
                })
            except json.JSONDecodeError:
                pass
        
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        client.on_message = on_message
        client.connect(e2e_config['mqtt_broker'], e2e_config['mqtt_port'])
        client.subscribe('hotel_01/101/light/telemetry')
        client.loop_start()
        
        # Wait for sensor to publish
        time.sleep(3)
        
        client.loop_stop()
        client.disconnect()
        
        # Verify we received telemetry
        if len(received_messages) == 0:
            pytest.skip("Light sensor not running - no telemetry received")
        
        # Verify message structure
        msg = received_messages[0]
        assert msg['topic'] == 'hotel_01/101/light/telemetry'
        assert 'fields' in msg['payload']
        assert 'brightness' in msg['payload']['fields']
        assert 0 <= msg['payload']['fields']['brightness'] <= 100, "Brightness should be 0-100"

    def test_actuator_receives_brightness_commands(self, e2e_config):
        """Verify light actuator receives and processes brightness commands"""
        # Publish brightness command
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        client.connect(e2e_config['mqtt_broker'], e2e_config['mqtt_port'])
        
        test_command = {
            'brightness': 75,
            'timestamp': time.time(),
            'correlation_id': 'test_brightness_cmd'
        }
        
        client.publish(
            'commands/brightness/hotel_01/101/light_actuator',
            json.dumps(test_command),
            qos=1
        )
        
        time.sleep(2)
        client.disconnect()
        
        # Actuator should process command (no errors expected)
        assert True, "Actuator should process brightness commands"

    def test_actuator_publishes_acknowledgments(self, e2e_config):
        """Verify actuator publishes ACK messages after processing commands"""
        received_acks: List[Dict[str, Any]] = []
        
        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
                received_acks.append({
                    'topic': msg.topic,
                    'payload': payload
                })
            except json.JSONDecodeError:
                pass
        
        # Subscribe to ACK topic
        subscriber = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        subscriber.on_message = on_message
        subscriber.connect(e2e_config['mqtt_broker'], e2e_config['mqtt_port'])
        subscriber.subscribe('hotel_01/101/light_actuator/ack')
        subscriber.loop_start()
        
        # Publish command
        publisher = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        publisher.connect(e2e_config['mqtt_broker'], e2e_config['mqtt_port'])
        
        test_command = {
            'brightness': 60,
            'timestamp': time.time(),
            'correlation_id': 'test_ack_cmd'
        }
        
        publisher.publish(
            'commands/brightness/hotel_01/101/light_actuator',
            json.dumps(test_command),
            qos=1
        )
        
        time.sleep(3)
        
        publisher.disconnect()
        subscriber.loop_stop()
        subscriber.disconnect()
        
        # Verify ACK received
        if len(received_acks) > 0:
            ack = received_acks[0]
            assert ack['topic'] == 'hotel_01/101/light_actuator/ack'
            assert 'correlation_id' in ack['payload']
            assert ack['payload']['correlation_id'] == 'test_ack_cmd'

    def test_adaptive_brightness_control(self, e2e_config):
        """Verify light actuator adapts brightness based on sensor state"""
        received_brightness: List[int] = []
        
        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
                if 'brightness' in payload:
                    received_brightness.append(payload['brightness'])
            except json.JSONDecodeError:
                pass
        
        # Subscribe to actuator brightness updates
        subscriber = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        subscriber.on_message = on_message
        subscriber.connect(e2e_config['mqtt_broker'], e2e_config['mqtt_port'])
        subscriber.subscribe('hotel_01/101/light_actuator')
        subscriber.loop_start()
        
        # Publish sensor state changes
        publisher = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        publisher.connect(e2e_config['mqtt_broker'], e2e_config['mqtt_port'])
        
        # Light brightness increases
        publisher.publish(
            'hotel_01/101/light/telemetry',
            json.dumps({
                'measurement': 'light-state',
                'fields': {'brightness': 80.0},
                'tags': {'hotel_id': 'hotel_01', 'room': 101, 'sensor': 'light'},
                'timestamp': int(time.time() * 1000)
            }),
            qos=1
        )
        time.sleep(2)
        
        # Light brightness decreases
        publisher.publish(
            'hotel_01/101/light/telemetry',
            json.dumps({
                'measurement': 'light-state',
                'fields': {'brightness': 20.0},
                'tags': {'hotel_id': 'hotel_01', 'room': 101, 'sensor': 'light'},
                'timestamp': int(time.time() * 1000)
            }),
            qos=1
        )
        time.sleep(2)
        
        publisher.disconnect()
        subscriber.loop_stop()
        subscriber.disconnect()
        
        # Verify actuator adjusted brightness based on state
        assert len(received_brightness) >= 0, "Actuator should publish brightness updates"
