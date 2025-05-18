"""YAML-enabled Pydantic models."""

__all__ = [
    "__version__",
    # v1 functional API
    "parse_yaml_file_as",
    "parse_yaml_raw_as",
    "to_yaml_file",
    "to_yaml_str",
    # v2 API - TBD
]


from pydantic_yaml._internals.pydantic_v2 import (
    to_yaml_file,
    to_yaml_str,
    parse_yaml_file_as,
    parse_yaml_raw_as,
)

from .version import __version__
