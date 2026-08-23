"""Pluggable YAML reader/writer interfaces and built-in implementations.

Reading and writing are separate concerns: parsing YAML is a simple, largely unconfigurable
operation, while writing has many independent formatting knobs (indentation, comments, flow
style, ...). Any object implementing `read(stream)` (matching `YamlReader`) can be passed as
`reader=` to `parse_yaml_raw_as`/`parse_yaml_file_as`; any object implementing
`write(stream, model)` (matching `YamlWriter`) can be passed as `writer=` to
`to_yaml_str`/`to_yaml_file`. No inheritance required for either.

`RuamelReader`/`RuamelWriter` and `YamlRocksReader`/`YamlRocksWriter` are the built-in
implementations; write your own to bring a different YAML library, or to serialize/parse by hand
(bypassing this project's default JSON round-trip approach) for full control.
"""

from __future__ import annotations

from io import IOBase
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel

from pydantic_yaml.engines._ruamel import RuamelReader, RuamelWriter
from pydantic_yaml.engines._yamlrocks import YamlRocksReader, YamlRocksWriter

__all__ = [
    "YamlReader",
    "YamlWriter",
    "YamlEngine",
    "RuamelReader",
    "RuamelWriter",
    "YamlRocksReader",
    "YamlRocksWriter",
    "get_default_reader",
    "set_default_reader",
    "get_default_writer",
    "set_default_writer",
]


@runtime_checkable
class YamlReader(Protocol):
    """Structural interface a YAML reader must satisfy to plug into pydantic-yaml.

    Any object with this one method works - no inheritance required.
    """

    def read(self, stream: IOBase) -> Any:
        """Read a YAML stream into plain Python objects, for TypeAdapter validation."""
        ...


@runtime_checkable
class YamlWriter(Protocol):
    """Structural interface a YAML writer must satisfy to plug into pydantic-yaml.

    Any object with this one method works - no inheritance required. Writers carry their own
    configuration (comment behavior, formatting, JSON-dump kwargs); `write` takes only the
    stream and the model.
    """

    def write(self, stream: IOBase, model: BaseModel) -> None:
        """Write `model` as YAML to `stream`, using this writer's own configuration."""
        ...


@runtime_checkable
class YamlEngine(YamlReader, YamlWriter, Protocol):
    """Convenience protocol for an object that's both a `YamlReader` and a `YamlWriter`.

    Not required anywhere in the public API - `reader=`/`writer=` each only ask for their one
    method - but handy if you'd rather write a single custom class that does both instead of a
    matched pair, or want a type covering "either half" of `RuamelReader`/`RuamelWriter` (or the
    `yamlrocks` equivalents) together.
    """


def _autodetect(verb: str, candidates: tuple[type[Any], ...]) -> Any:
    for cls in candidates:
        try:
            return cls()
        except ImportError:
            continue
    raise ImportError(
        f"pydantic-yaml requires at least one YAML backend to be installed to {verb} YAML. "
        "Install one with `pip install pydantic-yaml[yamlrocks]` or `pip install pydantic-yaml[ruamel]`."
    )


# Resolved lazily (on first use) rather than at import time, so `import pydantic_yaml` never
# fails just because autodetection hasn't happened yet.
_default_reader: YamlReader | None = None
_default_writer: YamlWriter | None = None


def get_default_reader() -> YamlReader:
    """Get the default YAML reader used when `reader=None` is passed to the public functions.

    Resolved once (and cached) on first use: whichever of `YamlRocksReader`/`RuamelReader` is
    installed (preferring `YamlRocksReader` if both are), constructed with default
    configuration. Raises `ImportError` if neither backend is installed. Override with
    `set_default_reader()`.
    """
    global _default_reader
    if _default_reader is None:
        _default_reader = _autodetect("read", (YamlRocksReader, RuamelReader))
    return _default_reader


def set_default_reader(reader: YamlReader) -> None:
    """Set the default YAML reader used when `reader=None` is passed to the public functions.

    Parameters
    ----------
    reader : YamlReader
        A pre-constructed reader object, e.g. `RuamelReader()` or a custom reader implementing
        the `YamlReader` protocol.
    """
    global _default_reader
    if not isinstance(reader, YamlReader):
        raise TypeError(f"Expected an object implementing YamlReader (a read method), got {reader!r}")
    _default_reader = reader


def get_default_writer() -> YamlWriter:
    """Get the default YAML writer used when `writer=None` is passed to the public functions.

    Resolved once (and cached) on first use: whichever of `YamlRocksWriter`/`RuamelWriter` is
    installed (preferring `YamlRocksWriter` if both are), constructed with default
    configuration. Raises `ImportError` if neither backend is installed. Override with
    `set_default_writer()`.
    """
    global _default_writer
    if _default_writer is None:
        _default_writer = _autodetect("write", (YamlRocksWriter, RuamelWriter))
    return _default_writer


def set_default_writer(writer: YamlWriter) -> None:
    """Set the default YAML writer used when `writer=None` is passed to the public functions.

    Parameters
    ----------
    writer : YamlWriter
        A pre-constructed (and, for the built-ins, pre-configured) writer object, e.g.
        `RuamelWriter(sort_keys=True)` or a custom writer implementing the `YamlWriter` protocol.
    """
    global _default_writer
    if not isinstance(writer, YamlWriter):
        raise TypeError(f"Expected an object implementing YamlWriter (a write method), got {writer!r}")
    _default_writer = writer
