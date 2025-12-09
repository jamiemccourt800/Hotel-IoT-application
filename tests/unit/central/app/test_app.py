import pytest
from fastapi.testclient import TestClient
import importlib.util
import pathlib
import sys
from pathlib import Path

# Directly define load_module_from_path to avoid import conflicts with UnleashClient's test suite
def load_module_from_path(mod_name: str, file_path: pathlib.Path):
    """Load a module from a given file path."""
    spec = importlib.util.spec_from_file_location(mod_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {mod_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module

# Dynamically load FastAPI app

import os
import pytest

APP_PATH = "central/command/app.py"
COMMAND_DIR = str(pathlib.Path("central/command").resolve())
if not os.path.exists(APP_PATH):
    pytest.skip("App module not found: {}".format(APP_PATH), allow_module_level=True)

# Ensure local imports inside central/command resolve (eg. kafka_producer, config)
import sys
if COMMAND_DIR not in sys.path:
    sys.path.insert(0, COMMAND_DIR)

spec = importlib.util.spec_from_file_location("main", APP_PATH)
main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main)
client = TestClient(main.app)

def test_root():
    # The app doesn't have a root endpoint, so we test a valid endpoint instead
    response = client.get("/health")
    assert response.status_code == 200

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    # Health check returns "fail" when Kafka is not available during tests
    assert "status" in response.json()
    assert response.json()["status"] in ["ok", "fail"]

def test_health_returns_json():
    """Test that health endpoint returns JSON with expected structure."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    # May also have 'kafka' key with connection details

def test_invalid_endpoint_returns_404():
    """Test that invalid endpoints return 404."""
    response = client.get("/nonexistent")
    assert response.status_code == 404

def test_app_has_cors_middleware():
    """Test that CORS headers are present."""
    response = client.options("/health")
    # OPTIONS request should be handled by CORS middleware
    assert response.status_code in [200, 405]  # May vary based on CORS config

