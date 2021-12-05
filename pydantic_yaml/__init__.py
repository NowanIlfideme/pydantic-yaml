"""YAML-enabled Pydantic models."""

__all__ = [
    "__version__",
    "yaml",
    "YamlInt",
    "YamlIntEnum",
    "YamlStr",
    "YamlStrEnum",
]

from .compat.yaml_lib import yaml
from .compat.types import YamlInt, YamlIntEnum, YamlStr, YamlStrEnum
from .compat.hacks import inject_all as _inject_yaml_hacks
from .version import __version__

_inject_yaml_hacks()
