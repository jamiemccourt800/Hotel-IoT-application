import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

from kafka_producer import start_producer, stop_producer, send_message
from config import config
from controller.health import health_check
from controller.actuator import set_light_action, get_metric, get_metric_timeseries
import json, uuid, time
import httpx

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

SERVICE_NAME = "command"
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format=f'%(asctime)s - {SERVICE_NAME} - %(levelname)s - %(message)s',
)

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

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    from controller.actuator import set_temperature
    try:
        return await set_temperature(hotel_id, room_number, value)
    except Exception as e:
        logger.error(f"Error in send_command: {e}", exc_info=True)
        return {"status": "fail", "error": str(e)}


@app.post("/actuator/light/{hotel_id}/{room_number}/on")
async def light_on(hotel_id: str, room_number: int):
    try:
        return await set_light_action(hotel_id, 
                                      room_number, "on")
    except Exception as e:
        logger.error(f"Error in light_on: {e}", exc_info=True)
        return {"status": "fail", "error": str(e)}


@app.post("/actuator/light/{hotel_id}/{room_number}/off")
async def light_off(hotel_id: str, room_number: int):
    try:
        return await set_light_action(hotel_id, room_number, "off")
    except Exception as e:
        logger.error(f"Error in light_off: {e}", exc_info=True)
        return {"status": "fail", "error": str(e)}


@app.post("/actuator/light/{hotel_id}/{room_number}/toggle")
async def light_toggle(hotel_id: str, room_number: int):
    try:
        return await set_light_action(hotel_id, room_number, "toggle")
    except Exception as e:
        logger.error(f"Error in light_toggle: {e}", exc_info=True)
        return {"status": "fail", "error": str(e)}


@app.post("/actuator/light/{hotel_id}/{room_number}/brightness/{value}")
async def light_brightness(hotel_id: str, room_number: int, value: int):
    try:
        return await set_light_action(hotel_id, room_number, "set_brightness", value)
    except Exception as e:
        logger.error(f"Error in light_brightness: {e}", exc_info=True)
        return {"status": "fail", "error": str(e)}

@app.post("/actuator/humidity/{hotel_id}/{room_number}/set_target/{value}")
async def set_humidity_target_endpoint(hotel_id: str, room_number: int, value: float):
    try:
        from controller.actuator import set_humidity_target
        return await set_humidity_target(hotel_id, room_number, value)
    except Exception as e:
        logger.error(f"Error in set_humidity_target_endpoint: {e}", exc_info=True)
        return {"status": "fail", "error": str(e)}  
    

@app.get("/actuator/light/{hotel_id}/{room_number}/brightness")
async def light_brightness(hotel_id: str, room_number: int):
    async with httpx.AsyncClient() as http:
        try:
            metric = "light-state_brightness"
            sensor = "light-sensor"
            state = await get_metric(http, metric, hotel_id, str(room_number), sensor)
            return {"status": "success", "state": state}
        except Exception as e:
            logger.error(f"Error in light_state: {e}", exc_info=True)
            return {"status": "fail", "error": str(e)}

@app.get("/actuator/humidity/{hotel_id}/{room_number}/state")
async def light_brightness(hotel_id: str, room_number: int):
    async with httpx.AsyncClient() as http:
        try:
            metric = "humidity_humidityPercent"
            sensor = "humidity-sensor"
            state = await get_metric(http, metric, hotel_id, str(room_number), sensor=sensor)
            return {"status": "success", "state": state}
        except Exception as e:
            logger.error(f"Error in light_state: {e}", exc_info=True)
            return {"status": "fail", "error": str(e)}

@app.get("/actuator/light/{hotel_id}/{room_number}/state")
async def light_state(hotel_id: str, room_number: int):
    async with httpx.AsyncClient() as http:
        try:
            metric = "light-status_mode"
            sensor= "light-actuator"
            state = await get_metric(http,metric, hotel_id, str(room_number), sensor)
            return {"status": "success", "state": state}
        except Exception as e:
            logger.error(f"Error in light_state: {e}", exc_info=True)
            return {"status": "fail", "error": str(e)}

@app.get("/actuator/temperature/{hotel_id}/{room_number}/current")
async def current_temperature(hotel_id: str, room_number: int):
    async with httpx.AsyncClient() as http:
        try:
            metric = "temperature_temperatureC"
            temp = await get_metric(http, metric, hotel_id, str(room_number))
            return {"status": "success", "temperature": temp}
        except Exception as e:
            logger.error(f"Error in current_temperature: {e}", exc_info=True)
            return {"status": "fail", "error": str(e)}


@app.get("/api/metrics/timeseries")
async def timeseries(hotel_id: str, room: str, metric: str, hours: int = 6):
    async with httpx.AsyncClient() as client:
        data = await get_metric_timeseries(client, metric, hotel_id, room, hours)
    return data

