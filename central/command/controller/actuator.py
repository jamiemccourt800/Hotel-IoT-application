from datetime import datetime
import json
import time
import uuid
import logging
import os
from kafka_producer import send_message
import httpx

logger = logging.getLogger("actuator_routes")

VICTORIA_BASE_URL = os.getenv("VICTORIA_BASE_URL", "http://victoria-metrics:8428")

LIGHT_METRIC = os.getenv("LIGHT_METRIC", "light_status") 
TEMPERATURE_METRIC = os.getenv("TEMPERATURE_METRIC", "room_temperature")
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

async def set_humidity_target(hotel_id: str, room_number: int, value: float):
    """
    Send a command to set target humidity for a specific room.

    Produces a Kafka message to topic:
      actuators.{hotel_id}.{room_number}.humidity-actuator.cmd
    Args:
        hotel_id (str): The ID of the hotel.
        room_number (int): The room number.
        value (float): The target humidity value.
    Returns:
        dict: A dictionary indicating success or failure.
    """
    try:
        topic = f"actuators.{hotel_id}.{room_number}.humidity-actuator.cmd"
        message = {
            "command": "set_target_humidity",
            "value": value,
            "timestamp": int(time.time() * 1000)
        }
        await send_message(topic, json.dumps(message).encode('utf-8'))
        logger.info(f"Sent humidity target command to {topic}: {message}")
        return {"status": "success", "message": f"Command sent to {topic}"}
    except Exception as e:
        logger.error(f"Error in set_humidity_target: {e}", exc_info=True)
        return {"status": "fail", "error": str(e)}
    
async def get_metric(http: httpx.Client, metric: str, hotel_id: str, room: str, sensor: str = None) -> float | None:
    """Generic function to query VictoriaMetrics for a single value metric."""
    
    if sensor:
        promql =  f'last_over_time({metric}{{hotel_id="{hotel_id}", room="{room}", sensor="{sensor}"}}[1m])'
    else:
        promql = f'last_over_time({metric}{{hotel_id="{hotel_id}", room="{room}"}}[1m])'
    try:
        resp = await http.get(f"{VICTORIA_BASE_URL}/api/v1/query", params={"query": promql}, timeout=10)                
        resp.raise_for_status()
        payload = resp.json()

        results = payload.get("data", {}).get("result", [])
        if not results:
            return None

        value = results[0].get("value")
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            return float(value[1])

    except (httpx.RequestError, ValueError, TypeError, IndexError) as e:
        logger.warning(f"Error fetching metric {metric}: {e}")
        return None

    return None

async def get_metric_timeseries(http: httpx.AsyncClient, metric: str, hotel_id: str, room: str, sensor: str = None, hours: int = 6, step: int = 60):
    end_ts = int(datetime.utcnow().timestamp())
    start_ts = end_ts - hours * 3600

    if sensor: 
        promql = f'{metric}{{hotel_id="{hotel_id}",room="{room}",sensor="{sensor}"}}'
    else:
        promql = f'{metric}{{hotel_id="{hotel_id}",room="{room}"}}'

    try:
        resp = await http.get(
            f"{VICTORIA_BASE_URL}/api/v1/query_range",
            params={"query": promql, "start": start_ts, "end": end_ts, "step": step},
            timeout=10
        )
        resp.raise_for_status()
        payload = resp.json()

        results = payload.get("data", {}).get("result", [])
        if not results:
            logger.warning(f"No data returned for metric {metric} (hotel={hotel_id}, room={room})")
            return []

        values = results[0].get("values", [])
        return [{"timestamp": int(ts) * 1000, "value": float(val)} for ts, val in values]

    except Exception as e:
        logger.warning(f"Error fetching time series metric {metric}: {e}")
        return []