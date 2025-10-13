from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import logging
from kafka_producer import start_producer, stop_producer, send_message
from config import config
from routes.health import health_check
import json, uuid, time

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_producer()
    msg = "App startup at " + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    logger.info(msg)
    yield
    await stop_producer()
    msg = "App ended at " + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    logger.info(msg)

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    return await health_check()


@app.post("/send_command/{hotel_id}/{room_number}/temperature/{value}")
async def send_command(
    hotel_id: str,
    room_number: int,
    value: float,
):
    """
    Send a command to a specific device in a hotel room.

    Args:
        hotel_id (str): The ID of the hotel.
        room_number (int): The room number.
        value (float): The value associated with the command.
    Returns:
        dict: A dictionary indicating success or failure.
    """
    from routes.actuator import set_temperature
    try:
        return await set_temperature(hotel_id, room_number, value)
    except Exception as e:
        logger.error(f"Error in send_command: {e}", exc_info=True)
        return {"status": "fail", "error": str(e)}

