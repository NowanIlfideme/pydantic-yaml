"""YAML-enabled Pydantic models."""

__all__ = [
    # New API
    "__version__",
    "parse_yaml_file_as",
    "parse_yaml_raw_as",
    "to_yaml_file",
    "to_yaml_str",
    # Engine selection
    "EngineName",
    "get_default_engine",
    "set_default_engine",
]


from pydantic_yaml._internals.v2 import (
    EngineName,
    get_default_engine,
    parse_yaml_file_as,
    parse_yaml_raw_as,
    set_default_engine,
    to_yaml_file,
    to_yaml_str,
)

from .version import __version__
