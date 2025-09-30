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

# Kafka settings
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "mqtt_messages")
KAFKA_ACTIONS_TOPIC = os.getenv("KAFKA_ACTIONS_TOPIC", "executed_actions")

# Kafka producer with retry logic
def create_kafka_producer():
    max_retries = 10
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            print(f"Attempting to connect to Kafka (attempt {attempt + 1}/{max_retries})...")
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
            print(f"Unexpected error connecting to Kafka: {e}")
            time.sleep(retry_delay)
    
    raise Exception("Failed to connect to Kafka after maximum retries")

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

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        message = json.loads(payload) if payload.startswith("{") else {"payload": payload}

        topic = msg.topic
        # Branch by topic namespace
        if topic.startswith("sensors/"):
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