import pathlib

def test_load_module_imports_alert_agent(load_module):
    mod = load_module("hotel.room1.alert-agent.app.main")
    assert hasattr(mod, "on_message")

def test_load_module_with_invalid_name(load_module):
    import pytest
    with pytest.raises(ImportError):
        load_module("not.a.real.module")

def test_load_module_with_non_string_argument(load_module):
    import pytest
    with pytest.raises(Exception):
        load_module(12345)

def test_loaded_modules_use_correct_env_var_names(load_module):
    """Verify that modules loaded for contract tests use project environment variable names."""
    # Alert agent
    alert_mod = load_module("hotel.room1.alert-agent.app.main")
    assert hasattr(alert_mod, 'BROKER')  # MQTT_BROKER
    assert hasattr(alert_mod, 'PORT')    # MQTT_PORT
    assert hasattr(alert_mod, 'HOTEL')   # HOTEL_ID
    assert hasattr(alert_mod, 'ROOM')    # ROOM
    
    # Light actuator
    light_mod = load_module("hotel.room1.light-actuator.logic.main")
    assert hasattr(light_mod, 'HOTEL_ID')
    assert hasattr(light_mod, 'ROOM')
    assert hasattr(light_mod, 'SENSOR')
    assert hasattr(light_mod, 'BROKER')
    assert hasattr(light_mod, 'BROKER_PORT')
    
    # Temperature sensor
    sensor_mod = load_module("hotel.room1.temperature-sensor.logic.main")
    assert hasattr(sensor_mod, 'build_payload')
    # Verify function signature matches expected parameter names
    import inspect
    sig = inspect.signature(sensor_mod.build_payload)
    params = list(sig.parameters.keys())
    assert 'hotel_id' in params
    assert 'room' in params
    assert 'sensor' in params
    assert 'temp_c' in params

def test_contract_tests_work_with_production_env_values(load_module, monkeypatch):
    """Verify contract tests work when environment variables match docker-compose production values."""
    # Set production environment variables
    monkeypatch.setenv("MQTT_BROKER", "mosquitto")
    monkeypatch.setenv("MQTT_PORT", "1883")
    monkeypatch.setenv("HOTEL_ID", "hotel_01")
    monkeypatch.setenv("ROOM", "101")
    monkeypatch.setenv("SENSOR", "temperature-sensor")
    monkeypatch.setenv("BROKER", "mosquitto")
    monkeypatch.setenv("BROKER_PORT", "1883")
    monkeypatch.setenv("TEMP_HIGH_C", "30")
    
    # Reload modules with production env vars
    alert_mod = load_module("hotel.room1.alert-agent.app.main")
    light_mod = load_module("hotel.room1.light-actuator.logic.main")
    sensor_mod = load_module("hotel.room1.temperature-sensor.logic.main")
    
    # Verify they loaded successfully and have expected attributes
    assert hasattr(alert_mod, 'on_message')
    assert hasattr(light_mod, 'on_message')
    assert hasattr(sensor_mod, 'build_payload')
    
    # Verify production values are used
    assert alert_mod.BROKER == "mosquitto"
    assert alert_mod.PORT == 1883
    assert alert_mod.HOTEL == "hotel_01"
    assert alert_mod.ROOM == "101"
    assert light_mod.HOTEL_ID == "hotel_01"
    assert light_mod.BROKER == "mosquitto"
