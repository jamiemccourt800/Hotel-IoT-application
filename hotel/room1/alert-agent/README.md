# Alert Agent — Room-level Watchdog

The Alert Agent monitors both **temperature-sensor** and **light-actuator** messages for anomalies and publishes alert messages when thresholds are exceeded.

## Overview
**Subscribes:** `sensors/#`  
**Publishes:** `sensors/<hotel_id>/<room>/<sensor>` with `measurement: alert`

### Example
```json
{
  "measurement": "alert",
  "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "light-actuator"},
  "fields": {
    "alert_type": "brightness_out_of_range",
    "severity": "warning",
    "message": "Brightness out of range: 200"
  },
  "timestamp": 1695800110459
}
```

## Alerts
| Type | Condition | Severity |
|------|------------|-----------|
| temp_high | temperature ≥ 28°C | warning |
| actuator_state_changed | state/brightness changed | info |
| brightness_out_of_range | brightness <0 or >100 | warning |
| sensor_offline | no message >120s | critical |

## Configuration
| Variable | Default | Description |
|-----------|----------|-------------|
| MQTT_BROKER | mosquitto | MQTT broker |
| MQTT_PORT | 1883 | Broker port |
| HOTEL_ID | hotel_01 | Hotel ID |
| ROOM | 101 | Room number |
| TEMP_HIGH_C | 28 | High temp threshold |
| OFFLINE_TIMEOUT_S | 120 | Offline timeout |
| DEDUP_WINDOW_S | 60 | Dedupe window |

## Run
```bash
docker compose -f hotel/docker-compose.hotel1.yml up -d alert-agent
```

## Testing / Verify

### 1) Trigger an alert via FastAPI
Use the **Command FastAPI service** to issue a command that should generate an alert (e.g., out-of-range brightness):

```bash
CMD_BASE=http://localhost:8000
curl -X POST "$CMD_BASE/actuator/light" -H "Content-Type: application/json"   -d '{"hotel_id":"hotel_01","room":"101","sensor":"light-actuator","state":"on","brightness":200}'
```

### 2) Watch alert-agent & MQTT logs
```bash
docker compose -f hotel/docker-compose.hotel1.yml logs -f alert-agent
docker compose -f hotel/docker-compose.hotel1.yml logs -f mosquitto
```
Confirm you see `measurement="alert"` messages with `alert_type="brightness_out_of_range"` and `severity="warning"`.

You can also verify end-to-end by viewing alert messages in Grafana Explore once they are ingested via the MQTT → Kafka → VictoriaMetrics pipeline.
