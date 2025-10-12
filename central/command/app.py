from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import logging
from kafka_producer import start_producer, stop_producer, send_message
from config import config
from routes.health import health_check
import json, uuid, time

app = FastAPI()
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

@asynccontextmanager
async def lifespan():
    await start_producer()
    msg = "App startup at " + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    logger.info(msg)
    yield
    await stop_producer()
    msg = "App ended at " + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    logger.info(msg)

@app.get("/health")
async def health():
    return await health_check()


# @app.post("/send_command/{hotel_id}/{room_number}/{device_type}/{command_type}")
# async def send_command(
#     hotel_id: str,
#     room_number: int,
#     device_type: str,
#     command_type: str,
#     command_value: dict,
#     background_tasks: BackgroundTasks,
# ):
#     """
#     Send a command to a specific device in a hotel room.
#
#     Args:
#         hotel_id (str): The ID of the hotel.
#         room_number (int): The room number.
#         device_type (str): The type of device (e.g., "thermostat", "light").
#         command_type (str): The type of command (e.g., "set_temperature", "turn_on").
#         command_value (dict): The value associated with the command.