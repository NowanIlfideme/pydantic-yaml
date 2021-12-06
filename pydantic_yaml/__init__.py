"""YAML-enabled Pydantic models."""

from .version import __version__

try:
    __all__ = [
        "__version__",
        "SemVer",
        "yaml",
        "VersionedYamlModel",
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
        SemVer,
        VersionedYamlModel,
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
except Exception:
    pass
