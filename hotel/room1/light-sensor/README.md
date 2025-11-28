# Light Sensor

Modular ambient light sensor for hotel room automation.

## Features

- Time-of-day based light simulation
- Publishes ambient brightness levels (0-100)
- MQTT telemetry publishing
- Shared common libraries with other sensors

## Environment Variables

- `HOTEL_ID`: Hotel identifier (default: "hotel_01")
- `ROOM`: Room number (default: 101)
- `SENSOR`: Sensor identifier (default: "light-sensor")
- `BROKER`: MQTT broker host
- `BROKER_PORT`: MQTT broker port (default: 1883)
- `INTERVAL`: Publishing interval in seconds (default: 2.0)
- `MODE`: Simulation mode - "simulation" or "static" (default: "simulation")
- `INITIAL_BRIGHTNESS`: Initial brightness level (default: 50)

## MQTT Topics

- Telemetry: `{hotel_id}/{room}/light-sensor/telemetry`
- Status: `{hotel_id}/{room}/light-sensor/status`

## Message Format

```json
{
  "measurement": "light-state",
  "tags": {
    "hotel_id": "hotel_01",
    "room": 101,
    "sensor": "light-sensor"
  },
  "fields": {
    "ambient_brightness": 75
  },
  "timestamp": 1700000000000
}
```
