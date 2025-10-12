import json
import time
import uuid

from central.command.app import logger
from central.command.kafka_producer import send_message


async def set_temperature(req: TemperatureRequest, background_tasks: BackgroundTasks):
    """
    Set the target temperature for a room's thermostat.
    Publishes the target temperature asynchronously to Kafka.
    """
    # Create Kafka topic similar to your MQTT topic structure
    thermostat_topic = f"actuators/{req.hotel_id}/{req.room_number}/thermostat"

    # Build message payload
    message = {
        "id": str(uuid.uuid4()),
        "timestamp": int(time.time()),
        "target_temperature": req.temperature
    }
    message_bytes = json.dumps(message).encode("utf-8")

    try:
        # Async send in background
        background_tasks.add_task(send_message, thermostat_topic, message_bytes)
        logger.info(f"Enqueued temperature set: hotel {req.hotel_id}, room {req.room_number}, target {req.temperature}")
        return {"status": "success", "target_temperature": req.temperature}

    except Exception as e:
        logger.error(f"Failed to enqueue temperature for hotel {req.hotel_id}, room {req.room_number}: {e}")
        return {"status": "error", "error": str(e)}