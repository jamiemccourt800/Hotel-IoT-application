import pytest
import importlib.util
import pathlib
import os

# Dynamically load config.py
spec = importlib.util.spec_from_file_location("config", pathlib.Path("central/command/config.py"))
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

def test_config_class_exists():
    assert hasattr(config, 'Config')
    assert hasattr(config, 'config')

def test_config_attributes():
    cfg = config.config
    assert hasattr(cfg, 'KAFKA_BOOTSTRAP')
    assert hasattr(cfg, 'KAFKA_TOPIC')
    assert hasattr(cfg, 'CLIENT_ID')
    assert hasattr(cfg, 'ACKS')
    assert hasattr(cfg, 'RETRIES')
    assert hasattr(cfg, 'LINGER_MS')

def test_config_defaults():
    """Test that config has sensible defaults."""
    cfg = config.config
    assert isinstance(cfg.KAFKA_BOOTSTRAP, str)
    assert isinstance(cfg.KAFKA_TOPIC, str)
    assert isinstance(cfg.CLIENT_ID, str)
    assert isinstance(cfg.ACKS, str)
    assert isinstance(cfg.RETRIES, int)
    assert isinstance(cfg.LINGER_MS, int)

def test_config_production_values():
    """Test that defaults match production docker-compose values where applicable."""
    # Note: Production uses "kafka:9092" but defaults to "localhost:9092" for local dev
    # This is correct - the environment variable overrides the default in production
    cfg = config.config
    
    # These should match the defaults in config.py
    # In production, docker-compose.central.yml overrides these via environment variables
    assert cfg.CLIENT_ID == "fastapi-producer"  # Matches docker-compose
    assert cfg.ACKS == "all"  # Matches docker-compose
    assert cfg.LINGER_MS == 5  # Matches docker-compose
    
    # These have different defaults for local vs production (via env vars)
    # Default in code is for local development
    assert cfg.KAFKA_BOOTSTRAP == "localhost:9092"  # Local default
    assert cfg.KAFKA_TOPIC == "test-topic"  # Local default (prod uses "actuator")
    assert cfg.RETRIES == 3  # Local default (prod uses 10)

def test_config_with_env_vars(monkeypatch):
    """Test that config reads from environment variables."""
    monkeypatch.setenv("KAFKA_BOOTSTRAP", "test-kafka:9092")
    monkeypatch.setenv("KAFKA_TOPIC", "test-topic")
    monkeypatch.setenv("CLIENT_ID", "test-client")
    monkeypatch.setenv("ACKS", "1")
    monkeypatch.setenv("RETRIES", "5")
    monkeypatch.setenv("LINGER_MS", "10")
    
    # Reload the config module
    spec = importlib.util.spec_from_file_location("config_test", pathlib.Path("central/command/config.py"))
    config_test = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_test)
    
    assert config_test.config.KAFKA_BOOTSTRAP == "test-kafka:9092"
    assert config_test.config.KAFKA_TOPIC == "test-topic"
    assert config_test.config.CLIENT_ID == "test-client"
    assert config_test.config.ACKS == "1"
    assert config_test.config.RETRIES == 5
    assert config_test.config.LINGER_MS == 10
