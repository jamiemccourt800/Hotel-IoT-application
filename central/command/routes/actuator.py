import json
import time
import uuid

from app import logger
from kafka_producer import send_message


async def set_temperature(hotel_id: str, room_number: int, temperature: float):
    """
    Set the target temperature for a room's thermostat.
    Publishes the target temperature asynchronously to Kafka.
    """
    # Create Kafka topic similar to your MQTT topic structure
    thermostat_topic = f"actuators/{hotel_id}/{room_number}/thermostat"

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