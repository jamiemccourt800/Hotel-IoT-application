# Temperature Actuator — HVAC/Thermostat Control

This service controls room temperature by managing HVAC systems (heating/cooling) based on sensor feedback and commands from the central control system.

## Overview
**Subscribes:**
- `commands/temperature/<hotel_id>/<room>/<sensor>` - Thermostat commands
- `<hotel_id>/<room>/temperature-sensor/telemetry` - Temperature readings

**Publishes:** 
- `<hotel_id>/<room>/thermostat` - Target temperature setpoints
- `<hotel_id>/<room>/hvac-status` - HVAC system status

### Example HVAC status
```json
{
  "measurement": "hvac-status",
  "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "temperature-actuator"},
  "fields": {
    "mode": "heating",
    "power_level": 75.0,
    "target_temperature": 22.0,
    "current_temperature": 20.5
  },
  "timestamp": 1695800110456
}
```

## Configuration
| Variable | Default | Description |
|-----------|----------|-----------|
| MQTT_BROKER | mosquitto | MQTT broker host |
| MQTT_PORT | 1883 | MQTT port |
| HOTEL_ID | hotel_01 | Hotel ID |
| ROOM | 101 | Room number |
| DEFAULT_TARGET | 22.0 | Default target temperature (°C) |
| CONTROL_INTERVAL | 5.0 | Control loop frequency (seconds) |
| DEADBAND | 0.5 | Temperature deadband (°C) |

## Control Algorithm
- **Bang-bang control** with deadband to prevent oscillation
- **Proportional power output** based on temperature error
- **Auto mode** switches between heating/cooling as needed
- **Feedback control** using temperature sensor readings

## Run
```bash
docker compose -f hotel/docker-compose.hotel1.yml up -d temperature-actuator
```

## Testing / Verify

### 1) Send thermostat commands via FastAPI
```bash
CMD_BASE=http://localhost:8000
curl -X POST "$CMD_BASE/actuator/temperature/hotel_01/101" \
  -H "Content-Type: application/json" \
  -d '{"target_temperature": 24.0, "mode": "auto"}'
```

### 2) Monitor HVAC control loop
```bash
docker compose -f hotel/docker-compose.hotel1.yml logs -f temperature-actuator
```
Confirm you see control output messages and HVAC status updates.

### 3) Verify temperature control loop
```bash
# Watch both sensor and actuator working together
docker compose -f hotel/docker-compose.hotel1.yml logs -f temperature-sensor temperature-actuator
```
Confirm the sensor responds to setpoint changes from the actuator.