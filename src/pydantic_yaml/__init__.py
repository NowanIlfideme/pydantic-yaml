"""YAML-enabled Pydantic models."""

__all__ = [
    # New API
    "__version__",
    "parse_yaml_file_as",
    "parse_yaml_raw_as",
    "to_yaml_file",
    "to_yaml_str",
    # TODO: Re-add
    # YamlModelMixin ?
    # YamlModel ?
    # Deprecated classes
    "YamlInt",
    "YamlIntEnum",
    "YamlStr",
    "YamlStrEnum",
]


from pydantic_yaml._internals.v2 import parse_yaml_file_as, parse_yaml_raw_as, to_yaml_file, to_yaml_str

from .deprecated.types import YamlInt, YamlIntEnum, YamlStr, YamlStrEnum
from .version import __version__
