"""YAML-enabled Pydantic models."""

__all__ = [
    # New API
    "__version__",
    "parse_yaml_file_as",
    "parse_yaml_raw_as",
    "to_yaml_file",
    "to_yaml_str",
    # Engines
    "YamlEngine",
    "RuamelEngine",
    "YamlRocksEngine",
    "get_default_engine",
    "set_default_engine",
]


from pydantic_yaml._internals.v2 import (
    parse_yaml_file_as,
    parse_yaml_raw_as,
    to_yaml_file,
    to_yaml_str,
)
from pydantic_yaml.engines import (
    RuamelEngine,
    YamlEngine,
    YamlRocksEngine,
    get_default_engine,
    set_default_engine,
)

from .version import __version__
