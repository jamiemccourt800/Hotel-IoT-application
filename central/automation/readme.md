# Automation service

## Goal: 
Automate room lights and temperature using simple business rules, expose an HTTP API for health check in container, 
based on data in MongoDB and VictoriaMetrics, and call the Command service to actuate devices.

Actuator commands are sent via the Command service API, which in turn calls the Kafka bridge to publish MQTT messages to hotel brokers.

## Process (high level):
  - Start service entrypoint automation/app.py on 0.0.0.0:5000.
  - Connect to Mongo and VM using env vars.
  - Execute domain logic in automation/lights.py and automation/temperature.py.
  - Send commands to Command service as needed.
  - Expose /health for readiness checks.

## Connects to:
  - mongodb — persistent storage (compose service mongodb, port 27017)
  - command — actuator command service (API port 5000)
  - victoria-metrics — metrics collection (port 8428)

## Environment variables to set:
  - MONGO_HOST
  - MONGO_PORT
  - MONGO_DB
  - MONGO_USER
  - MONGO_PASS
  - COMMAND_SERVICE_URL
  - VICTORIA_METRICS_URL

## How to run:
Docker Compose: docker compose -f central/docker-compose.central.yml up --build automation

### Ports: 
Service listens on 0.0.0.0:5000 (mapped to host 5012 in compose).

### Healthcheck: 
GET /health returns 200; compose can use a healthcheck.
 
### Key files: 
Key files described:
- `automation/app.py` — service entrypoint and HTTP API (starts Flask server on 0.0.0.0:5000), loads env vars, connects to MongoDB, starts scheduled loops for lights and temperature, exposes `/health`.
- `automation/lights.py` — domain logic and scheduler for room lights (business rules, state transitions), reads/writes state to MongoDB and sends actuation commands via the Command service.
- `automation/temperature.py` — domain logic and scheduler for temperature control (thermostat rules, setpoint management), persists readings/state to MongoDB and calls actuators when needed.
- `automation/Dockerfile` — container build instructions (installs dependencies, copies app code, exposes port 5000, sets the container entrypoint).
- `automation/requirements.txt` — Python package dependencies required to run the service (pins versions used in the Docker build).