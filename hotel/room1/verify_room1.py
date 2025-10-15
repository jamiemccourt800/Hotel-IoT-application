import time
import threading
import json
import paho.mqtt.client as mqtt

# MQTT broker settings (adjust as needed)
BROKER = 'localhost'
PORT = 1883



# Topics (match actual device topics)
HOTEL_ID = 'hotel_01'
ROOM = '101'
TEMP_SENSOR = 'temperature-sensor'
LIGHT_SENSOR = 'light-actuator'
ALERT_AGENT = 'alert-agent'

# MQTT topic for Kafka-forwarded temperature (example: kafka.sensors.hotel_01.101.temperature-sensor.sensor)
KAFKA_TEMP_TOPIC = f'kafka.sensors.{HOTEL_ID}.{ROOM}.{TEMP_SENSOR}.sensor'
TEMP_TOPIC = f'{HOTEL_ID}/{ROOM}/{TEMP_SENSOR}/sensor'
LIGHT_CMD_TOPIC = f'{HOTEL_ID}/{ROOM}/{LIGHT_SENSOR}/cmd'
LIGHT_STATE_TOPIC = f'{HOTEL_ID}/{ROOM}/{LIGHT_SENSOR}/state'
ALERT_TOPIC = f'sensors/{HOTEL_ID}/{ROOM}/{ALERT_AGENT}'


# Results for verification
results = {
    'temperature_telemetry_received': False,
    'light_actuator_state_updated': False,
    'light_actuator_status_updated': False,
    'alert_emitted': False
}


# For light actuator state/status
light_state_prev = None
light_status_prev = None

def on_temp_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"[MQTT] Received on {msg.topic}: {payload}")
        if (
            payload.get('measurement') == 'temperature'
            and 'fields' in payload
            and 'temperatureC' in payload['fields']
        ):
            results['temperature_telemetry_received'] = True
    except Exception as e:
        print(f"[MQTT] Error decoding message: {e}")

def on_light_state_message(client, userdata, msg):
    global light_state_prev
    try:
        payload = json.loads(msg.payload.decode())
        if payload.get('measurement') == 'state':
            new_on = payload.get('fields', {}).get('on')
            new_brightness = payload.get('fields', {}).get('brightness')
            # Detect any state update
            if light_state_prev is not None and (light_state_prev != (new_on, new_brightness)):
                results['light_actuator_state_updated'] = True
            light_state_prev = (new_on, new_brightness)
    except Exception:
        pass

def on_light_status_message(client, userdata, msg):
    global light_status_prev
    try:
        payload = json.loads(msg.payload.decode())
        if payload.get('measurement') == 'alert':
            # Status topic is used for online/offline alerts
            kind = payload.get('fields', {}).get('kind')
            if kind in ("actuator_online", "actuator_offline"):
                if light_status_prev != kind:
                    results['light_actuator_status_updated'] = True
                light_status_prev = kind
    except Exception:
        pass

def on_alert_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if payload.get('measurement') == 'alert':
            results['alert_emitted'] = True
    except Exception:
        pass

def subscribe_and_listen():
    client = mqtt.Client()
    client.connect(BROKER, PORT, 60)
    # Subscribe to both the direct sensor topic and the Kafka-forwarded topic
    client.subscribe([(TEMP_TOPIC, 0), (KAFKA_TEMP_TOPIC, 0), (LIGHT_STATE_TOPIC, 0), (ALERT_TOPIC, 0), (f'{HOTEL_ID}/{ROOM}/{LIGHT_SENSOR}/status', 0)])
    client.message_callback_add(TEMP_TOPIC, on_temp_message)
    client.message_callback_add(KAFKA_TEMP_TOPIC, on_temp_message)
    client.message_callback_add(LIGHT_STATE_TOPIC, on_light_state_message)
    client.message_callback_add(f'{HOTEL_ID}/{ROOM}/{LIGHT_SENSOR}/status', on_light_status_message)
    client.message_callback_add(ALERT_TOPIC, on_alert_message)
    client.loop_start()
    return client

def test_light_actuator(client):
    # Turn light on, then off using correct message format
    on_cmd = json.dumps({"fields": {"action": "on"}})
    off_cmd = json.dumps({"fields": {"action": "off"}})
    client.publish(LIGHT_CMD_TOPIC, on_cmd)
    time.sleep(1)
    client.publish(LIGHT_CMD_TOPIC, off_cmd)
    # Wait for state and status update
    timeout = time.time() + 5
    while (not results['light_actuator_state_updated'] or not results['light_actuator_status_updated']) and time.time() < timeout:
        time.sleep(0.2)

def induce_brightness_oor(client):
    # Send a set_brightness command with out-of-range value (e.g., 999)
    oor_cmd = json.dumps({"fields": {"action": "set_brightness", "value": 999}})
    client.publish(LIGHT_CMD_TOPIC, oor_cmd)
    # Wait for alert from alert-agent
    timeout = time.time() + 5
    while not results['alert_emitted'] and time.time() < timeout:
        time.sleep(0.2)

def main():

    print('Starting verification...')
    client = subscribe_and_listen()

    # Wait for temperature sensor telemetry
    print('Waiting for temperature sensor telemetry...')
    timeout = time.time() + 5
    while not results['temperature_telemetry_received'] and time.time() < timeout:
        time.sleep(0.2)
    if results['temperature_telemetry_received']:
        print('Temperature sensor is online and emitting telemetry.')
    else:
        print('Temperature sensor is NOT emitting telemetry.')

    # Test light actuator state and status
    print('Testing light actuator state and status update...')
    test_light_actuator(client)
    if results['light_actuator_state_updated']:
        print('Light actuator state updated in response to command.')
    else:
        print('Light actuator state did NOT update as expected.')
    if results['light_actuator_status_updated']:
        print('Light actuator status (online/offline) updated.')
    else:
        print('Light actuator status did NOT update as expected.')

    # Test alert agent
    print('Inducing brightness out-of-range to test alert-agent...')
    induce_brightness_oor(client)
    if results['alert_emitted']:
        print('Alert-agent emitted an alert for brightness OOR.')
    else:
        print('Alert-agent did NOT emit expected alert.')

    client.loop_stop()
    client.disconnect()
    print('\nVerification Results:')
    for k, v in results.items():
        print(f'{k}: {v}')

if __name__ == '__main__':
    main()
