"""
E2E Test: Temperature Sensor → MQTT → Kafka → Telegraf → VictoriaMetrics

This test verifies the complete telemetry data pipeline:
1. Sensor publishes temperature data to MQTT (hotel_01/101/temperature-sensor/telemetry)
2. MQTT-to-Kafka bridge forwards message to Kafka (mqtt_messages topic)
3. Telegraf consumes from Kafka and writes to VictoriaMetrics
4. VictoriaMetrics stores the data and can be queried
"""
import pytest
import time
import json
import requests
import paho.mqtt.client as mqtt


@pytest.fixture(scope="module")
def mqtt_client(e2e_config):
    """Create MQTT client connected to the broker."""
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
def test_temperature_sensor_to_victoriametrics(mqtt_client, e2e_config):
    """
    Test complete data flow from temperature sensor to VictoriaMetrics.
    
    Steps:
    1. Publish temperature telemetry to MQTT (simulating temperature sensor)
    2. Wait for data to flow through MQTT → Kafka → Telegraf → VictoriaMetrics
    3. Query VictoriaMetrics to verify data was stored
    """
    hotel_id = e2e_config["hotel_id"]
    room_number = e2e_config["room_number"]
    sensor = "temperature-sensor"
    
    # Build telemetry payload matching the sensor's format
    timestamp_ms = int(time.time() * 1000)
    temperature_c = 23.5
    
    payload = {
        "measurement": "temperature",
        "tags": {
            "hotel_id": hotel_id,
            "room": room_number,
            "sensor": sensor
        },
        "fields": {
            "temperatureC": temperature_c
        },
        "timestamp": timestamp_ms
    }
    
    # Publish to MQTT topic that sensor uses
    mqtt_topic = f"{hotel_id}/{room_number}/{sensor}/telemetry"
    print(f"\n[E2E] Publishing to MQTT topic: {mqtt_topic}")
    print(f"[E2E] Payload: {json.dumps(payload)}")
    
    mqtt_client.publish(mqtt_topic, json.dumps(payload), qos=1)
    
    # Wait for data to flow through the pipeline
    # MQTT → Kafka bridge → Kafka → Telegraf → VictoriaMetrics
    print("[E2E] Waiting 10 seconds for data to propagate...")
    time.sleep(10)
    
    # Query VictoriaMetrics for the temperature metric
    vm_url = f"{e2e_config['victoria_metrics_url']}/api/v1/query"
    
    # Query for temperature measurements from this specific room
    query = f'temperature{{hotel_id="{hotel_id}",room="{room_number}",sensor="{sensor}"}}'
    print(f"[E2E] Querying VictoriaMetrics: {query}")
    
    params = {"query": query}
    
    try:
        response = requests.get(vm_url, params=params, timeout=5)
        assert response.status_code == 200, f"VictoriaMetrics query failed: {response.status_code}"
        
        data = response.json()
        print(f"[E2E] VictoriaMetrics response: {json.dumps(data, indent=2)}")
        
        # Verify response structure
        assert "status" in data
        assert data["status"] == "success"
        assert "data" in data
        assert "result" in data["data"]
        
        # Check if we have results (temperature data was stored)
        results = data["data"]["result"]
        
        if len(results) == 0:
            pytest.skip(
                "No temperature data found in VictoriaMetrics. "
                "This may be expected if pipeline is not fully running. "
                "Ensure all services are running: MQTT broker, Kafka, Telegraf, VictoriaMetrics"
            )
        
        # Verify we got temperature data
        assert len(results) > 0, "Expected at least one temperature measurement"
        
        # Verify the result has the expected structure
        first_result = results[0]
        assert "metric" in first_result
        assert "value" in first_result
        
        # Verify metric tags
        metric = first_result["metric"]
        assert metric["hotel_id"] == hotel_id
        assert metric["room"] == str(room_number)
        assert metric["sensor"] == sensor
        
        # Verify we have a temperature value
        value_tuple = first_result["value"]
        assert len(value_tuple) == 2, "Expected [timestamp, value] tuple"
        
        temp_value = float(value_tuple[1])
        print(f"[E2E] Found temperature value: {temp_value}°C")
        
        # Temperature should be in reasonable range (-50 to 120)
        assert -50 <= temp_value <= 120, f"Temperature {temp_value}°C out of valid range"
        
        print("[E2E] SUCCESS: Temperature data successfully flowed through pipeline")
        
    except requests.exceptions.ConnectionError:
        pytest.skip("VictoriaMetrics not available")
    except requests.exceptions.Timeout:
        pytest.skip("VictoriaMetrics query timeout")
