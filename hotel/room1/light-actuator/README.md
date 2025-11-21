# Light Actuator

Modular light control actuator for hotel room automation.

## Features

- Light on/off control
- Brightness control (0-100)
- Toggle functionality
- State publishing to MQTT
- Command acknowledgments

## Environment Variables

- `HOTEL_ID`: Hotel identifier (default: "hotel_01")
- `ROOM`: Room number (default: 101)
- `SENSOR`: Sensor identifier (default: "light-actuator")
- `BROKER`: MQTT broker host
- `BROKER_PORT`: MQTT broker port (default: 1883)

## MQTT Topics

### Subscribed
- Commands: `{hotel_id}/{room}/light-actuator/cmd`

### Published
- State: `{hotel_id}/{room}/light-actuator/state`
- Acknowledgments: `{hotel_id}/{room}/light-actuator/ack`

## Command Format

```json
{
  "action": "on",
  "payload": {
    "brightness": 75
  }
}
```

### Supported Actions

- `on`: Turn light on (optionally with brightness)
- `off`: Turn light off
- `toggle`: Toggle light state
- `set_brightness`: Set brightness level (0-100)

## State Message Format

```json
{
  "measurement": "light-state",
  "tags": {
    "hotel_id": "hotel_01",
    "room": 101,
    "sensor": "light-actuator"
  },
  "fields": {
    "state_on": 1,
    "state_brightness": 75
  },
  "timestamp": 1700000000000
}
```
