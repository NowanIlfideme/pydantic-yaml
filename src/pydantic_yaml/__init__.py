"""YAML-enabled Pydantic models."""

__all__ = [
    # New API
    "__version__",
    "parse_yaml_file_as",
    "parse_yaml_raw_as",
    "to_yaml_file",
    "to_yaml_str",
    # Readers and writers
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


from pydantic_yaml._internals.v2 import (
    parse_yaml_file_as,
    parse_yaml_raw_as,
    to_yaml_file,
    to_yaml_str,
)
from pydantic_yaml.engines import (
    RuamelReader,
    RuamelWriter,
    YamlEngine,
    YamlReader,
    YamlRocksReader,
    YamlRocksWriter,
    YamlWriter,
    get_default_reader,
    get_default_writer,
    set_default_reader,
    set_default_writer,
)

from .version import __version__
