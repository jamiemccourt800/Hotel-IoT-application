# Multi-site IoT Demo (Central + 2 Hotels)

This splits the stack into three compose files:

- `docker-compose.central.yml` — Central HQ: Kafka, VictoriaMetrics, Telegraf, Grafana
- `docker-compose.hotel1.yml` — Hotel Alpha: local Mosquitto, Simulator (room 101), Node-RED, MQTT→Kafka bridge
- `docker-compose.hotel2.yml` — Hotel Beta: local Mosquitto, Simulator (room 202), Node-RED, MQTT→Kafka bridge

The bridge forwards only sensor messages to central Kafka (`mqtt_messages`). Actuator commands are handled locally and only an `actions` event is emitted to Kafka (`executed_actions`).

## API

Current API Calls:
- localhost:5000/hotels
- localhost:5000/hotels/HTL-Alpha/rooms

## Run

- Create a shared network once:
  ```bash
  docker network create iot-net || true
  ```
- Start central HQ:
  ```bash
  docker compose -f docker-compose.central.yml up -d --build
  ```
- Start each hotel:
  ```bash
  docker compose -f docker-compose.hotel1.yml up -d --build
  docker compose -f docker-compose.hotel2.yml up -d --build
  ```

## Ports

- API: http://localhost:5000
- Grafana: http://localhost:3000 (admin/admin)
- VictoriaMetrics: http://localhost:8428
- Node-RED (Hotel 1): http://localhost:1881
- Simulator UI (Hotel 1): http://localhost:5001
- Frontend (React): http://localhost:3001

## Topics

- Sensors publish to `sensors/<HOTEL_ID>/<ROOM>/<sensor>`; forwarded to Kafka topic `mqtt_messages`.
- Actuators consume `actuators/<HOTEL_ID>/<ROOM>/<device>` locally. Bridge publishes an action audit to Kafka topic `executed_actions`.

## Grafana

Datasource is VictoriaMetrics (provisioned). You can graph:
- `temperature` by hotel_id/room
- `light` status
- `actions` measurement for audit trail

## Node-RED

Use Node-RED in each hotel to send actuator commands to the local Mosquitto broker using topics:
- `actuators/HTL-Alpha/101/thermostat` with JSON `{ "set": 23 }`
- `actuators/HTL-Alpha/101/light` with JSON `{ "command": "on" }`
- likewise for HTL-Beta/202

These will switch lights or change thermostat locally, while the action event is reported to central Kafka.

## Developer: run tests (PowerShell)

Preferred: use the Makefile which creates/uses the project venv:

```powershell
# create venv and install test deps (one-time)
make init

# run unit tests
make unit
```

Fallback (avoid Makefile):

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-test.txt
.venv\Scripts\python.exe -m pytest -q tests/unit --cov=. --junitxml=reports/unit.xml
```


