import paho.mqtt.client as mqtt
from kafka import KafkaProducer
import json
import os
import time
from kafka.errors import NoBrokersAvailable

# MQTT settings
MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_SUB_TOPICS_RAW = os.getenv("MQTT_TOPIC", "sensors/#")  # can be comma/pipe/space-separated
MQTT_PUB_TOPIC_PREFIX = os.getenv("MQTT_PUB_TOPIC_PREFIX", "actuators/")  # where to forward actuator commands if needed
SITE_ID = os.getenv("SITE_ID", "unknown-site")

# Fields
SENSOR_FIELDS = os.getenv("SENSOR_FIELDS", "value,Value,status,Status,temperature")  # comma-separated list of fields to check for sensor values

# Kafka settings
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "mqtt_messages")
KAFKA_ACTIONS_TOPIC = os.getenv("KAFKA_ACTIONS_TOPIC", "executed_actions")

# Tolerances Settings
DEFAULT_TOLERANCE_PERCENT = float(os.getenv("DEFAULT_TOLERANCE_PERCENT", "2.0"))  # 5% change
DEFAULT_TOLERANCE_ABSOLUTE = float(os.getenv("DEFAULT_TOLERANCE_ABSOLUTE", "0.5"))  # absolute change
MIN_TIME_BETWEEN_UPDATES = int(os.getenv("MIN_TIME_BETWEEN_UPDATES", "30"))  # seconds

# Last Values and Timestamps
last_values = {}
last_timestamps = {}

SENSOR_TOLERANCES = {
    "temperature": {"percent": DEFAULT_TOLERANCE_PERCENT, "absolute": DEFAULT_TOLERANCE_ABSOLUTE},
    "light": {"percent": 0.0, "absolute": 0.1},  # binary sensor
}

