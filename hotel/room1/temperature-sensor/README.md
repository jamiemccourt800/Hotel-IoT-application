# Temperature Sensor — Room IoT Device

This service simulates a room temperature sensor that continuously publishes temperature readings to the local MQTT broker.
It represents an IoT device within a hotel room.

## Overview
**Publishes:** `sensors/<hotel_id>/<room>/<sensor>`  
**Measurement:** `temperature`

### Example message
```json
{
  "measurement": "temperature",
  "tags": {"hotel_id": "hotel_01", "room": "101", "sensor": "temperature-sensor"},
  "fields": {"temperatureC": 23.7},
  "timestamp": 1695800105123
}
```

## Configuration
| Variable | Default | Description |
|-----------|----------|-------------|
| MQTT_BROKER | mosquitto | MQTT broker host |
| MQTT_PORT | 1883 | MQTT broker port |
| HOTEL_ID | hotel_01 | Hotel identifier |
| ROOM | 101 | Room identifier |
| SENSOR | temperature-sensor | Sensor name |
| SPEED | 1.0 | Replay speed multiplier |
| MQTT_QOS | 1 | MQTT QoS level |
| MQTT_RETAIN | false | Retain flag |

## Run
```bash
docker compose -f hotel/docker-compose.hotel1.yml up -d temperature-sensor
```

## Testing / Verify

### 1) Verify in Grafana (VictoriaMetrics)
1. Log in to Grafana.
2. Go to **Explore** → Select the **VictoriaMetrics** datasource.
3. Run this query:
```
temperature_temperatureC{db="victoriametrics",host="fed469becd80",hotel_id="hotel_01",room="101",sensor="temperature-sensor"}
```
You should see a live graph of temperature readings over time.

### 2) Watch MQTT logs from the container
To confirm the sensor is publishing and the MQTT broker is receiving:
```bash
docker compose -f hotel/docker-compose.hotel1.yml logs -f temperature-sensor
docker compose -f hotel/docker-compose.hotel1.yml logs -f mosquitto
```
