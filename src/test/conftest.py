"""Shared pytest fixtures for the test suite."""

import importlib.util

import pytest

from pydantic_yaml import EngineName

_ENGINE_MODULES: dict[EngineName, str] = {"yamlrocks": "yamlrocks", "ruamel": "ruamel.yaml"}


def _engine_available(name: EngineName) -> bool:
    try:
        return importlib.util.find_spec(_ENGINE_MODULES[name]) is not None
    except ImportError:
        return False


@pytest.fixture(params=["yamlrocks", "ruamel"])
def engine(request: pytest.FixtureRequest) -> EngineName:
    """Parametrize a test over both YAML engines, skipping whichever isn't installed.

    Preferring `yamlrocks` first (see issue #338) just orders test output; both engines are
    exercised either way as long as both are installed, which they are in the dev environment.
    """
    name: EngineName = request.param
    if not _engine_available(name):
        pytest.skip(f"{name!r} engine is not installed")
    return name
