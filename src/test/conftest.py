"""Shared pytest fixtures for the test suite."""

from typing import NamedTuple, TypeVar

import pytest

from pydantic_yaml import RuamelReader, RuamelWriter, YamlRocksReader, YamlRocksWriter

_READERS = {"yamlrocks": YamlRocksReader, "ruamel": RuamelReader}
_WRITERS = {"yamlrocks": YamlRocksWriter, "ruamel": RuamelWriter}

T = TypeVar("T")


class Backend(NamedTuple):
    """A matched reader/writer pair backed by the same YAML library."""

    reader: RuamelReader | YamlRocksReader
    writer: RuamelWriter | YamlRocksWriter


def _construct(cls: type[T], name: str) -> T:
    try:
        return cls()
    except ImportError:
        pytest.skip(f"{name!r} backend is not installed")


@pytest.fixture(params=["yamlrocks", "ruamel"])
def reader(request: pytest.FixtureRequest) -> RuamelReader | YamlRocksReader:
    """Parametrize a test over both built-in readers, skipping whichever isn't installed.

    Preferring `yamlrocks` first (see issue #338) just orders test output; both backends are
    exercised either way as long as both are installed, which they are in the dev environment.
    """
    name = request.param
    return _construct(_READERS[name], name)


@pytest.fixture(params=["yamlrocks", "ruamel"])
def writer(request: pytest.FixtureRequest) -> RuamelWriter | YamlRocksWriter:
    """Parametrize a test over both built-in writers, skipping whichever isn't installed."""
    name = request.param
    return _construct(_WRITERS[name], name)


@pytest.fixture(params=["yamlrocks", "ruamel"])
def backend(request: pytest.FixtureRequest) -> Backend:
    """Parametrize a test over both built-in YAML backends, as a matched reader/writer pair.

    Use this (rather than the standalone `reader`/`writer` fixtures) whenever a test needs both
    directions from the *same* library, e.g. a round-trip test.
    """
    name = request.param
    return Backend(reader=_construct(_READERS[name], name), writer=_construct(_WRITERS[name], name))
