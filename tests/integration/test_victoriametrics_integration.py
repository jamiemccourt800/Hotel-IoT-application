import requests
import time
import pytest

def check_victoria_metrics_available(base_url):
    """Check if VictoriaMetrics is available."""
    try:
        resp = requests.get(f"{base_url}/health", timeout=2)
        return resp.status_code == 200
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False

@pytest.mark.integration
def test_write_and_query_metric(integration_settings):
    # Get VictoriaMetrics URL from integration settings
    victoria_metrics_url = integration_settings["victoria_metrics_url"]
    write_url = f"{victoria_metrics_url}/api/v1/import/prometheus"
    query_url = f"{victoria_metrics_url}/api/v1/query"
    
    # Skip if VictoriaMetrics is not available
    if not check_victoria_metrics_available(victoria_metrics_url):
        pytest.skip(f"VictoriaMetrics is not available at {victoria_metrics_url}")
    
    # Write a test metric
    metric_name = "test_metric_victoria"
    value = 42
    ts = int(time.time())
    prometheus_line = f"{metric_name}{{job=\"test\"}} {value} {ts}"
    resp = requests.post(write_url, data=prometheus_line)
    assert resp.status_code == 204, f"Write failed: {resp.text}"

    # Wait for metric to be ingested
    time.sleep(2)

    # Query the metric
    query = f"{metric_name}"
    params = {"query": query}
    resp = requests.get(query_url, params=params)
    assert resp.status_code == 200, f"Query failed: {resp.text}"
    data = resp.json()
    assert data["status"] == "success", f"Query status not success: {data}"
    
    # Check if we got results
    results = data.get("data", {}).get("result", [])
    assert len(results) > 0, f"No results found for metric {metric_name}. Response: {data}"
    
    # Verify the metric value - VictoriaMetrics returns value as [timestamp, value_string]
    found = False
    for result in results:
        metric_labels = result.get("metric", {})
        value_data = result.get("value", [])
        if len(value_data) >= 2:
            returned_value = float(value_data[1])
            if metric_labels.get("job") == "test" and returned_value == value:
                found = True
                break
    
    assert found, f"Metric {metric_name} with value {value} not found. Results: {results}"

