def test_env_defaults_are_set(integration_settings):
    assert integration_settings["mqtt_host"]
    assert integration_settings["mqtt_port"] > 0
    assert ":" in integration_settings["kafka_bootstrap"]
