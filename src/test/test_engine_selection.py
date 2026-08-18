"""Tests for YAML engine selection/autodetection (see issue #338).

`ruamel.yaml` and `yamlrocks` are both optional dependencies - at least one must be installed,
either one suffices, and whichever is installed is picked automatically if not chosen
explicitly (preferring `ruamel`, the historical default, if both are present).

Unlike test_engine_yamlrocks.py, these don't require `yamlrocks` to actually be installed:
only the selection *logic* is exercised here, via a monkeypatched `_module_available`, so this
file runs the same way regardless of which backend(s) happen to be present.
"""

import pytest

from pydantic_yaml._internals import v2


@pytest.fixture(autouse=True)
def _reset_default_engine(monkeypatch):
    """Give every test a fresh, unresolved default-engine cache."""
    monkeypatch.setattr(v2, "_default_engine", None)


def test_validate_engine():
    """Only the two known engine names validate; anything else raises `ValueError`."""
    assert v2._validate_engine("ruamel") == "ruamel"
    assert v2._validate_engine("yamlrocks") == "yamlrocks"
    with pytest.raises(ValueError):
        v2._validate_engine("not-a-real-engine")


def test_autodetect_prefers_ruamel_when_both_available(monkeypatch):
    """`"ruamel"` is preferred (historical default) when both backends are installed."""
    monkeypatch.setattr(v2, "_module_available", lambda name: True)
    assert v2.get_default_engine() == "ruamel"


def test_autodetect_falls_back_to_yamlrocks_only(monkeypatch):
    """`"yamlrocks"` is picked when it's the only backend installed."""
    monkeypatch.setattr(v2, "_module_available", lambda name: name == "yamlrocks")
    assert v2.get_default_engine() == "yamlrocks"


def test_autodetect_uses_ruamel_only(monkeypatch):
    """`"ruamel"` is picked when it's the only backend installed."""
    monkeypatch.setattr(v2, "_module_available", lambda name: name == "ruamel.yaml")
    assert v2.get_default_engine() == "ruamel"


def test_autodetect_raises_when_neither_available(monkeypatch):
    """A clear `ImportError` is raised when neither backend is installed."""
    monkeypatch.setattr(v2, "_module_available", lambda name: False)
    with pytest.raises(ImportError):
        v2.get_default_engine()


def test_default_engine_is_cached(monkeypatch):
    """Autodetection runs once; a later change in availability doesn't retroactively apply."""
    calls: list[str] = []

    def tracked(name: str) -> bool:
        calls.append(name)
        return name == "yamlrocks"

    monkeypatch.setattr(v2, "_module_available", tracked)
    assert v2.get_default_engine() == "yamlrocks"
    n_calls = len(calls)
    assert v2.get_default_engine() == "yamlrocks"
    assert len(calls) == n_calls  # not re-invoked


def test_env_var_overrides_autodetection(monkeypatch):
    """`PYDANTIC_YAML_ENGINE` wins over autodetection when set."""
    monkeypatch.setattr(v2, "_module_available", lambda name: name == "yamlrocks")
    monkeypatch.setenv(v2._ENGINE_ENV_VAR, "ruamel")
    assert v2.get_default_engine() == "ruamel"


def test_env_var_invalid_raises(monkeypatch):
    """An unrecognized `PYDANTIC_YAML_ENGINE` value raises `ValueError`."""
    monkeypatch.setenv(v2._ENGINE_ENV_VAR, "not-a-real-engine")
    with pytest.raises(ValueError):
        v2.get_default_engine()


def test_set_default_engine_requires_module_available(monkeypatch):
    """`set_default_engine` fails fast if the requested backend isn't installed."""
    monkeypatch.setattr(v2, "_module_available", lambda name: name == "ruamel.yaml")
    with pytest.raises(ImportError):
        v2.set_default_engine("yamlrocks")
    v2.set_default_engine("ruamel")
    assert v2.get_default_engine() == "ruamel"


def test_set_default_engine_unknown_raises():
    """An unrecognized engine name raises `ValueError` rather than silently falling back."""
    bad_engine: str = "not-a-real-engine"
    with pytest.raises(ValueError):
        v2.set_default_engine(bad_engine)  # ty: ignore[invalid-argument-type]


def test_engine_kwarg_bypasses_default_resolution(monkeypatch):
    """Passing `engine=` explicitly skips default-engine autodetection entirely."""
    monkeypatch.setattr(v2, "_module_available", lambda name: False)  # neither "available"
    assert v2._resolve_engine("ruamel") == "ruamel"
    assert v2._resolve_engine("yamlrocks") == "yamlrocks"
    with pytest.raises(ValueError):
        v2._resolve_engine("not-a-real-engine")  # ty: ignore[invalid-argument-type]
