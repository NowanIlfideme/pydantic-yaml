"""Pluggable YAML engine interface and built-in implementations.

Any object implementing `read`/`write` (matching the `YamlEngine` protocol) can be passed as
`engine=` to `to_yaml_str`/`to_yaml_file`/`parse_yaml_raw_as`/`parse_yaml_file_as` - no
inheritance required. `RuamelEngine` and `YamlRocksEngine` are the two built-in implementations;
write your own to bring a different YAML library, or to serialize by hand (bypassing this
project's default JSON round-trip approach) for full control.
"""

from __future__ import annotations

from io import IOBase
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel

from pydantic_yaml.engines._ruamel import RuamelEngine
from pydantic_yaml.engines._yamlrocks import YamlRocksEngine

__all__ = [
    "YamlEngine",
    "RuamelEngine",
    "YamlRocksEngine",
    "get_default_engine",
    "set_default_engine",
]


@runtime_checkable
class YamlEngine(Protocol):
    """Structural interface a YAML engine must satisfy to plug into pydantic-yaml.

    Any object with these two methods works - no inheritance required. Engines carry their own
    configuration (comment behavior, formatting, JSON-dump kwargs); `read`/`write` take only the
    stream and, for writing, the model.
    """

    def read(self, stream: IOBase) -> Any:
        """Read a YAML stream into plain Python objects, for TypeAdapter validation."""
        ...

    def write(self, stream: IOBase, model: BaseModel) -> None:
        """Write `model` as YAML to `stream`, using this engine's own configuration."""
        ...


# Resolved lazily (on first use) rather than at import time, so `import pydantic_yaml` never
# fails just because engine autodetection hasn't happened yet.
_default_engine: YamlEngine | None = None


def _autodetect_engine() -> YamlEngine:
    for cls in (YamlRocksEngine, RuamelEngine):  # preference order: yamlrocks first
        try:
            return cls()
        except ImportError:
            continue
    raise ImportError(
        "pydantic-yaml requires at least one YAML backend to be installed. Install one with "
        "`pip install pydantic-yaml[yamlrocks]` or `pip install pydantic-yaml[ruamel]`."
    )


def get_default_engine() -> YamlEngine:
    """Get the default YAML engine used when `engine=None` is passed to the public functions.

    Resolved once (and cached) on first use: whichever of `YamlRocksEngine`/`RuamelEngine` is
    installed (preferring `YamlRocksEngine` if both are), constructed with default
    configuration. Raises `ImportError` if neither backend is installed. Override with
    `set_default_engine()`.
    """
    global _default_engine
    if _default_engine is None:
        _default_engine = _autodetect_engine()
    return _default_engine


def set_default_engine(engine: YamlEngine) -> None:
    """Set the default YAML engine used when `engine=None` is passed to the public functions.

    Parameters
    ----------
    engine : YamlEngine
        A pre-constructed (and, for the built-ins, pre-configured) engine object, e.g.
        `RuamelEngine(sort_keys=True)` or a custom engine implementing the `YamlEngine` protocol.
    """
    global _default_engine
    if not isinstance(engine, YamlEngine):
        raise TypeError(
            f"Expected an object implementing YamlEngine (read/write methods), got {engine!r}"
        )
    _default_engine = engine
