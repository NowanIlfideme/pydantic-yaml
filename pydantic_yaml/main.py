"""YAML-enabled Pydantic models."""

__all__ = [
    "__version__",
    "yaml",
    "yaml_safe_dump",
    "yaml_safe_load",
    "YamlEnum",
    "YamlInt",
    "YamlIntEnum",
    "YamlStr",
    "YamlStrEnum",
    "YamlModel",
    "YamlModelMixin",
    "YamlModelMixinConfig",
    "SemVer",
    "VersionedYamlModel",
]

from .compat.old_enums import YamlEnum
from .compat.hacks import inject_all as _inject_yaml_hacks
from .compat.types import YamlInt, YamlIntEnum, YamlStr, YamlStrEnum
from .compat.yaml_lib import yaml, yaml_safe_dump, yaml_safe_load
from .ext.semver import SemVer
from .ext.versioned_model import VersionedYamlModel
from .mixin import YamlModelMixin, YamlModelMixinConfig
from .model import YamlModel
from .version import __version__

_inject_yaml_hacks()
