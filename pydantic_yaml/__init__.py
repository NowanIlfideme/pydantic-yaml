"""YAML-enabled Pydantic models."""
from pathlib import Path

__all__ = ["__version__", "YamlEnum", "YamlModel"]

_v = Path(__file__).parent / "VERSION"
with _v.open() as f:
    __version__ = f.read()


from . import aux_types  # noqa
from .enums import YamlEnum
from .models import YamlModel
