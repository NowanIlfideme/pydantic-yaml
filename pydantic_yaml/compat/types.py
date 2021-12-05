"""Defines useful types for building your own YAML-compatible types."""

from enum import Enum
from inspect import isabstract
from typing import Dict

from .representers import register_int_like, register_str_like
from .yaml_lib import yaml

__all__ = ["YamlInt", "YamlIntEnum", "YamlStr", "YamlStrEnum"]


class YamlStr(str):
    """A `str` subclass that serializes to YAML as an integer."""

    def __init_subclass__(cls):
        """Adds a representer when defining a subclass."""
        res = super().__init_subclass__()
        if not isabstract(cls):
            register_str_like(cls, method=cls._to_yaml_str)
        return res

    @classmethod
    def _to_yaml_str(cls, v) -> str:
        """Represent a value of this type as a string."""
        return str(v)

    def __str__(self) -> str:
        """This just returns the wrapped string."""
        return super().__str__()

    def __repr__(self) -> str:
        """Repr string that keeps the class type. You may redefine this."""
        return type(self).__qualname__ + "(" + super().__repr__() + ")"


class YamlInt(int):
    """An `int` subclass that serializes to YAML as an integer."""

    def __init_subclass__(cls):
        """Adds a representer when defining a subclass."""
        res = super().__init_subclass__()
        if not isabstract(cls):
            register_int_like(cls, method=cls._to_yaml_int)
        return res

    @classmethod
    def _to_yaml_int(cls, v) -> int:
        """Represent a value of this type as an integer."""
        return int(v)

    def __int__(self) -> int:
        return super().__int__()

    def __str__(self) -> str:
        """This returns the int-wrapped string."""
        return super().__str__()

    def __repr__(self) -> str:
        """Repr string that keeps the class type. You may redefine this."""
        return type(self).__qualname__ + "(" + super().__repr__() + ")"


class YamlStrEnum(YamlStr, Enum):
    """String-valued enum that serializes to YAML directly as a string.

    This also checks that your enum can properly be serialized.
    """

    def __init_subclass__(cls):
        res = super().__init_subclass__()
        if not isabstract(cls):
            vals: Dict[str, cls] = dict(cls.__members__)
            yaml.dump(vals)
        return res


class YamlIntEnum(YamlInt, Enum):
    """Integer-valued enum that serializes to YAML directly as an integer.

    This also checks that your enum can properly be serialized.
    """

    def __init_subclass__(cls):
        res = super().__init_subclass__()
        if not isabstract(cls):
            vals: Dict[str, cls] = dict(cls.__members__)
            yaml.dump(vals)
        return res


if __name__ == "__main__":

    class A(YamlStrEnum):
        a = "a"
        b = "b"

    class X(YamlIntEnum):
        x1 = 1
        x2 = 2
