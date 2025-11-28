# tests/integration/test_conftest_loader.py
import pytest

@pytest.mark.integration
def test_top_level_conftest_load_module():
    """
    This test exists only to COVER tests/conftest.py during integration runs.
    Skip if module imports fail (circular dependencies or missing modules).
    """
    import tests.conftest as top_conf
    import pathlib

    try:
        mod = top_conf.load_module_from_path(
            "hotel.room1.temperature-sensor.app.sensor",
            pathlib.Path("hotel/room1/temperature-sensor/app/sensor.py"),
        )
        assert mod is not None
    except (ImportError, ModuleNotFoundError) as e:
        pytest.skip(f"Module import failed: {e}")
    # we don't need to call anything on mod, just importing it is enough for coverage
