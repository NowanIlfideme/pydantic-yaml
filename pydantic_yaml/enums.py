from enum import Enum
from pydantic_yaml._yaml import yaml

__all__ = ["YamlEnum"]


def _repr_enum(dumper: yaml.Dumper, data: Enum):
    """Represent enums without additional hastles."""
    return dumper.represent_str(data.value)


class YamlEnum(Enum):
    """Enumeration that serializes as the proper underlying object type.

    You can use this instead of `enum.Enum`, for example:

        class MyEnum(str, YamlEnum):
            val1 = "Value 1"
            val2 = "Value 2"

    Note
    ----
    This is actually a lie, it only supports `str` enums for now. Oops.
    """

    def __init_subclass__(cls):
        yaml.add_representer(cls, _repr_enum)

    def __repr__(self) -> str:
        return repr(self.value)

    def __str__(self) -> str:
        return str(self.value)
