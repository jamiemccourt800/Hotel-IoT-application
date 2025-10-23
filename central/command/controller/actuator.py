import json
import time
import uuid
import logging
import os
from kafka_producer import send_message

logger = logging.getLogger("actuator_routes")

VICTORIA_BASE_URL = os.getenv("VICTORIA_BASE_URL", "http://localhost:8428")
LIGHT_METRIC = os.getenv("LIGHT_METRIC", "light_status") 
LIGHT_WINDOW = os.getenv("LIGHT_WINDOW", "5m")

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


async def get_light_state(http, hotel_id: str, room: str) -> float | None:
    """Gets the current light level in the room

    Uses PromQL: last_over_time(METRIC{hotel_id="...",room="..."}[LIGHT_WINDOW])
    Returns the numeric value or None if not found.
    """
    promql = f'last_over_time({LIGHT_METRIC}{{hotel_id="{hotel_id}",room="{room}"}}[{LIGHT_WINDOW}])'
    try:
        r = await http.get(
            f"{VICTORIA_BASE_URL}/api/v1/query",
            params={"query": promql},
        )
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "success":
            logger.warning(f"VM query not successful: {data}")
            return None
        result = data.get("data", {}).get("result") or []
        if not result:
            return None
        value = result[0].get("value")
        if isinstance(value, list) and len(value) >= 2:
            try:
                return float(value[1])
            except Exception:
                return None
        return None
    except Exception as e:
        logger.error(f"Error querying VictoriaMetrics: {e}")
        return None