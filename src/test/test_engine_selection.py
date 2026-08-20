"""Tests for YAML engine selection/autodetection (see issue #338).

`RuamelEngine`/`YamlRocksEngine` are both optional-dependency-backed - at least one must be
installed, either one suffices, and whichever is installed is picked automatically if not
chosen explicitly (preferring `YamlRocksEngine` if both are present). There's no more
string-based engine selection: `engine=` and the default always resolve to an actual object.

Most of these don't require either backend to actually be installed: the autodetection *logic*
is exercised via fake stand-in engine classes monkeypatched into `pydantic_yaml.engines`, so
those run the same way regardless of which backend(s) happen to be present.
`test_set_default_engine_changes_runtime_behavior` is the exception - it's a real (non-mocked)
integration check, using the shared `engine` fixture.
"""

from io import IOBase
from typing import Any

import pytest
from pydantic import BaseModel

from pydantic_yaml import YamlEngine, get_default_engine, set_default_engine, to_yaml_str
from pydantic_yaml import engines as engines_module
from pydantic_yaml.examples.base_models import A


class _FakeYamlRocks:
    """Stand-in for `YamlRocksEngine` that always "succeeds" (backend "installed")."""

    def read(self, stream: IOBase) -> Any: ...
    def write(self, stream: IOBase, model: BaseModel) -> None: ...


class _FakeRuamel:
    """Stand-in for `RuamelEngine` that always "succeeds" (backend "installed")."""

    def read(self, stream: IOBase) -> Any: ...
    def write(self, stream: IOBase, model: BaseModel) -> None: ...


class _FakeMissing:
    """Stand-in for an engine whose backend isn't installed - always fails to construct."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise ImportError("simulated missing backend")


@pytest.fixture(autouse=True)
def _reset_default_engine(monkeypatch):
    """Give every test a fresh, unresolved default-engine cache."""
    monkeypatch.setattr(engines_module, "_default_engine", None)


def test_autodetect_prefers_yamlrocks_when_both_available(monkeypatch):
    """`YamlRocksEngine` is preferred when both backends are "installed"."""
    monkeypatch.setattr(engines_module, "YamlRocksEngine", _FakeYamlRocks)
    monkeypatch.setattr(engines_module, "RuamelEngine", _FakeRuamel)
    assert isinstance(engines_module._autodetect_engine(), _FakeYamlRocks)


def test_autodetect_falls_back_to_ruamel_only(monkeypatch):
    """`RuamelEngine` is picked when it's the only backend "installed"."""
    monkeypatch.setattr(engines_module, "YamlRocksEngine", _FakeMissing)
    monkeypatch.setattr(engines_module, "RuamelEngine", _FakeRuamel)
    assert isinstance(engines_module._autodetect_engine(), _FakeRuamel)


def test_autodetect_uses_yamlrocks_only(monkeypatch):
    """`YamlRocksEngine` is picked when it's the only backend "installed"."""
    monkeypatch.setattr(engines_module, "YamlRocksEngine", _FakeYamlRocks)
    monkeypatch.setattr(engines_module, "RuamelEngine", _FakeMissing)
    assert isinstance(engines_module._autodetect_engine(), _FakeYamlRocks)


def test_autodetect_raises_when_neither_available(monkeypatch):
    """A clear `ImportError` is raised when neither backend is "installed"."""
    monkeypatch.setattr(engines_module, "YamlRocksEngine", _FakeMissing)
    monkeypatch.setattr(engines_module, "RuamelEngine", _FakeMissing)
    with pytest.raises(ImportError):
        engines_module._autodetect_engine()


def test_default_engine_is_cached(monkeypatch):
    """Autodetection runs once; a later change in availability doesn't retroactively apply."""
    calls: list[str] = []

    class _TrackedYamlRocks(_FakeMissing):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            calls.append("yamlrocks")
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(engines_module, "YamlRocksEngine", _TrackedYamlRocks)
    monkeypatch.setattr(engines_module, "RuamelEngine", _FakeRuamel)
    first = get_default_engine()
    n_calls = len(calls)
    second = get_default_engine()
    assert first is second
    assert len(calls) == n_calls  # not re-invoked


def test_set_default_engine_accepts_any_conforming_object():
    """`set_default_engine` accepts anything with `read`/`write` methods, not just built-ins."""
    fake = _FakeRuamel()
    set_default_engine(fake)
    assert get_default_engine() is fake


def test_set_default_engine_rejects_non_conforming_object():
    """An object without `read`/`write` methods is rejected with a clear `TypeError`."""
    with pytest.raises(TypeError):
        set_default_engine("not-an-engine")  # ty: ignore[invalid-argument-type]
    with pytest.raises(TypeError):
        set_default_engine(object())  # ty: ignore[invalid-argument-type]


def test_set_default_engine_changes_runtime_behavior(engine: YamlEngine):
    """`set_default_engine` (real, not mocked) actually changes what `engine=None` calls do."""
    original = get_default_engine()
    try:
        set_default_engine(engine)
        assert get_default_engine() is engine
        # No engine passed -> uses the new default.
        assert to_yaml_str(A(a="a")) == to_yaml_str(A(a="a"), engine=engine)
    finally:
        set_default_engine(original)
