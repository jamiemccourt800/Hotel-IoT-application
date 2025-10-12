import json

import paho.mqtt.client as mqtt
from datetime import datetime
import os

from fastapi import FastAPI

app = FastAPI()

MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

def get_mqtt_client():
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 2)
    return client

@app.get("/health")
def health_check():
    client = mqtt.Client()
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 2)
        client.disconnect()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.post("{hotel_id}/actuators/{room_number}/thermostat")
def set_temperature(hotel_id: str, room_number: int, temperature: float = None):
    """
    Set the target temperature for a room's thermostat.

    Args:
        room_number (int): The room number to set the thermostat for.

    Request Body (form-data):
        temperature (float): The target temperature to set.

    Returns:
        dict: Status of the operation and the target temperature if successful,
              or error details if failed.
              :param hotel_id:
              :param room_number:
              :param temperature:
    """
    from flask import request
    # set the temperature topics
    thermostat_topic = f"actuators/{hotel_id}/{room_number}/thermostat"
    thermometer_topic = f"sensors/{hotel_id}/{room_number}/thermometer"

    # publish the temperature to the MQTT broker
    if get_mqtt_client().publish(thermostat_topic, temperature):
        return {"status": "success", "target_temperature": temperature}

    else:
        # publish updated temperature to the MQTT broker to get the data in DB,
        # although this has to be done the way the thermostat and thermometer are different devices
        # get_mqtt_client().publish(thermometer_topic, json.dumps({"get": "temperature"}))
        return {"status": "error", "error": "Failed to publish temperature to MQTT broker"}