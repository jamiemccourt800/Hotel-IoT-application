# Hotel IoT Simulator — Modular (MQTT, LWT, Backoff, CSV pacing)

## Features added
- **MQTT LWT**: broker will publish a `sensor_offline` alert if the client dies unexpectedly.
- **Auto-reconnect with exponential backoff** and a small **publish buffer**.
- **Config via env/flags**: `QOS`, `RETAIN`, `KEEPALIVE` (plus IDs/broker).
- **CSV pacing**: `--pace-real` to replay timestamp deltas; `--speed` to fast-forward (e.g., 2.0 = twice as fast).
- **Graceful shutdown**: flush buffered messages before disconnect.

## Layout
```
IoT Simulator
=============

Overview
--------
This folder contains a lightweight IoT simulator and a verification script that confirms the full telemetry pipeline used in this project.

Pipeline validated by the script:

Simulator -> MQTT broker (mosquitto) -> mqtt-to-kafka bridge -> Kafka -> Telegraf (Kafka consumer) -> VictoriaMetrics -> Grafana

Files
-----
- `app/` — simulator application code (publishes MQTT telemetry messages)
- `core/` — simulator core logic and message definitions
- `mqtt/` — mqtt helpers
- `services/` — supporting services used by the simulator
- `verify_pipeline.py` — verification script that checks containers, logs, VictoriaMetrics, and Grafana
- `requirements.txt` — Python requirements for the simulator apps (note: `verify_pipeline.py` uses only the Python standard library)

Requirements
------------
- Docker & Docker Compose (to run the full stack)
- Python 3.8+ for running simulator scripts locally
- On Windows, PowerShell is used in examples below (commands are PowerShell-friendly)

Run the simulator locally (development)
--------------------------------------
1. Create and activate a virtual environment (PowerShell):

```powershell
cd iot-simulator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

2. Run the simulator (example):

```powershell
# From repo root
set PYTHONPATH=%CD%; python -u iot-simulator\app\main.py --mode random --interval 0.5 --broker host.docker.internal --port 1883 --hotel-id hotel_01 --room 101 --sensor sensor-iot --qos 0
```

Verify the end-to-end pipeline
------------------------------
`iot-simulator/verify_pipeline.py` verifies telemetry flows from the simulator through the whole stack by checking:
- Required Docker containers are running
- `mqtt-to-kafka` container logs show messages forwarded from MQTT to Kafka
- VictoriaMetrics contains a recent value for `temperature_temperatureC`
- Grafana has the `VictoriaMetrics` datasource and the `hotel-iot` dashboard panels reference the metric

The script is standalone and uses only the Python standard library.

Run the verification script (from repo root):

```powershell
python iot-simulator\verify_pipeline.py
```

Expected output (summary):
- Containers: OK
- MQTT -> Kafka forwarding: OK (log snippet)
- VictoriaMetrics series: OK (shows metric & recent value)
- Grafana datasource/dashboard: OK