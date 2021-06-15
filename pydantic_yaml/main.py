"""YAML-enabled Pydantic models."""

__all__ = ["__version__", "YamlEnum", "YamlModel"]

from ._inject_representers import _inject_all
from .enums import YamlEnum
from .models import YamlModel
from .version import __version__

_inject_all()
