"""YAML-enabled Pydantic models."""

__all__ = [
    # New API
    "__version__",
    "parse_yaml_file_as",
    "parse_yaml_raw_as",
    "to_yaml_file",
    "to_yaml_str",
]


from pydantic_yaml._internals.v2 import (
    to_yaml_file,
    to_yaml_str,
    parse_yaml_file_as,
    parse_yaml_raw_as,
)

from .version import __version__
