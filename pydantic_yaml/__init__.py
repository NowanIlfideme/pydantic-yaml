"""YAML-enabled Pydantic models."""

from .version import __version__


__all__ = [
    "__version__",
    "yaml",
    "YamlEnum",  # deprecated class
    "YamlInt",
    "YamlIntEnum",
    "YamlModel",
    "YamlModelMixin",
    "YamlModelMixinConfig",
    "YamlStr",
    "YamlStrEnum",
]
from .main import (
    YamlEnum,
    YamlInt,
    YamlIntEnum,
    YamlModel,
    YamlModelMixin,
    YamlModelMixinConfig,
    YamlStr,
    YamlStrEnum,
    yaml,
)
try:
    from .main import (    SemVer,
        VersionedYamlModel,
    )
    __all__.extend(["SemVer","VersionedYamlModel"])
except ImportError:
    pass
