import pytest
import os
import sys
from importlib import reload
from pathlib import Path

# Ensure tests.integration is importable
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import tests.integration.test_mqtt_to_kafka_bridge as bridge_test

@pytest.mark.integration
@pytest.mark.timeout(15)
def test_integration_skips_cleanly_when_kafka_is_down(monkeypatch, request):
    """
    Cover the branch where kafka is unreachable by pointing to a fake host.
    """
    # Patch the env var first, then obtain the fixture so it reads the patched env.
    monkeypatch.setenv("TEST_KAFKA_BOOTSTRAP", "does-not-exist:9999")
    reload(bridge_test)

    # Request the fixture after monkeypatching so it picks up the changed environment
    integration_settings = request.getfixturevalue("integration_settings")

    with pytest.raises(pytest.skip.Exception):
        bridge_test.test_mqtt_message_is_forwarded_to_kafka(integration_settings)
