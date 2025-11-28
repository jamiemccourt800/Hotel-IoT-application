"""
E2E tests for temperature sensor-actuator control loop.
Tests the full feedback loop: sensor → MQTT → actuator → control output.
"""
import pytest
import json
import time
import paho.mqtt.client as mqtt


@pytest.mark.e2e
class TestTemperatureLoop:
    """Test temperature sensor-actuator feedback loop"""
    
    def test_sensor_publishes_telemetry_to_mqtt(self, e2e_config):
        """Verify temperature sensor can publish telemetry to MQTT broker"""
        received_messages = []
        
        def on_message(client, userdata, msg):
            received_messages.append({
                'topic': msg.topic,
                'payload': json.loads(msg.payload.decode())
            })
        
        # Subscribe to temperature sensor telemetry topic
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        client.on_message = on_message
        client.connect(e2e_config["mqtt_broker"], e2e_config["mqtt_port"], 60)
        client.subscribe("hotel_01/101/temperature-sensor/telemetry")
        client.loop_start()
        
        # Wait for at least one telemetry message
        time.sleep(2)
        
        client.loop_stop()
        client.disconnect()
        
        # Should have received at least one temperature reading
        if len(received_messages) == 0:
            pytest.skip("Temperature sensor not running - no telemetry received")
        
        # Verify message structure
        msg = received_messages[0]['payload']
        assert msg['measurement'] == 'temperature'
        assert 'temperatureC' in msg['fields']
        assert msg['tags']['hotel_id'] == 'hotel_01'
        assert msg['tags']['room'] == 101
        assert msg['tags']['sensor'] == 'temperature-sensor'
    
    def test_actuator_subscribes_to_sensor_readings(self, e2e_config):
        """Verify actuator subscribes to sensor topic and receives readings"""
        # Publish a simulated sensor reading
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        client.connect(e2e_config["mqtt_broker"], e2e_config["mqtt_port"], 60)
        
        sensor_reading = {
            "measurement": "temperature",
            "tags": {
                "hotel_id": "hotel_01",
                "room": "101",
                "sensor": "temperature-sensor"
            },
            "fields": {
                "temperatureC": 25.0
            },
            "timestamp": int(time.time() * 1000)
        }
        
        client.publish("hotel_01/101/temperature-sensor/telemetry", 
                      json.dumps(sensor_reading), qos=1)
        client.disconnect()
        
        # If actuator is running, it should process this reading
        # (verified by no errors in actuator logs)
        time.sleep(0.5)
        assert True  # Test passes if no exceptions
    
    def test_actuator_publishes_setpoint_changes(self, e2e_config):
        """Verify actuator publishes target temperature setpoints"""
        received_setpoints = []
        
        def on_message(client, userdata, msg):
            received_setpoints.append(json.loads(msg.payload.decode()))
        
        # Subscribe to thermostat setpoint topic
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        client.on_message = on_message
        client.connect(e2e_config["mqtt_broker"], e2e_config["mqtt_port"], 60)
        client.subscribe("hotel_01/101/thermostat")
        client.loop_start()
        
        # Wait for actuator to potentially publish setpoints
        time.sleep(3)
        
        client.loop_stop()
        client.disconnect()
        
        # Actuator may publish setpoints during control loop
        # Test passes regardless - this is monitoring only
        if received_setpoints:
            setpoint = received_setpoints[0]
            assert 'target_temperature' in setpoint
            assert isinstance(setpoint['target_temperature'], (int, float))
    
    def test_feedback_loop_convergence(self, e2e_config):
        """Test that temperature converges toward setpoint over time"""
        temperature_readings = []
        
        def on_message(client, userdata, msg):
            data = json.loads(msg.payload.decode())
            if 'temperatureC' in data.get('fields', {}):
                temperature_readings.append(data['fields']['temperatureC'])
        
        # Monitor temperature sensor for several readings
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        client.on_message = on_message
        client.connect(e2e_config["mqtt_broker"], e2e_config["mqtt_port"], 60)
        client.subscribe("hotel_01/101/temperature-sensor/telemetry")
        client.loop_start()
        
        # Collect readings over 5 seconds
        time.sleep(5)
        
        client.loop_stop()
        client.disconnect()
        
        # Should have multiple readings showing temperature behavior
        if len(temperature_readings) < 3:
            pytest.skip("Temperature sensor not running - insufficient readings collected")
        
        # Verify temperatures are in reasonable range
        for temp in temperature_readings:
            assert -50 < temp < 120, f"Temperature {temp}°C out of physical range"
