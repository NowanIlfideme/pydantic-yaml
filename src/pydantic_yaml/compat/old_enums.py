"""Old class for YamlEnum that is now deprecated (and marked as such)."""

from enum import Enum
from inspect import isabstract

from deprecated import deprecated

from .representers import register_str_like

__all__ = ["YamlEnum"]


@deprecated(version="0.5.0", reason="Use the `YamlStrEnum` class instead.")
class YamlEnum(Enum):
    """DEPRECATED, please use `pydantic_yaml.YamlStrEnum` instead.

    Enumeration that serializes as the proper underlying object type.

    You can use this instead of `enum.Enum`, for example:
        class MyEnum(str, YamlEnum):
            val1 = "Value 1"
            val2 = "Value 2"

    Note
    ----
    This is actually a lie, it only supports `str` enums for now. Oops.
    """

    def __init_subclass__(cls):
        """Subclass hook for old enumerations."""
        if not isabstract(cls):
            register_str_like(cls)

    def __repr__(self) -> str:
        """Return representation."""
        return repr(self.value)

    def __str__(self) -> str:
        """Return string value."""
        return str(self.value)
