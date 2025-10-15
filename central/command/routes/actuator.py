import json
import time
import uuid
import logging

from kafka_producer import send_message

logger = logging.getLogger("actuator_routes")


async def set_temperature(hotel_id: str, room_number: int, temperature: float):
    """
    Set the target temperature for a room's thermostat.
    Publishes the target temperature asynchronously to Kafka.
    """
    # Create Kafka topic similar to your MQTT topic structure
    # Use dot-delimited Kafka topic naming (slashes are not valid in Kafka topics)
    thermostat_topic = f"actuators.{hotel_id}.{room_number}.thermostat"

    # Build message payload
    message = {
        "id": str(uuid.uuid4()),
        "timestamp": int(time.time()),
        "target_temperature": temperature
    }
    message_bytes = json.dumps(message).encode("utf-8")

    try:
        # Async send in background
        await send_message(thermostat_topic, message_bytes)
        logger.info(f"Enqueued temperature set: hotel {hotel_id}, room {room_number}, target {temperature}")
        return {"status": "success", "target_temperature": temperature}

    except Exception as e:
        logger.error(f"Failed to enqueue temperature for hotel {hotel_id}, room {room_number}: {e}")
        return {"status": "error", "error": str(e)}


async def set_light_action(hotel_id: str, room_number: int, action: str, value: int | None = None):
    """
    Send a light actuator command for a specific room.

    Produces a Kafka message to topic:
      actuators.{hotel_id}.{room_number}.light-actuator.cmd

    The Kafka→MQTT bridge maps this to MQTT topic:
      {hotel_id}/{room_number}/light-actuator/cmd

    Message format matches the actuator's expected schema:
      {"messageId": "uuid", "fields": {"action": "on|off|toggle|set_brightness", "value": optional-int}}
    """
    # Validate action
    allowed = {"on", "off", "toggle", "set_brightness"}
    if action not in allowed:
        return {"status": "error", "error": f"unsupported_action:{action}"}

    topic = f"actuators.{hotel_id}.{room_number}.light-actuator.cmd"
    message = {
        "messageId": str(uuid.uuid4()),
        "fields": {"action": action}
    }
    if action == "set_brightness":
        if value is None:
            return {"status": "error", "error": "missing_value"}
        try:
            ival = int(value)
        except Exception:
            return {"status": "error", "error": "invalid_value"}
        message["fields"]["value"] = ival

    try:
        await send_message(topic, json.dumps(message).encode("utf-8"))
        logger.info(f"Enqueued light action: hotel {hotel_id}, room {room_number}, action {action}, value {value}")
        return {"status": "success", "action": action, "value": value}
    except Exception as e:
        logger.error(f"Failed to enqueue light action for hotel {hotel_id}, room {room_number}: {e}")
        return {"status": "error", "error": str(e)}