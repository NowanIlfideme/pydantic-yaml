"""Deprecated types and enums."""

from enum import Enum

from typing_extensions import deprecated  # type: ignore

__all__ = [
    "YamlInt",
    "YamlIntEnum",
    "YamlStr",
    "YamlStrEnum",
]


@deprecated("Use `str` instead.")
class YamlStr(str):
    """YAML-compatible string."""


@deprecated("Use `int` instead.")
class YamlInt(int):
    """YAML-compatible int."""


@deprecated("Use `MyEnum(str, Enum)` instead.")
class YamlStrEnum(str, Enum):
    """String enumeration."""

    def __str__(self) -> str:
        """Return wrapped string."""
        return str.__str__(self)

    def __repr__(self) -> str:
        """Repr string that keeps the class type. You may redefine this."""
        return type(self).__qualname__ + "(" + str.__repr__(self) + ")"


@deprecated("Use `MyEnum(int, Enum)` instead.")
class YamlIntEnum(int, Enum):
    """Integer enumeration."""
