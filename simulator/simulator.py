import paho.mqtt.client as mqtt
import json
import os
import time
import threading
from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO

# MQTT settings
MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
HOTEL_ID = os.getenv("HOTEL_ID", "DUB-Grand")
ROOM_NUMBER = int(os.getenv("ROOM_NUMBER", 621))
THERMOMETER_TOPIC = f"sensors/{HOTEL_ID}/{ROOM_NUMBER}/thermometer"
LIGHT_STATUS_TOPIC = f"sensors/{HOTEL_ID}/{ROOM_NUMBER}/light"
THERMOSTAT_TOPIC = f"actuators/{HOTEL_ID}/{ROOM_NUMBER}/thermostat"
LIGHTSWITCH_TOPIC = f"actuators/{HOTEL_ID}/{ROOM_NUMBER}/light"

# State
state = {
    "temperature": 20,
    "target_temperature": 20,
    "light": False
}

# Use the enum for callback API version (required by paho-mqtt >= 2.0)
mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv311)


# Flask UI
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Handle incoming actuator commands
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)

        if msg.topic == THERMOSTAT_TOPIC:
            state["target_temperature"] = data.get("set", state["target_temperature"])
            print(f"Thermostat set to {state['target_temperature']}°C")
            socketio.emit("state_update", {
                "hotel_id": HOTEL_ID,
                "room": ROOM_NUMBER,
                "state": state
            })

        elif msg.topic == LIGHTSWITCH_TOPIC:
            command = data.get("command")
            if command == "on":
                state["light"] = True
            elif command == "off":
                state["light"] = False
            print(f"Light switched {'ON' if state['light'] else 'OFF'}")
            socketio.emit("state_update", {
                "hotel_id": HOTEL_ID,
                "room": ROOM_NUMBER,
                "state": state
            })

    except Exception as e:
        print(f"Error handling actuator command: {e}")

mqtt_client.on_message = on_message

def mqtt_loop():
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.subscribe(THERMOSTAT_TOPIC)
    mqtt_client.subscribe(LIGHTSWITCH_TOPIC)
    mqtt_client.loop_forever()

# Sensor simulator loop
def sensor_loop():
    while True:
        # Move temperature toward target
        if state["temperature"] < state["target_temperature"]:
            state["temperature"] += 0.1
        elif state["temperature"] > state["target_temperature"]:
            state["temperature"] -= 0.1

        # Kafka-compatible JSON for thermometer
        thermometer_msg = {
            "measurement": "temperature",
            "tags": {
                "hotel_id": HOTEL_ID,
                "room": ROOM_NUMBER,
                "sensor": "thermometer-1"
            },
            "fields": {
                "temperature": round(state["temperature"], 1)
            },
            "timestamp": int(time.time() * 1000)
        }
        mqtt_client.publish(THERMOMETER_TOPIC, json.dumps(thermometer_msg))

        # Kafka-compatible JSON for light status
        light_msg = {
            "measurement": "light",
            "tags": {
                "hotel_id": HOTEL_ID,
                "room": ROOM_NUMBER,
                "sensor": "light-1"
            },
            "fields": {
                "status": int(state["light"])
            },
            "timestamp": int(time.time() * 1000)
        }
        mqtt_client.publish(LIGHT_STATUS_TOPIC, json.dumps(light_msg))

        socketio.emit("state_update", {
            "hotel_id": HOTEL_ID,
            "room": ROOM_NUMBER,
            "state": state
        })
        time.sleep(2)

@app.route("/")
def index():
    return render_template("index.html", state=state)

@app.route("/set_temp", methods=["POST"])
def set_temp():
    target = float(request.form.get("temperature"))
    state["target_temperature"] = target
    mqtt_client.publish(THERMOSTAT_TOPIC, json.dumps({"set": target}))
    socketio.emit("state_update", {
        "hotel_id": HOTEL_ID,
        "room": ROOM_NUMBER,
        "state": state
    })
    return redirect("/")

@app.route("/toggle_light", methods=["POST"])
def toggle_light():
    new_state = not state["light"]
    state["light"] = new_state
    mqtt_client.publish(LIGHTSWITCH_TOPIC, json.dumps({"command": "on" if new_state else "off"}))
    socketio.emit("state_update", {
        "hotel_id": HOTEL_ID,
        "room": ROOM_NUMBER,
        "state": state
    })
    return redirect("/")

def flask_loop():
    socketio.run(app, host="0.0.0.0", port=5000)

if __name__ == "__main__":
    threading.Thread(target=mqtt_loop, daemon=True).start()
    threading.Thread(target=sensor_loop, daemon=True).start()
    flask_loop()