"""
Simple verification script for the IoT telemetry pipeline.

Checks performed:
- required docker containers present and running
- mqtt-to-kafka container recently forwarded MQTT messages
- VictoriaMetrics has recent samples for `temperature_temperatureC`
- Grafana has the VictoriaMetrics datasource and the `hotel-iot` dashboard

Usage (from repo root):
  python iot-simulator/verify_pipeline.py

Note: The script uses the local Docker socket and HTTP APIs on localhost:8428 (VictoriaMetrics) and localhost:3000 (Grafana).
"""

import subprocess
import sys
import time
import urllib.request
import urllib.parse
import json

# Config
REQUIRED_CONTAINERS = [
    'devops-group-project-mqtt-to-kafka-1',
    'devops-group-project-victoria-metrics-1',
    'telegraf',
    'grafana',
    'devops-group-project-mosquitto-1'
]
VM_URL = 'http://localhost:8428'
GRAFANA_URL = 'http://localhost:3000'
GRAFANA_USER = 'admin'
GRAFANA_PASS = 'admin'
METRIC_NAME = 'temperature_temperatureC'
DASHBOARD_UID = 'hotel-iot'


def run_cmd(cmd, capture=True, check=False, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=capture, text=True, check=check, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, '', 'timeout'
    except Exception as e:
        return 1, '', str(e)


def check_containers():
    code, out, err = run_cmd(['docker', 'ps', '--format', '{{.Names}}\t{{.Status}}'])
    if code != 0:
        return False, 'docker ps failed: ' + (err or out)
    lines = out.splitlines()
    present = {l.split('\t')[0]: l.split('\t')[1] if '\t' in l else '' for l in lines}
    missing = [c for c in REQUIRED_CONTAINERS if c not in present]
    status_msgs = []
    for c in REQUIRED_CONTAINERS:
        status_msgs.append(f"{c}: {present.get(c,'MISSING')}")
    if missing:
        return False, 'Missing containers: ' + ', '.join(missing) + '\n' + '\n'.join(status_msgs)
    return True, '\n'.join(status_msgs)


def check_mqtt_to_kafka_logs():
    # look for forwarded messages pattern in recent logs
    name = 'devops-group-project-mqtt-to-kafka-1'
    code, out, err = run_cmd(['docker', 'logs', '--tail', '200', name], timeout=5)
    if code != 0:
        return False, f'failed to read logs for {name}: {err or out}'
    if 'Forwarded message to Kafka' in out or 'Forwarded message' in out:
        # return a small snippet
        idx = out.rfind('Forwarded message')
        snippet = out[idx:idx+400] if idx != -1 else out[-400:]
        return True, 'found forwarded messages: ' + snippet
    return False, 'no forwarded message lines found in last 200 log lines'


def check_victoriametrics():
    # instant query for the metric
    try:
        q = urllib.parse.urlencode({'query': METRIC_NAME})
        url = f'{VM_URL}/api/v1/query?{q}'
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.load(r)
        results = data.get('data', {}).get('result', [])
        if not results:
            return False, 'no series found for ' + METRIC_NAME
        # pick most recent point from first series
        vals = results[0].get('value') or results[0].get('values')
        return True, f'found series: {results[0].get("metric")} value: {vals}'
    except Exception as e:
        return False, f'VM query failed: {e}'


def check_grafana():
    # datasources
    try:
        req = urllib.request.Request(f'{GRAFANA_URL}/api/datasources')
        auth = (GRAFANA_USER + ':' + GRAFANA_PASS).encode('utf-8')
        import base64
        basic = base64.b64encode(auth).decode('ascii')
        req.add_header('Authorization', 'Basic ' + basic)
        with urllib.request.urlopen(req, timeout=5) as r:
            ds = json.load(r)
        vm_ds = [d for d in ds if d.get('name') == 'VictoriaMetrics' or d.get('url','').find('victoria-metrics')!=-1]
        if not vm_ds:
            return False, 'VictoriaMetrics datasource not found in Grafana'
        # check dashboard
        req2 = urllib.request.Request(f'{GRAFANA_URL}/api/dashboards/uid/{DASHBOARD_UID}')
        req2.add_header('Authorization', 'Basic ' + basic)
        with urllib.request.urlopen(req2, timeout=5) as r2:
            dash = json.load(r2)
        panels = dash.get('dashboard', {}).get('panels', [])
        # verify panels include our metric name
        found = False
        for p in panels:
            for t in p.get('targets', []):
                expr = t.get('expr') or ''
                if METRIC_NAME in expr:
                    found = True
        if not found:
            return False, f'Dashboard {DASHBOARD_UID} panels do not reference {METRIC_NAME}'
        return True, 'Grafana datasource and dashboard look good'
    except Exception as e:
        return False, f'Grafana check failed: {e}'


def main():
    print('\nVERIFYING IOT TELEMETRY PIPELINE\n')

    ok, msg = check_containers()
    print('1) Containers:', 'OK' if ok else 'FAIL')
    print(msg + '\n')
    if not ok:
        print('Aborting early due to missing containers.')
        sys.exit(2)

    ok, msg = check_mqtt_to_kafka_logs()
    print('2) MQTT -> Kafka forwarding:', 'OK' if ok else 'WARN/FAIL')
    print(msg + '\n')

    ok, msg = check_victoriametrics()
    print('3) VictoriaMetrics series:', 'OK' if ok else 'FAIL')
    print(msg + '\n')

    ok, msg = check_grafana()
    print('4) Grafana datasource/dashboard:', 'OK' if ok else 'FAIL')
    print(msg + '\n')

    # overall status
    failures = []
    for check in ['1','3','4']:
        pass
    print('Done.\n')

if __name__ == '__main__':
    main()
