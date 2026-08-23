"""Tests for YAML reader/writer selection & autodetection (see issue #338).

`RuamelReader`/`RuamelWriter` and `YamlRocksReader`/`YamlRocksWriter` are all backed by optional
dependencies - at least one backend must be installed, either one suffices, and whichever is
installed is picked automatically if not chosen explicitly (preferring `yamlrocks` if both are
present). There's no string-based selection: `reader=`/`writer=` and the defaults always resolve
to an actual object.

Most of these don't require either backend to actually be installed: the autodetection *logic*
is exercised via fake stand-in classes monkeypatched into `pydantic_yaml.engines`, so those run
the same way regardless of which backend(s) happen to be present.
`test_set_default_*_changes_runtime_behavior` are the exception - real (non-mocked) integration
checks, using the shared `reader`/`writer` fixtures.
"""

from io import IOBase
from typing import Any

import pytest
from pydantic import BaseModel

from pydantic_yaml import (
    YamlReader,
    YamlWriter,
    get_default_reader,
    get_default_writer,
    parse_yaml_raw_as,
    set_default_reader,
    set_default_writer,
    to_yaml_str,
)
from pydantic_yaml import engines as engines_module
from pydantic_yaml.examples.base_models import A


class _FakeYamlRocksReader:
    """Stand-in for `YamlRocksReader` that always "succeeds" (backend "installed")."""

    def read(self, stream: IOBase) -> Any: ...


class _FakeRuamelReader:
    """Stand-in for `RuamelReader` that always "succeeds" (backend "installed")."""

    def read(self, stream: IOBase) -> Any: ...


class _FakeYamlRocksWriter:
    """Stand-in for `YamlRocksWriter` that always "succeeds" (backend "installed")."""

    def write(self, stream: IOBase, model: BaseModel) -> None: ...


class _FakeRuamelWriter:
    """Stand-in for `RuamelWriter` that always "succeeds" (backend "installed")."""

    def write(self, stream: IOBase, model: BaseModel) -> None: ...


class _FakeMissing:
    """Stand-in for a reader/writer whose backend isn't installed - always fails to construct."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise ImportError("simulated missing backend")


@pytest.fixture(autouse=True)
def _reset_defaults(monkeypatch):
    """Give every test a fresh, unresolved default reader/writer cache."""
    monkeypatch.setattr(engines_module, "_default_reader", None)
    monkeypatch.setattr(engines_module, "_default_writer", None)


def test_autodetect_reader_prefers_yamlrocks_when_both_available(monkeypatch):
    """`YamlRocksReader` is preferred when both backends are "installed"."""
    monkeypatch.setattr(engines_module, "YamlRocksReader", _FakeYamlRocksReader)
    monkeypatch.setattr(engines_module, "RuamelReader", _FakeRuamelReader)
    assert isinstance(get_default_reader(), _FakeYamlRocksReader)


def test_autodetect_reader_falls_back_to_ruamel_only(monkeypatch):
    """`RuamelReader` is picked when it's the only backend "installed"."""
    monkeypatch.setattr(engines_module, "YamlRocksReader", _FakeMissing)
    monkeypatch.setattr(engines_module, "RuamelReader", _FakeRuamelReader)
    assert isinstance(get_default_reader(), _FakeRuamelReader)


def test_autodetect_reader_raises_when_neither_available(monkeypatch):
    """A clear `ImportError` is raised when neither backend is "installed"."""
    monkeypatch.setattr(engines_module, "YamlRocksReader", _FakeMissing)
    monkeypatch.setattr(engines_module, "RuamelReader", _FakeMissing)
    with pytest.raises(ImportError):
        get_default_reader()


def test_autodetect_writer_prefers_yamlrocks_when_both_available(monkeypatch):
    """`YamlRocksWriter` is preferred when both backends are "installed"."""
    monkeypatch.setattr(engines_module, "YamlRocksWriter", _FakeYamlRocksWriter)
    monkeypatch.setattr(engines_module, "RuamelWriter", _FakeRuamelWriter)
    assert isinstance(get_default_writer(), _FakeYamlRocksWriter)


def test_autodetect_writer_falls_back_to_ruamel_only(monkeypatch):
    """`RuamelWriter` is picked when it's the only backend "installed"."""
    monkeypatch.setattr(engines_module, "YamlRocksWriter", _FakeMissing)
    monkeypatch.setattr(engines_module, "RuamelWriter", _FakeRuamelWriter)
    assert isinstance(get_default_writer(), _FakeRuamelWriter)


def test_autodetect_writer_raises_when_neither_available(monkeypatch):
    """A clear `ImportError` is raised when neither backend is "installed"."""
    monkeypatch.setattr(engines_module, "YamlRocksWriter", _FakeMissing)
    monkeypatch.setattr(engines_module, "RuamelWriter", _FakeMissing)
    with pytest.raises(ImportError):
        get_default_writer()


def test_default_reader_is_cached(monkeypatch):
    """Autodetection runs once; a later change in availability doesn't retroactively apply."""
    calls: list[str] = []

    class _TrackedMissing(_FakeMissing):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            calls.append("yamlrocks")
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(engines_module, "YamlRocksReader", _TrackedMissing)
    monkeypatch.setattr(engines_module, "RuamelReader", _FakeRuamelReader)
    first = get_default_reader()
    n_calls = len(calls)
    second = get_default_reader()
    assert first is second
    assert len(calls) == n_calls  # not re-invoked


def test_set_default_reader_accepts_any_conforming_object():
    """`set_default_reader` accepts anything with a `read` method, not just built-ins."""
    fake = _FakeRuamelReader()
    set_default_reader(fake)
    assert get_default_reader() is fake


def test_set_default_writer_accepts_any_conforming_object():
    """`set_default_writer` accepts anything with a `write` method, not just built-ins."""
    fake = _FakeRuamelWriter()
    set_default_writer(fake)
    assert get_default_writer() is fake


def test_set_default_reader_rejects_non_conforming_object():
    """An object without a `read` method is rejected with a clear `TypeError`."""
    with pytest.raises(TypeError):
        set_default_reader("not-a-reader")  # ty: ignore[invalid-argument-type]
    with pytest.raises(TypeError):
        set_default_reader(object())  # ty: ignore[invalid-argument-type]


def test_set_default_writer_rejects_non_conforming_object():
    """An object without a `write` method is rejected with a clear `TypeError`."""
    with pytest.raises(TypeError):
        set_default_writer("not-a-writer")  # ty: ignore[invalid-argument-type]
    with pytest.raises(TypeError):
        set_default_writer(object())  # ty: ignore[invalid-argument-type]


def test_set_default_reader_changes_runtime_behavior(reader: YamlReader):
    """`set_default_reader` (real, not mocked) actually changes what `reader=None` calls do."""
    original = get_default_reader()
    try:
        set_default_reader(reader)
        assert get_default_reader() is reader
        # No reader passed -> uses the new default.
        yml = to_yaml_str(A(a="a"))
        assert parse_yaml_raw_as(A, yml) == parse_yaml_raw_as(A, yml, reader=reader)
    finally:
        set_default_reader(original)


def test_set_default_writer_changes_runtime_behavior(writer: YamlWriter):
    """`set_default_writer` (real, not mocked) actually changes what `writer=None` calls do."""
    original = get_default_writer()
    try:
        set_default_writer(writer)
        assert get_default_writer() is writer
        # No writer passed -> uses the new default.
        assert to_yaml_str(A(a="a")) == to_yaml_str(A(a="a"), writer=writer)
    finally:
        set_default_writer(original)
