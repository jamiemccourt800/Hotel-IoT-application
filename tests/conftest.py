import importlib
import pytest

@pytest.fixture
def load_module():
    def _load(name):
        return importlib.import_module(name)
    return _load
# conftest.py - pytest configuration and utilities

import sys, pathlib, importlib.util

# Add repo root to sys.path for absolute imports
ROOT = pathlib.Path(__file__).resolve().parents[1]

# allow absolute imports from repo root
sys.path.append(str(ROOT))  

def load_module_from_path(mod_name: str, file_path: pathlib.Path):
    """
    Load a module from a given file path.
    
    Args:
        mod_name (str): Name to assign to the loaded module.
        file_path (pathlib.Path): Path to the module file.
    Returns:
        module: The loaded module object.
    """
    spec = importlib.util.spec_from_file_location(mod_name, str(file_path))
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod
