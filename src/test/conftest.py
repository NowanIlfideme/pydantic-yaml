"""Shared pytest fixtures for the test suite."""

import pytest

from pydantic_yaml import RuamelEngine, YamlRocksEngine


@pytest.fixture(params=[YamlRocksEngine, RuamelEngine])
def engine(request: pytest.FixtureRequest) -> RuamelEngine | YamlRocksEngine:
    """Parametrize a test over both built-in YAML engines, skipping whichever isn't installed.

    Preferring `YamlRocksEngine` first (see issue #338) just orders test output; both engines
    are exercised either way as long as both are installed, which they are in the dev
    environment. Construction itself is the availability check - `YamlRocksEngine()`/
    `RuamelEngine()` raise `ImportError` if their backend isn't installed.
    """
    cls = request.param
    try:
        return cls()
    except ImportError:
        pytest.skip(f"{cls.__name__} backend is not installed")
