# temperature-sensor

A standalone containerized emulator that publishes temperature telemetry to MQTT.


## Topics
- Telemetry: `hotel_01/101/temperature-sensor/telemetry`
- Status (online/offline): `hotel_01/101/temperature-sensor/status`


## Configuration (env)
- HOTEL_ID, ROOM, SENSOR
- BROKER, BROKER_PORT, QOS, KEEPALIVE
- MODE (`random`|`csv`), INTERVAL, SPEED
- START_TEMP, TARGET_TEMP, CSV_PATH


## Build & Run (with a local broker)
```bash
docker run -d --name mqtt-broker -p 1883:1883 eclipse-mosquitto:2

docker build -t temperature-sensor:latest .
docker run --rm --name temperature-sensor-101 \
  -e HOTEL_ID=hotel_01 -e ROOM=101 -e SENSOR=temperature-sensor \
  -e BROKER=host.docker.internal -e BROKER_PORT=1883 \
  -e MODE=random -e INTERVAL=1.0 -e SPEED=1.0 \
  temperature-sensor:latest
```