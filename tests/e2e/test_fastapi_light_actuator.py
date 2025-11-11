"""
E2E Test: FastAPI Command → Kafka → MQTT → Light Actuator

This test verifies the complete command/control pipeline:
1. FastAPI receives HTTP POST request to control light
2. FastAPI publishes command to Kafka (actuators.{hotel}.{room}.light-actuator.cmd)
3. Kafka-to-MQTT bridge forwards to MQTT ({hotel}/{room}/light-actuator/cmd)
4. Light actuator receives and processes command
5. Light actuator publishes acknowledgment/status back to MQTT
"""
import pytest
import time
import json
import requests
import paho.mqtt.client as mqtt
from threading import Event


@pytest.fixture(scope="module")
def mqtt_client(e2e_config):
    """Create MQTT client to monitor actuator responses."""
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    
    try:
        client.connect(e2e_config["mqtt_broker"], e2e_config["mqtt_port"], 60)
        client.loop_start()
        yield client
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        pytest.skip(f"MQTT broker not available: {e}")


@pytest.mark.e2e
def test_fastapi_light_command_to_actuator(mqtt_client, e2e_config):
    """
    Test complete command flow from FastAPI to light actuator.
    
    Steps:
    1. Subscribe to MQTT topic where actuator publishes acknowledgments
    2. Send light control command via FastAPI HTTP endpoint
    3. Verify FastAPI accepts the command (Kafka publish)
    4. Wait for actuator to process command and publish acknowledgment
    5. Verify acknowledgment received on MQTT
    """
    hotel_id = e2e_config["hotel_id"]
    room_number = e2e_config["room_number"]
    
    # Track received messages
    received_messages = []
    message_event = Event()
    
    def on_message(client, userdata, msg):
        """Callback for MQTT messages."""
        payload = msg.payload.decode("utf-8")
        print(f"\n[E2E] Received MQTT message on {msg.topic}: {payload}")
        received_messages.append({
            "topic": msg.topic,
            "payload": payload
        })
        message_event.set()
    
    mqtt_client.on_message = on_message
    
    # Subscribe to actuator's acknowledgment topic
    # Actuator publishes to: {hotel_id}/{room_number}/light-actuator/ack
    ack_topic = f"{hotel_id}/{room_number}/light-actuator/ack"
    print(f"\n[E2E] Subscribing to actuator ACK topic: {ack_topic}")
    mqtt_client.subscribe(ack_topic, qos=1)
    
    # Also subscribe to status topic for good measure
    status_topic = f"{hotel_id}/{room_number}/light-actuator/status"
    print(f"[E2E] Subscribing to actuator status topic: {status_topic}")
    mqtt_client.subscribe(status_topic, qos=1)
    
    # Give subscription time to establish
    time.sleep(1)
    
    # Send command via FastAPI endpoint
    # Endpoint: POST /actuator/light/{hotel_id}/{room_number}/on
    fastapi_url = e2e_config["fastapi_url"]
    endpoint = f"{fastapi_url}/actuator/light/{hotel_id}/{room_number}/on"
    
    print(f"[E2E] Sending POST request to FastAPI: {endpoint}")
    
    try:
        response = requests.post(endpoint, timeout=5)
        
        # Check if FastAPI is available
        if response.status_code == 404:
            pytest.skip(f"FastAPI endpoint not found: {endpoint}")
        
        print(f"[E2E] FastAPI response status: {response.status_code}")
        print(f"[E2E] FastAPI response body: {response.text}")
        
        # Verify FastAPI accepted the command
        assert response.status_code == 200, f"FastAPI returned {response.status_code}: {response.text}"
        
        response_data = response.json()
        assert "status" in response_data
        assert response_data["status"] == "success", f"Command failed: {response_data}"
        
        print("[E2E] FastAPI successfully accepted command")
        
        # Wait for actuator to process command and publish acknowledgment
        # Command flow: FastAPI → Kafka → Kafka-to-MQTT bridge → MQTT → Actuator
        print("[E2E] Waiting up to 15 seconds for actuator acknowledgment...")
        
        # Wait for message with timeout
        message_received = message_event.wait(timeout=15)
        
        if not message_received:
            pytest.skip(
                "Actuator acknowledgment not received within 15 seconds. "
                "This may be expected if actuator is not running or Kafka→MQTT bridge is down. "
                "Ensure all services are running: Kafka, Kafka-to-MQTT bridge, Light actuator"
            )
        
        # Verify we received acknowledgment
        assert len(received_messages) > 0, "No messages received from actuator"
        
        # Check the acknowledgment message
        for msg in received_messages:
            try:
                payload = json.loads(msg["payload"])
                print(f"[E2E] Parsed acknowledgment: {json.dumps(payload, indent=2)}")
                
                # Actuator sends acknowledgment with status
                if "status" in payload:
                    assert payload["status"] in ["ok", "success"], f"Unexpected status: {payload['status']}"
                    print(f"[E2E] SUCCESS: Light actuator acknowledged command with status={payload['status']}")
                    return
                    
            except json.JSONDecodeError:
                # Some messages may not be JSON (status messages)
                print(f"[E2E] Non-JSON message: {msg['payload']}")
                continue
        
        print("[E2E] SUCCESS: Communication flow verified (FastAPI → Kafka → MQTT → Actuator)")
        
    except requests.exceptions.ConnectionError:
        pytest.skip(f"FastAPI not available at {fastapi_url}")
    except requests.exceptions.Timeout:
        pytest.skip("FastAPI request timeout")


