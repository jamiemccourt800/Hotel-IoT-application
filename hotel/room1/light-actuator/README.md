# Light Actuator — Room IoT Device

This service simulates a controllable light actuator. It receives MQTT commands to toggle on/off or adjust brightness and publishes its current state.

## Overview
**Listens:** `commands/<hotel_id>/<room>/<sensor>`  
**Publishes:** `sensors/<hotel_id>/<room>/<sensor>` with `measurement: light-state`

### Example state
```json
{
  "measurement": "light-state",
  "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "light-actuator"},
  "fields": {"state": "on", "brightness": 42},
  "timestamp": 1695800110456
}
```

## Configuration
| Variable | Default | Description |
|-----------|----------|-------------|
| MQTT_BROKER | mosquitto | MQTT broker host |
| MQTT_PORT | 1883 | MQTT port |
| HOTEL_ID | hotel_01 | Hotel ID |
| ROOM | 101 | Room number |
| ACTUATOR_ID | light-actuator | Device ID |
| DEFAULT_BRIGHTNESS | 50 | Default brightness value |

## Run
```bash
docker compose -f hotel/docker-compose.hotel1.yml up -d light-actuator
```

## Testing / Verify

### 1) Send commands via FastAPI (Command service)
Use the **Command FastAPI service** to control the actuator and verify behavior.

- Open API docs:
  ```
  http://<command-host>:<port>/docs
  ```
- Use `POST /actuator/light` with:
  ```json
  {
    "hotel_id": "hotel_01",
    "room": "101",
    "sensor": "light-actuator",
    "state": "on",
    "brightness": 42
  }
  ```

**Or via curl:**
```bash
CMD_BASE=http://localhost:8000
curl -X POST "$CMD_BASE/actuator/light" -H "Content-Type: application/json"   -d '{"hotel_id":"hotel_01","room":"101","sensor":"light-actuator","state":"on","brightness":42}'
```

### 2) Watch actuator & MQTT logs
```bash
docker compose -f hotel/docker-compose.hotel1.yml logs -f light-actuator
docker compose -f hotel/docker-compose.hotel1.yml logs -f mosquitto
```
Confirm you see `light-state` messages with the new state and brightness.
