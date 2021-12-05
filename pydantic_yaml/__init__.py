"""YAML-enabled Pydantic models."""

__all__ = [
    "__version__",
    "yaml",
    "YamlInt",
    "YamlIntEnum",
    "YamlStr",
    "YamlStrEnum",
    "YamlModel",
    "YamlModelMixin",
    "YamlModelMixinConfig",
]

from .compat.hacks import inject_all as _inject_yaml_hacks
from .compat.types import YamlInt, YamlIntEnum, YamlStr, YamlStrEnum
from .compat.yaml_lib import yaml
from .mixin import YamlModelMixin, YamlModelMixinConfig
from .model import YamlModel
from .version import __version__

_inject_yaml_hacks()
