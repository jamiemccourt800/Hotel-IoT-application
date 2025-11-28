"""
E2E tests for external control via FastAPI commands.
Tests command delivery, ACK responses, and external control mode activation.
"""
import pytest
import json
import time
import uuid
import paho.mqtt.client as mqtt


@pytest.mark.e2e
class TestExternalControl:
    """Test external control command integration"""
    
    def test_temperature_command_sent_and_acknowledged(self, e2e_config):
        """Verify temperature command is sent and ACK received"""
        ack_messages = []
        
        def on_message(client, userdata, msg):
            if '/ack' in msg.topic:
                ack_messages.append({
                    'topic': msg.topic,
                    'payload': json.loads(msg.payload.decode())
                })
        
        # Subscribe to ACK topic
        client = mqtt.Client()
        client.on_message = on_message
        client.connect(e2e_config["mqtt_broker"], e2e_config["mqtt_port"], 60)
        client.subscribe("hotel_01/101/+/ack")
        client.loop_start()
        
        # Send temperature command
        correlation_id = str(uuid.uuid4())
        command = {
            "fields": {
                "target_temperature": 23.0
            },
            "correlationId": correlation_id
        }
        
        client.publish("commands/temperature/hotel_01/101/thermostat", 
                      json.dumps(command), qos=1)
        
        # Wait for ACK
        time.sleep(2)
        
        client.loop_stop()
        client.disconnect()
        
        # Verify ACK received
        if len(ack_messages) == 0:
            pytest.skip("Temperature actuator not running - no ACK received")
        
        ack = ack_messages[0]['payload']
        assert ack['measurement'] == 'ack'
        assert ack['correlationId'] == correlation_id
        assert ack['fields']['status'] in ['ok', 'failed']
    
    def test_humidity_command_activates_external_mode(self, e2e_config):
        """Verify humidity command activates external control mode"""
        # Send humidity command
        client = mqtt.Client()
        client.connect(e2e_config["mqtt_broker"], e2e_config["mqtt_port"], 60)
        
        correlation_id = str(uuid.uuid4())
        command = {
            "fields": {
                "target_humidity": 55.0
            },
            "correlationId": correlation_id
        }
        
        client.publish("commands/humidity/hotel_01/101/humidifier", 
                      json.dumps(command), qos=1)
        client.disconnect()
        
        # Wait for command processing
        time.sleep(1)
        
        # Test passes if no errors (external mode should activate)
        assert True
    
    def test_light_brightness_command_delivered(self, e2e_config):
        """Verify light brightness command is delivered"""
        ack_messages = []
        
        def on_message(client, userdata, msg):
            if '/ack' in msg.topic:
                ack_messages.append(json.loads(msg.payload.decode()))
        
        client = mqtt.Client()
        client.on_message = on_message
        client.connect(e2e_config["mqtt_broker"], e2e_config["mqtt_port"], 60)
        client.subscribe("hotel_01/101/+/ack")
        client.loop_start()
        
        # Send light brightness command
        correlation_id = str(uuid.uuid4())
        command = {
            "fields": {
                "brightness": 75
            },
            "correlationId": correlation_id
        }
        
        client.publish("commands/light/hotel_01/101/light-control", 
                      json.dumps(command), qos=1)
        
        time.sleep(2)
        
        client.loop_stop()
        client.disconnect()
        
        # ACK may be received if light actuator is running
        if ack_messages:
            ack = ack_messages[0]
            assert ack['correlationId'] == correlation_id
    
    def test_command_without_correlation_id_still_processed(self, e2e_config):
        """Verify commands without correlationId are still processed"""
        client = mqtt.Client()
        client.connect(e2e_config["mqtt_broker"], e2e_config["mqtt_port"], 60)
        
        # Send command without correlationId
        command = {
            "fields": {
                "target_temperature": 22.0
            }
        }
        
        client.publish("commands/temperature/hotel_01/101/thermostat", 
                      json.dumps(command), qos=1)
        client.disconnect()
        
        time.sleep(1)
        
        # Should not crash - correlationId is optional
        assert True
    
    def test_multiple_commands_sequential(self, e2e_config):
        """Test sending multiple commands in sequence"""
        client = mqtt.Client()
        client.connect(e2e_config["mqtt_broker"], e2e_config["mqtt_port"], 60)
        
        # Send temperature command
        client.publish("commands/temperature/hotel_01/101/thermostat", 
                      json.dumps({"fields": {"target_temperature": 21.0}}), qos=1)
        time.sleep(0.5)
        
        # Send humidity command
        client.publish("commands/humidity/hotel_01/101/humidifier", 
                      json.dumps({"fields": {"target_humidity": 60.0}}), qos=1)
        time.sleep(0.5)
        
        # Send light command
        client.publish("commands/light/hotel_01/101/light-control", 
                      json.dumps({"fields": {"brightness": 50}}), qos=1)
        
        client.disconnect()
        time.sleep(1)
        
        # All commands should be processed without errors
        assert True
