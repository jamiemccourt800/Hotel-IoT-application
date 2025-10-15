import os
import time
import json
from typing import Optional

import paho.mqtt.client as mqtt
from kafka import KafkaConsumer
from kafka.errors import KafkaError

# Environment
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_GROUP = os.getenv("KAFKA_GROUP", "hotel-bridge")
KAFKA_PATTERN = os.getenv("KAFKA_PATTERN", "actuators.*")

MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_QOS = int(os.getenv("MQTT_QOS", "1"))
MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", "60"))


def make_mqtt_client() -> mqtt.Client:
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    return client


def mqtt_connect(client: mqtt.Client) -> None:
    attempts, max_attempts, delay = 0, 20, 3
    while True:
        try:
            attempts += 1
            print(f"Connecting to MQTT at {MQTT_BROKER}:{MQTT_PORT} (attempt {attempts}/{max_attempts})")
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=MQTT_KEEPALIVE)
            client.loop_start()
            print("Connected to MQTT")
            return
        except Exception as e:
            if attempts >= max_attempts:
                raise
            print(f"MQTT connect failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)


def make_kafka_consumer() -> KafkaConsumer:
    attempts, max_attempts, delay = 0, 20, 3
    while True:
        try:
            attempts += 1
            print(f"Creating KafkaConsumer for {KAFKA_BROKER} (attempt {attempts}/{max_attempts})")
            consumer = KafkaConsumer(
                bootstrap_servers=KAFKA_BROKER,
                group_id=KAFKA_GROUP,
                enable_auto_commit=True,
                auto_offset_reset="earliest",
                value_deserializer=lambda v: v,  # keep as bytes
            )
            consumer.subscribe(pattern=KAFKA_PATTERN)
            print(f"Subscribed to Kafka topics matching pattern: {KAFKA_PATTERN}")
            return consumer
        except Exception as e:
            if attempts >= max_attempts:
                raise
            print(f"Kafka not ready: {e}. Retrying in {delay}s...")
            time.sleep(delay)


def to_mqtt_payload(value: bytes) -> str:
    try:
        s = value.decode("utf-8")
    except Exception:
        s = str(value)
    # If already a JSON string that's fine; otherwise keep raw text
    return s


def map_kafka_topic_to_mqtt(kafka_topic: str) -> str:
    # Convert Kafka topics to the actuator's MQTT topics.
    # Expected Kafka pattern: actuators.<hotel>.<room>.light-actuator.cmd
    # Actuator MQTT topic:    <hotel>/<room>/light-actuator/cmd
    t = kafka_topic
    if t.startswith("actuators."):
        t = t[len("actuators."):]
    # If already using slashes, return as-is; else convert dots to slashes
    if "/" in t:
        return t
    return t.replace(".", "/")


def main():
    mqtt_client = make_mqtt_client()
    mqtt_connect(mqtt_client)

    consumer = make_kafka_consumer()

    print("Bridging Kafka -> MQTT started")
    while True:
        try:
            for msg in consumer:
                mqtt_topic = map_kafka_topic_to_mqtt(msg.topic)
                payload = to_mqtt_payload(msg.value)
                print(f"Kafka -> MQTT: {msg.topic} -> {mqtt_topic} : {payload}")
                result = mqtt_client.publish(mqtt_topic, payload, qos=MQTT_QOS)
                status = result[0] if isinstance(result, tuple) else result.rc
                if status != mqtt.MQTT_ERR_SUCCESS:
                    print(f"MQTT publish error (rc={status}) for topic {mqtt_topic}")
        except KafkaError as e:
            print(f"Kafka error: {e}. Recreating consumer...")
            try:
                consumer.close()
            except Exception:
                pass
            time.sleep(2)
            consumer = make_kafka_consumer()
        except Exception as e:
            print(f"Unexpected loop error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
