# tests/integration/test_conftest_loader.py

def test_top_level_conftest_load_module():
    """
    This test exists only to COVER tests/conftest.py during integration runs.
    It should call load_module(...) on a real file in the repo.
    """
    import tests.conftest as top_conf
    import pathlib

    mod = top_conf.load_module_from_path(
        "hotel.room1.temperature-sensor.logic.main",
        pathlib.Path("hotel/room1/temperature-sensor/logic/main.py"),
    )

    assert mod is not None
    # we don't need to call anything on mod, just importing it is enough for coverage
