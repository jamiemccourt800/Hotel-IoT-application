# Multi-site IoT Demo (Central + Hotels)
This project implements a distributed IoT monitoring system for hotel rooms with a microservices architecture split across multiple Docker Compose files:

This splits the stack into three compose files:

- `docker-compose.central.yml` — Central HQ: Kafka, VictoriaMetrics, Telegraf, Grafana
- `docker-compose.hotel1.yml` — Hotel Alpha: local Mosquitto, Simulator (room 101), Node-RED, MQTT→Kafka bridge

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

## Testing

Preferred: use the Makefile (reads cross-platform Python, creates venv, and produces reports under reports/).

Make targets (run e.g. `make unit`):

- `make init` — create virtualenv and install test deps (runs VENV_CREATE and installs requirements-test.txt).
- `make unit` — run unit tests (tests/unit). Produces `reports/unit.xml`, `reports/coverage.xml` and HTML coverage at `reports/htmlcov/`.
- `make contract` — run contract tests. Produces `reports/contract.xml`.
- `make integration` — run integration tests (requires Docker services). Produces `reports/integration.xml`.
- `make e2e` — run end-to-end tests. Produces `reports/e2e.xml`.
- `make frontend-test` — run frontend (React/Jest) tests in central/app/frontend (requires Node/npm in PATH).
- `make frontend-test-coverage` — run frontend tests with coverage (lcov + text).
- `make all-tests` — run unit, contract and integration tests together; produces `reports/all.xml` and coverage XML.
- `make all-tests-coverage-html` — same as above and generates HTML coverage (`reports/htmlcov/`) and attempts to open it in a browser.
- `make all-tests-with-frontend` — run Python tests then frontend tests.

Notes:
- If the venv python is missing, the Makefile falls back to the system `python`.
- Frontend dir used by the Makefile is `central/app/frontend` (Windows paths handled automatically).
- Inspect the Makefile for exact commands and output locations; run the equivalent `python -m pytest ...` commands from the Makefile if you cannot use `make`.
- Test artifacts and coverage HTML live under `reports/` (XML junit/coverage and `htmlcov/`).
- Integration tests require the central and hotel compose stacks to be up (see Run section).
- For CI parity and consistent reporting prefer the Makefile targets.

- Integration tests require the central and hotel compose stacks to be up
- Test reports and coverage HTML are stored under reports/ (unit/integration XML and coverage_html/).
- Prefer the Makefile targets for consistent environment and reporting.