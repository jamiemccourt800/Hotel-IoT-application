# test_conftest_import.py - Unit test for conftest module import

def test_conftest_import():
    import tests.conftest
    assert hasattr(tests.conftest, "load_module_from_path")