# Kafka producer with retry logic
def create_kafka_producer():
    # Robust connect: retry until Kafka is available.
    # Use environment variable KAFKA_RETRY_DELAY (seconds) to control wait between attempts.
    retry_delay = int(os.getenv("KAFKA_RETRY_DELAY", "5"))
    attempt = 0
    while True:
        attempt += 1
        try:
            print(f"Attempting to connect to Kafka (attempt {attempt})...")
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                retries=5,
                retry_backoff_ms=1000
            )
            print("Successfully connected to Kafka!")
            return producer
        except NoBrokersAvailable:
            print(f"Kafka not available yet. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        except Exception as e:
            # For any unexpected error, log and retry instead of exiting the container.
            print(f"Unexpected error connecting to Kafka: {e}. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

producer = create_kafka_producer()

# MQTT client (for both subscribe & publish)
mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

def _parse_topics(raw: str):
    # split by common separators and strip
    seps = [',', '|', ';', ' '] 
    parts = [raw]
    for sep in seps:
        new_parts = []
        for p in parts:
            new_parts.extend([s for s in p.split(sep) if s])
        parts = new_parts
    # ensure unique and non-empty
    uniq = []
    for p in parts:
        p = p.strip()
        if p and p not in uniq:
            uniq.append(p)
    return uniq or ["sensors/#"]

SUB_TOPICS = _parse_topics(MQTT_SUB_TOPICS_RAW)

def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected to MQTT broker with result code " + str(reason_code))
    # subscribe to all configured topics
    if len(SUB_TOPICS) == 1:
        client.subscribe(SUB_TOPICS[0])
        print(f"Subscribed to MQTT topic: {SUB_TOPICS[0]}")
    else:
        subs = [(t, 0) for t in SUB_TOPICS]
        client.subscribe(subs)
        print(f"Subscribed to MQTT topics: {', '.join(SUB_TOPICS)}")

def check_tolerance(topic, current_value, timestamp):
    """Check if the change in value exceeds the defined tolerances."""
    print(f"Checking tolerance for topic {topic} with current value {current_value}")
    # Send if no previous record
    if topic not in last_values:
        print(f"No previous value for topic {topic}, sending update.")
        return True
    
    last_value = last_values[topic]
    if not isinstance(current_value, (int, float)) or not isinstance(last_value, (int, float)):
        print(f"Non-numeric value detected for topic {topic}, sending update.")
        return True

    # Get sensor type from topic (e.g., "sensors/temperature/room1" -> "temperature")
    sensor_type = None
    if topic.startswith("sensors/"):
        parts = topic.split('/')
        if len(parts) >= 4:
            sensor_type = parts[3]

    # Find tolerances for this sensor type
    tolerances = SENSOR_TOLERANCES.get(sensor_type, {
        "percent": DEFAULT_TOLERANCE_PERCENT,
        "absolute": DEFAULT_TOLERANCE_ABSOLUTE
    })

    # Calculate Changes
    absolute_change = abs(current_value - last_value)
    # Avoid division by zero
    if current_value == 0.0 and last_value == 0.0:
        percent_change = 0.0
        return False
    elif last_value == 0.0 and current_value != 0.0:
        percent_change = 100.0  # from 0 to something is 100% change
        print(f"Significant change for {topic}: from 0 to {current_value}")
        return True
    elif current_value == 0.0 and last_value != 0.0:
        percent_change = 100.0  # from something to 0 is 100% change
        print(f"Significant change for {topic}: from {last_value} to 0")
        return True
    else:
        percent_change = (absolute_change / abs(last_value) * 100) if last_value != 0 else float('inf')

    # Check if the change exceeds the defined tolerances
    percent_tolerance = tolerances.get("percent", DEFAULT_TOLERANCE_PERCENT)
    absolute_tolerance = tolerances.get("absolute", DEFAULT_TOLERANCE_ABSOLUTE)

    exceeds_absolute = absolute_change >= tolerances["absolute"]
    exceeds_percent = percent_change >= tolerances["percent"]

    print(f"Changes for {topic}: absolute={absolute_change:.2f} (threshold={absolute_tolerance}), percent={percent_change:.2f}% (threshold={percent_tolerance}%)")

# If change doesn't exceed tolerances, check time constraint last
    if not (exceeds_absolute or exceeds_percent):
        # Check minimum time between updates
        if topic in last_timestamps:
            elapsed_time = timestamp - last_timestamps[topic]
            if elapsed_time < MIN_TIME_BETWEEN_UPDATES:
                print(f"No significant change and minimum time not reached for {topic}: {elapsed_time}s < {MIN_TIME_BETWEEN_UPDATES}s")
                return False

    return exceeds_absolute or exceeds_percent

def extract_sensor_value(message):
    """ Get the numerical value from the message payload. """
    if isinstance(message, dict):
        if "fields" in message:
            print(f"Extracting from fields: {message['fields']}")
            fields = message["fields"]
            for field in SENSOR_FIELDS.split(","):
                print(f"Checking field: {field}")
                field = field.strip()
                if field in fields:
                    return fields[field]

    # Fallback: if message is a simple value
    elif isinstance(message, (int, float)):
        print(f"Message is a direct numeric value: {message}")
        return message

    return None

def extract_light_actuator_ack(message):
    """ Extract value from light actuator ack messages. """
    if isinstance(message, dict):
        if "fields" in message:
            fields = message["fields"]
            if "light_status" in fields:
                return fields["light_status"]
    return None

def update_last_value(topic, value, timestamp):
    """ Update the last known value and timestamp for a topic. """
    last_values[topic] = value
    last_timestamps[topic] = timestamp

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        print(f"Received MQTT message on topic {msg.topic}: {payload}")
        message = json.loads(payload) if payload.startswith("{") else {"payload": payload}

        topic = msg.topic
        timestamp = int(time.time() * 1000)
        # Branch by topic namespace
        if topic.startswith("sensors/"):
            # Extract sensor values
            print(f"Processing sensor message on topic {topic}")
            sensor_value = extract_sensor_value(message)
            print(f"Extracted sensor value: {sensor_value}")
            light_actuator_value = extract_light_actuator_ack(message)
            if sensor_value is None and light_actuator_value is not None:
                sensor_value = light_actuator_value
                print(f"Extracted light actuator ack value: {sensor_value}")

            # Check tolerances
            if sensor_value is not None and not check_tolerance(topic, sensor_value, timestamp):
                print(f"Skipping sensor update for {topic} due to tolerance limits.")
                return
            
            # Update last known value
            if sensor_value is not None:
                update_last_value(topic, sensor_value, timestamp)

            # Forward raw sensor message to Kafka for Telegraf's json_v2 parser
            kafka_msg = {"topic": topic, "message": message}
            producer.send(KAFKA_TOPIC, kafka_msg)
            print(f"Forwarded sensor to Kafka: {kafka_msg}")

        elif topic.startswith("actuators/"):
            # Treat actuator topics as locally executed commands.
            # Do NOT forward the actuator command to the central KAFKA_TOPIC to avoid polluting metrics.
            # Instead, emit an action event for observability.
            action_payload = message.get("body", message)  # accept either wrapped or direct payload
            status_msg = {
                "event": "action_executed",
                "site_id": SITE_ID,
                "topic": topic,
                "body": action_payload,
                "timestamp": int(time.time() * 1000),
            }

            # If this is a light actuator ack, publish an equivalent sensors/... message back to MQTT
            # so the normal sensors/# path will pick it up and forward it to Kafka.
            try:
                light_ack = extract_light_actuator_ack(action_payload)
                if light_ack is not None:
                    sensor_topic = topic.replace("actuators/", "sensors/", 1)
                    sensor_payload = {
                        "fields": {
                            "value": light_ack,
                            "status": "ack"
                        },
                        "timestamp": int(time.time() * 1000)
                    }
                    print(f"Publishing light actuator ack to MQTT {sensor_topic}: {sensor_payload}")
                    mqtt_client.publish(sensor_topic, json.dumps(sensor_payload))
            except Exception as e:
                print(f"Failed to publish light ack to MQTT: {e}")
            producer.send(KAFKA_ACTIONS_TOPIC, status_msg)
            print(f"Reported executed action to Kafka: {status_msg}")
        else:
            # Generic fallback: check for headers directing a local route
            headers = message.get("headers", {}) if isinstance(message, dict) else {}
            local = headers.get("local", False)
            target = headers.get("target")
            if local and target:
                target_topic = f"{MQTT_PUB_TOPIC_PREFIX}{target}"
                action_payload = message.get("body", {}) if isinstance(message, dict) else message
                print(f"Routing local command to {target_topic}: {action_payload}")
                client.publish(target_topic, json.dumps(action_payload))
                status_msg = {
                    "event": "action_executed",
                    "site_id": SITE_ID,
                    "topic": target_topic,
                    "body": action_payload,
                    "timestamp": int(time.time() * 1000),
                }
                producer.send(KAFKA_ACTIONS_TOPIC, status_msg)
                print(f"Reported executed action to Kafka: {status_msg}")
            else:
                # Ensure message has a timestamp for Telegraf
                if isinstance(message, dict) and "timestamp" not in message:
                    try:
                        message["timestamp"] = timestamp
                    except Exception:
                        pass
                kafka_msg = {"topic": topic, "message": message}
                producer.send(KAFKA_TOPIC, kafka_msg)
                print(f"Forwarded message to Kafka (fallback): {kafka_msg}")

    except Exception as e:
        print(f"Error processing message: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Connect to MQTT with retry logic
def connect_to_mqtt():
    max_retries = 10
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            print(f"Attempting to connect to MQTT broker (attempt {attempt + 1}/{max_retries})...")
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            print("Successfully connected to MQTT broker!")
            break
        except Exception as e:
            print(f"MQTT connection failed: {e}. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    else:
        raise Exception("Failed to connect to MQTT broker after maximum retries")

connect_to_mqtt()
mqtt_client.loop_forever()