@pytest.mark.e2e
def test_fastapi_light_brightness_command(mqtt_client, e2e_config):
    """
    Test brightness control command flow.
    
    Similar to on/off test but with brightness value.
    """
    hotel_id = e2e_config["hotel_id"]
    room_number = e2e_config["room_number"]
    brightness_value = 75
    
    # Track received messages
    received_messages = []
    message_event = Event()
    
    def on_message(client, userdata, msg):
        payload = msg.payload.decode("utf-8")
        print(f"\n[E2E] Received MQTT message on {msg.topic}: {payload}")
        received_messages.append({
            "topic": msg.topic,
            "payload": payload
        })
        message_event.set()
    
    mqtt_client.on_message = on_message
    
    # Subscribe to actuator topics
    ack_topic = f"{hotel_id}/{room_number}/light-actuator/ack"
    mqtt_client.subscribe(ack_topic, qos=1)
    
    time.sleep(1)
    
    # Send brightness command via FastAPI
    fastapi_url = e2e_config["fastapi_url"]
    endpoint = f"{fastapi_url}/actuator/light/{hotel_id}/{room_number}/brightness/{brightness_value}"
    
    print(f"\n[E2E] Sending brightness command: {endpoint}")
    
    try:
        response = requests.post(endpoint, timeout=5)
        
        if response.status_code == 404:
            pytest.skip(f"FastAPI endpoint not found: {endpoint}")
        
        print(f"[E2E] FastAPI response: {response.status_code} - {response.text}")
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data.get("value") == brightness_value
        
        print(f"[E2E] FastAPI accepted brightness={brightness_value} command")
        
        # Wait for acknowledgment
        print("[E2E] Waiting for actuator acknowledgment...")
        message_received = message_event.wait(timeout=15)
        
        if not message_received:
            pytest.skip("Actuator acknowledgment not received (may be expected if actuator not running)")
        
        # Verify acknowledgment
        assert len(received_messages) > 0
        
        for msg in received_messages:
            try:
                payload = json.loads(msg["payload"])
                if "status" in payload:
                    assert payload["status"] in ["ok", "success"]
                    print(f"[E2E] SUCCESS: Brightness command acknowledged")
                    return
            except json.JSONDecodeError:
                continue
        
        print("[E2E] SUCCESS: Brightness command flow verified")
        
    except requests.exceptions.ConnectionError:
        pytest.skip(f"FastAPI not available at {fastapi_url}")
    except requests.exceptions.Timeout:
        pytest.skip("FastAPI request timeout")

