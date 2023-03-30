"""Tests for YAML compatible types."""

import pytest

from pydantic_yaml.compat.types import YamlInt, YamlIntEnum, YamlStr, YamlStrEnum
from pydantic_yaml.compat.yaml_lib import yaml_safe_dump, yaml_safe_load


class XSE(YamlStrEnum):
    a = "a"
    b = "b"


class XIE(YamlIntEnum):
    a = 1
    b = 2


class XI(YamlInt):
    def __new__(cls, val):
        return super().__new__(cls, int(val))


class XS(YamlStr):
    def __new__(cls, val):
        return super().__new__(cls, f"My value is: {val!s}")


def test_str_enum():
    """Test for YamlStrEnum class."""
    x1 = XSE.a
    x2 = XSE("b")
    assert yaml_safe_load(yaml_safe_dump(x1)) == "a"
    assert yaml_safe_load(yaml_safe_dump(x2)) == "b"

    with pytest.raises(ValueError):
        XSE("c")


def test_int_enum():
    """Test for YamlIntEnum class."""
    x1 = XIE.a
    x2 = XIE(2)
    assert yaml_safe_load(yaml_safe_dump(x1)) == 1
    assert yaml_safe_load(yaml_safe_dump(x2)) == 2

    with pytest.raises(ValueError):
        XIE(3)


def test_int():
    """Test for YamlInt class."""
    x = XI("123")
    assert isinstance(x, XI)
    assert x == 123
    assert repr(x) == "XI(123)"


def test_str():
    """Test for YamlStr class."""
    x = XS("123")
    _exp = "My value is: 123"
    assert isinstance(x, XS)
    assert x == _exp
    assert repr(x) == "XS('My value is: 123')"
