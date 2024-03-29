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


from pydantic.version import VERSION as PYDANTIC_VERSION

if (PYDANTIC_VERSION > "1") and (PYDANTIC_VERSION < "2"):
    from pydantic_yaml._internals.v1 import (
        to_yaml_file,
        to_yaml_str,
        parse_yaml_file_as,
        parse_yaml_raw_as,
    )
elif (PYDANTIC_VERSION > "2") and (PYDANTIC_VERSION < "3"):
    from pydantic_yaml._internals.v2 import (
        to_yaml_file,
        to_yaml_str,
        parse_yaml_file_as,
        parse_yaml_raw_as,
    )
else:
    raise ImportError(f"Unsupported version of Pydantic: {PYDANTIC_VERSION!r}")

from .deprecated.types import YamlInt, YamlIntEnum, YamlStr, YamlStrEnum
from .version import __version__
